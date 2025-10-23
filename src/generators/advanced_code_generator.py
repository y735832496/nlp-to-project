"""
高级代码生成系统
支持复杂需求的多轮对话代码生成，包括Planner Agent和Coder Agent
"""
import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from legacy.requirement_parser import ProjectRequirement, TechStack, ProjectType
from src.models.models import CodeGenerationResponse, GeneratedFile, Dependencies

class AgentType(Enum):
    """Agent类型枚举"""
    PLANNER = "planner"
    CODER = "coder"
    REVIEWER = "reviewer"
    OPTIMIZER = "optimizer"
    ARCHITECT = "architect"

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ProjectStructure:
    """项目结构定义"""
    project_name: str
    tech_stack: Any  # 支持灵活的技术栈
    modules: List[str]
    files: List[str]
    directories: List[str]
    dependencies: List[str]
    entry_points: List[str]
    configuration_files: List[str]
    test_files: List[str]
    documentation_files: List[str]
    
    def __post_init__(self):
        """确保tech_stack是可哈希的"""
        if hasattr(self.tech_stack, 'name'):
            self.tech_stack_name = self.tech_stack.name
        elif hasattr(self.tech_stack, 'value'):
            self.tech_stack_name = self.tech_stack.value
        elif hasattr(self.tech_stack, 'language'):
            self.tech_stack_name = self.tech_stack.language
        else:
            self.tech_stack_name = str(self.tech_stack)

@dataclass
class CodeTask:
    """代码任务定义"""
    task_id: str
    agent_type: AgentType
    description: str
    input_data: Any
    expected_output: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error_message: Optional[str] = None
    dependencies: List[str] = None

@dataclass
class ConversationRound:
    """对话轮次"""
    round_id: int
    agent_type: AgentType
    input_prompt: str
    output_response: str
    timestamp: datetime
    success: bool = True
    error_message: Optional[str] = None

class PlannerAgent:
    """项目规划Agent"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.name = "项目规划专家"
    
    def _get_tech_stack_name(self, tech_stack) -> str:
        """获取技术栈名称，支持灵活的技术栈"""
        if hasattr(tech_stack, 'value'):
            return tech_stack.value
        elif hasattr(tech_stack, 'name'):
            return tech_stack.name
        elif hasattr(tech_stack, 'language'):
            return tech_stack.language
        else:
            return str(tech_stack)
        self.description = "负责分析需求并规划项目结构"
    
    async def plan_project_structure(self, requirements: ProjectRequirement) -> ProjectStructure:
        """规划项目结构"""
        print(f"🏗️ {self.name} 开始规划项目结构...")
        
        try:
            # 构建规划提示
            prompt = self._build_planning_prompt(requirements)
            
            # 调用LLM进行规划
            if self.llm_client and not getattr(self.llm_client, 'use_mock', True):
                messages = [{"role": "user", "content": prompt}]
                response = await self.llm_client.create(messages)
                planning_result = response["choices"][0]["message"]["content"]
            else:
                planning_result = self._mock_planning(requirements)
            
            # 解析规划结果
            project_structure = self._parse_planning_result(planning_result, requirements)
            
            print(f"✅ {self.name} 完成项目结构规划")
            return project_structure
            
        except Exception as e:
            print(f"❌ {self.name} 规划失败: {e}")
            return self._create_fallback_structure(requirements)
    
    def _build_planning_prompt(self, requirements: ProjectRequirement) -> str:
        """构建规划提示"""
        return f"""
作为项目规划专家，请为以下需求设计详细的项目结构：

项目信息：
- 项目名称: {requirements.project_name}
- 技术栈: {self._get_tech_stack_name(requirements.tech_stack)}
- 项目类型: {requirements.project_type.value}
- 功能需求: {', '.join(requirements.features)}
- 数据库需求: {'是' if requirements.database_required else '否'}
- 认证需求: {'是' if requirements.authentication_required else '否'}
- 复杂度: {requirements.complexity_level}

请以JSON格式返回项目结构规划：

{{
    "modules": ["模块1", "模块2", "模块3"],
    "files": ["文件1.py", "文件2.js", "文件3.java"],
    "directories": ["目录1/", "目录2/", "目录3/"],
    "dependencies": ["依赖1", "依赖2", "依赖3"],
    "entry_points": ["入口点1", "入口点2"],
    "configuration_files": ["配置文件1", "配置文件2"],
    "test_files": ["测试文件1", "测试文件2"],
    "documentation_files": ["文档1", "文档2"],
    "architecture_notes": "架构说明和设计思路"
}}

请确保：
1. 结构清晰，模块化设计
2. 包含必要的配置和测试文件
3. 考虑可扩展性和维护性
4. 符合技术栈最佳实践
"""
    
    def _mock_planning(self, requirements: ProjectRequirement) -> str:
        """模拟规划结果"""
        tech_stack = self._get_tech_stack_name(requirements.tech_stack)
        
        if tech_stack.startswith("python"):
            return json.dumps({
                "modules": ["main", "models", "services", "utils", "api"],
                "files": ["main.py", "models.py", "services.py", "utils.py", "api.py", "config.py"],
                "directories": ["src/", "tests/", "docs/", "config/"],
                "dependencies": ["fastapi", "uvicorn", "pydantic", "sqlalchemy"],
                "entry_points": ["main.py"],
                "configuration_files": ["requirements.txt", "config.yaml", ".env"],
                "test_files": ["test_main.py", "test_models.py", "test_api.py"],
                "documentation_files": ["README.md", "API.md", "DEPLOYMENT.md"],
                "architecture_notes": "采用分层架构，包含API层、服务层、数据层"
            })
        elif tech_stack.startswith("nodejs"):
            return json.dumps({
                "modules": ["app", "routes", "models", "middleware", "utils"],
                "files": ["app.js", "routes.js", "models.js", "middleware.js", "utils.js"],
                "directories": ["src/", "tests/", "docs/", "public/"],
                "dependencies": ["express", "cors", "helmet", "mongoose"],
                "entry_points": ["app.js"],
                "configuration_files": ["package.json", "config.js", ".env"],
                "test_files": ["app.test.js", "routes.test.js", "models.test.js"],
                "documentation_files": ["README.md", "API.md", "DEPLOYMENT.md"],
                "architecture_notes": "采用MVC架构，包含路由、模型、中间件"
            })
        elif tech_stack.startswith("java"):
            return json.dumps({
                "modules": ["main", "controller", "service", "model", "config"],
                "files": ["Application.java", "Controller.java", "Service.java", "Model.java", "Config.java"],
                "directories": ["src/", "test/", "docs/", "resources/"],
                "dependencies": ["spring-boot-starter-web", "spring-boot-starter-data-jpa"],
                "entry_points": ["Application.java"],
                "configuration_files": ["pom.xml", "application.yml", ".env"],
                "test_files": ["ApplicationTest.java", "ControllerTest.java"],
                "documentation_files": ["README.md", "API.md", "DEPLOYMENT.md"],
                "architecture_notes": "采用Spring Boot架构，包含控制器、服务、数据层"
            })
        elif tech_stack.startswith("go"):
            return json.dumps({
                "modules": ["main", "handler", "service", "model", "middleware"],
                "files": ["main.go", "handler.go", "service.go", "model.go", "middleware.go"],
                "directories": ["cmd/", "internal/", "pkg/", "test/"],
                "dependencies": ["github.com/gin-gonic/gin", "gorm.io/gorm"],
                "entry_points": ["main.go"],
                "configuration_files": ["go.mod", "go.sum", "config.yaml"],
                "test_files": ["main_test.go", "handler_test.go"],
                "documentation_files": ["README.md", "API.md", "DEPLOYMENT.md"],
                "architecture_notes": "采用Go微服务架构，包含处理器、服务、数据层"
            })
        else:
            # 默认Python
            return json.dumps({
                "modules": ["main", "models", "services", "utils", "api"],
                "files": ["main.py", "models.py", "services.py", "utils.py", "api.py", "config.py"],
                "directories": ["src/", "tests/", "docs/", "config/"],
                "dependencies": ["fastapi", "uvicorn", "pydantic", "sqlalchemy"],
                "entry_points": ["main.py"],
                "configuration_files": ["requirements.txt", "config.yaml", ".env"],
                "test_files": ["test_main.py", "test_models.py", "test_api.py"],
                "documentation_files": ["README.md", "API.md", "DEPLOYMENT.md"],
                "architecture_notes": "采用分层架构，包含API层、服务层、数据层"
            })
    
    def _parse_planning_result(self, planning_result: str, requirements: ProjectRequirement) -> ProjectStructure:
        """解析规划结果"""
        try:
            # 提取JSON部分
            import re
            json_match = re.search(r'\{.*\}', planning_result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                return ProjectStructure(
                    project_name=requirements.project_name,
                    tech_stack=requirements.tech_stack,
                    modules=data.get("modules", []),
                    files=data.get("files", []),
                    directories=data.get("directories", []),
                    dependencies=data.get("dependencies", []),
                    entry_points=data.get("entry_points", []),
                    configuration_files=data.get("configuration_files", []),
                    test_files=data.get("test_files", []),
                    documentation_files=data.get("documentation_files", [])
                )
            else:
                print("⚠️ 无法解析规划结果，使用默认结构")
                return self._create_fallback_structure(requirements)
                
        except Exception as e:
            print(f"⚠️ 解析规划结果失败: {e}，使用默认结构")
            return self._create_fallback_structure(requirements)
    
    def _create_fallback_structure(self, requirements: ProjectRequirement) -> ProjectStructure:
        """创建默认项目结构"""
        # 支持灵活的技术栈
        if hasattr(requirements.tech_stack, 'value'):
            tech_stack = self._get_tech_stack_name(requirements.tech_stack)
        else:
            tech_stack = requirements.tech_stack.language
        
        if tech_stack.startswith("java") or (hasattr(requirements.tech_stack, 'language') and requirements.tech_stack.language == "java"):
            return ProjectStructure(
                project_name=requirements.project_name,
                tech_stack=requirements.tech_stack,
                modules=["main", "controller", "service", "model", "config"],
                files=["Application.java", "UserController.java", "UserService.java", "User.java", "SecurityConfig.java"],
                directories=["src/main/java/", "src/main/resources/", "src/test/java/"],
                dependencies=["spring-boot-starter-web", "spring-boot-starter-data-jpa", "spring-boot-starter-security"],
                entry_points=["Application.java"],
                configuration_files=["pom.xml", "application.yml"],
                test_files=["ApplicationTest.java", "UserControllerTest.java"],
                documentation_files=["README.md"]
            )
        elif tech_stack.startswith("nodejs") or (hasattr(requirements.tech_stack, 'language') and requirements.tech_stack.language == "javascript"):
            return ProjectStructure(
                project_name=requirements.project_name,
                tech_stack=requirements.tech_stack,
                modules=["app", "routes", "models", "middleware", "utils"],
                files=["app.js", "routes.js", "models.js", "middleware.js", "utils.js"],
                directories=["src/", "tests/", "docs/", "public/"],
                dependencies=["express", "cors", "helmet", "mongoose"],
                entry_points=["app.js"],
                configuration_files=["package.json", "config.js", ".env"],
                test_files=["app.test.js", "routes.test.js"],
                documentation_files=["README.md"]
            )
        elif tech_stack.startswith("go") or (hasattr(requirements.tech_stack, 'language') and requirements.tech_stack.language == "go"):
            return ProjectStructure(
                project_name=requirements.project_name,
                tech_stack=requirements.tech_stack,
                modules=["main", "handler", "service", "model", "middleware"],
                files=["main.go", "handler.go", "service.go", "model.go", "middleware.go"],
                directories=["cmd/", "internal/", "pkg/", "test/"],
                dependencies=["github.com/gin-gonic/gin", "gorm.io/gorm"],
                entry_points=["main.go"],
                configuration_files=["go.mod", "go.sum", "config.yaml"],
                test_files=["main_test.go", "handler_test.go"],
                documentation_files=["README.md"]
            )
        else:  # Python默认
            return ProjectStructure(
                project_name=requirements.project_name,
                tech_stack=requirements.tech_stack,
                modules=["main", "models", "services", "utils", "api", "config"],
                files=["main.py", "models.py", "services.py", "utils.py", "api.py", "config.py"],
                directories=["src/", "src/models/", "src/services/", "src/utils/", "src/api/", "tests/", "docs/", "data/"],
                dependencies=["torch", "numpy", "pandas", "scikit-learn", "fastapi", "uvicorn"],
                entry_points=["main.py"],
                configuration_files=["requirements.txt", "config.yaml", ".env"],
                test_files=["test_main.py", "test_models.py", "test_api.py"],
                documentation_files=["README.md", "docs/"]
            )

class CoderAgent:
    """代码生成Agent"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.name = "代码生成专家"
        self.description = "负责根据项目结构生成具体代码"
        self.conversation_history = []
    
    def _get_tech_stack_name(self, tech_stack) -> str:
        """获取技术栈名称，支持灵活的技术栈"""
        if hasattr(tech_stack, 'value'):
            return tech_stack.value
        elif hasattr(tech_stack, 'name'):
            return tech_stack.name
        elif hasattr(tech_stack, 'language'):
            return tech_stack.language
        else:
            return str(tech_stack)
    
    def _get_file_directory(self, file_name: str, project_structure: ProjectStructure) -> str:
        """根据文件名和项目结构确定文件目录"""
        # 配置文件放在根目录
        if file_name in ["requirements.txt", "config.yaml", ".env", "README.md"]:
            return ""
        
        # 测试文件放在tests目录
        if file_name.startswith("test_"):
            return "tests/"
        
        # 根据文件类型确定目录
        if file_name == "main.py":
            return "src/"
        elif file_name == "models.py":
            return "src/models/"
        elif file_name == "services.py":
            return "src/services/"
        elif file_name == "utils.py":
            return "src/utils/"
        elif file_name == "api.py":
            return "src/api/"
        elif file_name == "config.py":
            return "src/"
        else:
            return "src/"
    
    async def generate_code_for_file(self, file_path: str, project_structure: ProjectStructure, 
                                   requirements: ProjectRequirement, context: Dict[str, Any] = None) -> GeneratedFile:
        """为特定文件生成代码"""
        # 确定文件的实际路径（包含目录结构）
        file_name = os.path.basename(file_path)
        directory = self._get_file_directory(file_name, project_structure)
        full_path = os.path.join(directory, file_name).replace("\\", "/")
        
        print(f"💻 {self.name} 生成文件: {full_path}")
        
        try:
            # 构建代码生成提示
            prompt = self._build_coding_prompt(full_path, project_structure, requirements, context)
            
            # 调用LLM生成代码
            if self.llm_client and not getattr(self.llm_client, 'use_mock', True):
                messages = [{"role": "user", "content": prompt}]
                response = await self.llm_client.create(messages)
                code_content = response["choices"][0]["message"]["content"]
            else:
                code_content = self._mock_code_generation(full_path, project_structure, requirements)
            
            # 清理和验证代码
            cleaned_code = self._clean_code_content(code_content)
            
            # 记录对话历史
            self.conversation_history.append(ConversationRound(
                round_id=len(self.conversation_history) + 1,
                agent_type=AgentType.CODER,
                input_prompt=prompt,
                output_response=cleaned_code,
                timestamp=datetime.now()
            ))
            
            print(f"✅ {self.name} 完成文件生成: {full_path}")
            
            return GeneratedFile(
                path=full_path,
                content=cleaned_code,
                is_executable=self._is_executable_file(full_path)
            )
            
        except Exception as e:
            print(f"❌ {self.name} 生成文件失败: {file_path} - {e}")
            return GeneratedFile(
                path=file_path,
                content=f"# 代码生成失败: {e}",
                is_executable=False
            )
    
    def _build_coding_prompt(self, file_path: str, project_structure: ProjectStructure, 
                           requirements: ProjectRequirement, context: Dict[str, Any] = None) -> str:
        """构建代码生成提示"""
        # 支持灵活的技术栈
        if hasattr(project_structure.tech_stack, 'value'):
            tech_stack = self._get_tech_stack_name(project_structure.tech_stack)
        else:
            tech_stack = project_structure.tech_stack.language
        
        # 根据文件类型构建不同的提示
        if file_path.endswith('.py'):
            return self._build_python_prompt(file_path, project_structure, requirements, context)
        elif file_path.endswith('.js'):
            return self._build_javascript_prompt(file_path, project_structure, requirements, context)
        elif file_path.endswith('.java'):
            return self._build_java_prompt(file_path, project_structure, requirements, context)
        else:
            return self._build_generic_prompt(file_path, project_structure, requirements, context)
    
    def _build_python_prompt(self, file_path: str, project_structure: ProjectStructure, 
                           requirements: ProjectRequirement, context: Dict[str, Any] = None) -> str:
        """构建Python代码生成提示"""
        return f"""
作为Python代码生成专家，请为以下文件生成完整、可运行的代码：

文件路径: {file_path}
项目名称: {project_structure.project_name}
技术栈: {self._get_tech_stack_name(project_structure.tech_stack)}

项目结构:
- 模块: {', '.join(project_structure.modules)}
- 文件: {', '.join(project_structure.files)}
- 依赖: {', '.join(project_structure.dependencies)}

功能需求:
- 功能: {', '.join(requirements.features)}
- 数据库: {'是' if requirements.database_required else '否'}
- 认证: {'是' if requirements.authentication_required else '否'}

请生成完整的Python代码，包括：
1. 必要的导入语句
2. 完整的类和方法定义
3. 错误处理
4. 文档字符串
5. 类型注解
6. 符合PEP8规范

只返回代码内容，不要包含任何解释文字。
"""
    
    def _build_javascript_prompt(self, file_path: str, project_structure: ProjectStructure, 
                               requirements: ProjectRequirement, context: Dict[str, Any] = None) -> str:
        """构建JavaScript代码生成提示"""
        return f"""
作为JavaScript代码生成专家，请为以下文件生成完整、可运行的代码：

文件路径: {file_path}
项目名称: {project_structure.project_name}
技术栈: {self._get_tech_stack_name(project_structure.tech_stack)}

项目结构:
- 模块: {', '.join(project_structure.modules)}
- 文件: {', '.join(project_structure.files)}
- 依赖: {', '.join(project_structure.dependencies)}

功能需求:
- 功能: {', '.join(requirements.features)}
- 数据库: {'是' if requirements.database_required else '否'}
- 认证: {'是' if requirements.authentication_required else '否'}

请生成完整的JavaScript代码，包括：
1. 必要的require/import语句
2. 完整的函数和类定义
3. 错误处理
4. JSDoc注释
5. 符合ES6+规范

只返回代码内容，不要包含任何解释文字。
"""
    
    def _build_java_prompt(self, file_path: str, project_structure: ProjectStructure, 
                          requirements: ProjectRequirement, context: Dict[str, Any] = None) -> str:
        """构建Java代码生成提示"""
        return f"""
作为Java代码生成专家，请为以下文件生成完整、可运行的代码：

文件路径: {file_path}
项目名称: {project_structure.project_name}
技术栈: {self._get_tech_stack_name(project_structure.tech_stack)}

项目结构:
- 模块: {', '.join(project_structure.modules)}
- 文件: {', '.join(project_structure.files)}
- 依赖: {', '.join(project_structure.dependencies)}

功能需求:
- 功能: {', '.join(requirements.features)}
- 数据库: {'是' if requirements.database_required else '否'}
- 认证: {'是' if requirements.authentication_required else '否'}

请生成完整的Java代码，包括：
1. 必要的import语句
2. 完整的类和方法定义
3. 异常处理
4. JavaDoc注释
5. 符合Java编码规范

只返回代码内容，不要包含任何解释文字。
"""
    
    def _build_generic_prompt(self, file_path: str, project_structure: ProjectStructure, 
                           requirements: ProjectRequirement, context: Dict[str, Any] = None) -> str:
        """构建通用代码生成提示"""
        return f"""
作为代码生成专家，请为以下文件生成完整、可运行的代码：

文件路径: {file_path}
项目名称: {project_structure.project_name}
技术栈: {self._get_tech_stack_name(project_structure.tech_stack)}

项目结构:
- 模块: {', '.join(project_structure.modules)}
- 文件: {', '.join(project_structure.files)}
- 依赖: {', '.join(project_structure.dependencies)}

功能需求:
- 功能: {', '.join(requirements.features)}
- 数据库: {'是' if requirements.database_required else '否'}
- 认证: {'是' if requirements.authentication_required else '否'}

请生成完整的代码，包括：
1. 必要的导入语句
2. 完整的函数和类定义
3. 错误处理
4. 文档注释
5. 符合最佳实践

只返回代码内容，不要包含任何解释文字。
"""
    
    def _mock_code_generation(self, file_path: str, project_structure: ProjectStructure, 
                            requirements: ProjectRequirement) -> str:
        """模拟代码生成"""
        tech_stack = self._get_tech_stack_name(project_structure.tech_stack)
        
        if tech_stack.startswith("java"):
            return self._generate_java_code(file_path, project_structure, requirements)
        elif tech_stack.startswith("nodejs"):
            return self._generate_javascript_code(file_path, project_structure, requirements)
        elif tech_stack.startswith("go"):
            return self._generate_go_code(file_path, project_structure, requirements)
        else:  # Python默认
            return self._generate_python_code(file_path, project_structure, requirements)
    
    def _generate_java_code(self, file_path: str, project_structure: ProjectStructure, requirements: ProjectRequirement) -> str:
        """生成Java代码"""
        if file_path == "Application.java":
            return f'''package com.example.{project_structure.project_name};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

@SpringBootApplication
@EnableJpaRepositories
public class Application {{
    public static void main(String[] args) {{
        SpringApplication.run(Application.class, args);
    }}
}}
'''
        elif file_path == "UserController.java":
            return f'''package com.example.{project_structure.project_name}.controller;

import com.example.{project_structure.project_name}.model.User;
import com.example.{project_structure.project_name}.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/users")
@CrossOrigin(origins = "*")
public class UserController {{
    
    @Autowired
    private UserService userService;
    
    @GetMapping
    public ResponseEntity<List<User>> getAllUsers() {{
        return ResponseEntity.ok(userService.getAllUsers());
    }}
    
    @PostMapping
    public ResponseEntity<User> createUser(@RequestBody User user) {{
        return ResponseEntity.ok(userService.createUser(user));
    }}
    
    @GetMapping("/{{id}}")
    public ResponseEntity<User> getUserById(@PathVariable Long id) {{
        return ResponseEntity.ok(userService.getUserById(id));
    }}
    
    @PutMapping("/{{id}}")
    public ResponseEntity<User> updateUser(@PathVariable Long id, @RequestBody User user) {{
        return ResponseEntity.ok(userService.updateUser(id, user));
    }}
    
    @DeleteMapping("/{{id}}")
    public ResponseEntity<String> deleteUser(@PathVariable Long id) {{
        userService.deleteUser(id);
        return ResponseEntity.ok("User deleted successfully");
    }}
}}
'''
        elif file_path == "User.java":
            return f'''package com.example.{project_structure.project_name}.model;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "users")
public class User {{
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false, unique = true)
    private String username;
    
    @Column(nullable = false)
    private String email;
    
    @Column(nullable = false)
    private String password;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
    
    // Constructors
    public User() {{}}
    
    public User(String username, String email, String password) {{
        this.username = username;
        this.email = email;
        this.password = password;
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }}
    
    // Getters and Setters
    public Long getId() {{ return id; }}
    public void setId(Long id) {{ this.id = id; }}
    
    public String getUsername() {{ return username; }}
    public void setUsername(String username) {{ this.username = username; }}
    
    public String getEmail() {{ return email; }}
    public void setEmail(String email) {{ this.email = email; }}
    
    public String getPassword() {{ return password; }}
    public void setPassword(String password) {{ this.password = password; }}
    
    public LocalDateTime getCreatedAt() {{ return createdAt; }}
    public void setCreatedAt(LocalDateTime createdAt) {{ this.createdAt = createdAt; }}
    
    public LocalDateTime getUpdatedAt() {{ return updatedAt; }}
    public void setUpdatedAt(LocalDateTime updatedAt) {{ this.updatedAt = updatedAt; }}
}}
'''
        else:
            return f'''// {project_structure.project_name} - {file_path}
package com.example.{project_structure.project_name};

public class {file_path.replace('.java', '')} {{
    // TODO: Implement {file_path}
}}
'''
    
    def _generate_javascript_code(self, file_path: str, project_structure: ProjectStructure, requirements: ProjectRequirement) -> str:
        """生成JavaScript代码"""
        if file_path == "app.js":
            return f'''const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const mongoose = require('mongoose');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());

// Routes
app.get('/', (req, res) => {{
    res.json({{ message: 'Welcome to {project_structure.project_name}', version: '1.0.0' }});
}});

app.get('/health', (req, res) => {{
    res.json({{ status: 'healthy' }});
}});

// Start server
app.listen(PORT, () => {{
    console.log(`Server running on port ${{PORT}}`);
}});
'''
        else:
            return f'''// {project_structure.project_name} - {file_path}
const express = require('express');

// TODO: Implement {file_path}
module.exports = {{}};
'''
    
    def _generate_go_code(self, file_path: str, project_structure: ProjectStructure, requirements: ProjectRequirement) -> str:
        """生成Go代码"""
        if file_path == "main.go":
            return f'''package main

import (
    "net/http"
    "github.com/gin-gonic/gin"
)

func main() {{
    r := gin.Default()
    
    r.GET("/", func(c *gin.Context) {{
        c.JSON(http.StatusOK, gin.H{{
            "message": "Welcome to {project_structure.project_name}",
            "version": "1.0.0",
        }})
    }})
    
    r.GET("/health", func(c *gin.Context) {{
        c.JSON(http.StatusOK, gin.H{{"status": "healthy"}})
    }})
    
    r.Run(":8080")
}}
'''
        else:
            return f'''package main

// TODO: Implement {file_path}
'''
    
    def _generate_python_code(self, file_path: str, project_structure: ProjectStructure, requirements: ProjectRequirement) -> str:
        """生成Python代码"""
        return f'''"""
{project_structure.project_name} - {file_path}
"""
import os
import sys
from typing import Dict, List, Any, Optional

class {project_structure.project_name}Service:
    """服务类"""
    
    def __init__(self):
        self.name = "{project_structure.project_name}"
    
    def process_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求"""
        return {{"status": "success", "data": data}}
    
    def get_info(self) -> Dict[str, str]:
        """获取信息"""
        return {{"name": self.name, "version": "1.0.0"}}

if __name__ == "__main__":
    service = {project_structure.project_name}Service()
    print(service.get_info())
'''
    
    def _clean_code_content(self, content: str) -> str:
        """清理代码内容"""
        # 移除代码块标记
        content = content.replace('```python', '').replace('```javascript', '').replace('```java', '').replace('```', '')
        
        # 移除可能的解释文字
        lines = content.split('\n')
        cleaned_lines = []
        in_code = False
        
        for line in lines:
            # 如果遇到明显的代码行，开始收集代码
            if any(keyword in line.lower() for keyword in ['import ', 'from ', 'def ', 'class ', 'function ', 'public ', 'private ']):
                in_code = True
            
            if in_code:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def _is_executable_file(self, file_path: str) -> bool:
        """判断是否为可执行文件"""
        executable_extensions = ['.py', '.js', '.sh', '.bat']
        return any(file_path.endswith(ext) for ext in executable_extensions)

class AdvancedCodeGenerator:
    """高级代码生成器"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.planner_agent = PlannerAgent(llm_client)
        self.coder_agent = CoderAgent(llm_client)
        self.conversation_history = []
    
    def _get_tech_stack_name(self, tech_stack) -> str:
        """获取技术栈名称，支持灵活的技术栈"""
        if hasattr(tech_stack, 'value'):
            return tech_stack.value
        elif hasattr(tech_stack, 'name'):
            return tech_stack.name
        elif hasattr(tech_stack, 'language'):
            return tech_stack.language
        else:
            return str(tech_stack)
    
    async def generate_complex_project(self, requirements: ProjectRequirement) -> CodeGenerationResponse:
        """生成复杂项目"""
        print("🚀 开始高级代码生成流程...")
        
        try:
            # 第一步：规划项目结构
            print("\n📋 步骤1: 项目结构规划")
            project_structure = await self.planner_agent.plan_project_structure(requirements)
            print(f"✅ 项目结构规划完成，包含 {len(project_structure.files)} 个文件")
            
            # 第二步：多轮对话生成代码
            print("\n💻 步骤2: 多轮对话代码生成")
            generated_files = []
            
            # 按优先级生成文件
            file_priority = self._get_file_priority(project_structure)
            
            for file_path in file_priority:
                print(f"🔄 生成文件: {file_path}")
                
                # 构建上下文
                context = {
                    "generated_files": [f.path for f in generated_files],
                    "project_structure": project_structure,
                    "conversation_history": self.conversation_history
                }
                
                # 生成文件代码
                file_content = await self.coder_agent.generate_code_for_file(
                    file_path, project_structure, requirements, context
                )
                
                generated_files.append(file_content)
                
                # 记录对话历史
                self.conversation_history.append(ConversationRound(
                    round_id=len(self.conversation_history) + 1,
                    agent_type=AgentType.CODER,
                    input_prompt=f"生成文件: {file_path}",
                    output_response=f"已生成: {file_path}",
                    timestamp=datetime.now()
                ))
            
            # 第三步：生成依赖信息
            dependencies = Dependencies(
                language_version=self._get_language_version(requirements.tech_stack),
                packages=project_structure.dependencies
            )
            
            # 第四步：生成构建和运行命令
            build_commands = self._get_build_commands(requirements.tech_stack)
            run_commands = self._get_run_commands(requirements.tech_stack)
            test_commands = self._get_test_commands(requirements.tech_stack)
            
            print(f"✅ 高级代码生成完成，生成了 {len(generated_files)} 个文件")
            
            return CodeGenerationResponse(
                files=generated_files,
                dependencies=dependencies,
                build_commands=build_commands,
                run_commands=run_commands,
                test_commands=test_commands
            )
            
        except Exception as e:
            print(f"❌ 高级代码生成失败: {e}")
            return CodeGenerationResponse(
                files=[],
                dependencies=Dependencies(language_version="3.8", packages=[]),
                build_commands=[],
                run_commands=[],
                test_commands=[]
            )
    
    def _get_file_priority(self, project_structure: ProjectStructure) -> List[str]:
        """获取文件生成优先级"""
        priority_order = []
        
        # 配置文件优先
        priority_order.extend(project_structure.configuration_files)
        
        # 核心文件
        priority_order.extend(project_structure.entry_points)
        
        # 其他文件
        for file_path in project_structure.files:
            if file_path not in priority_order:
                priority_order.append(file_path)
        
        # 测试文件最后
        priority_order.extend(project_structure.test_files)
        
        return priority_order
    
    def _get_language_version(self, tech_stack: TechStack) -> str:
        """获取语言版本"""
        if self._get_tech_stack_name(tech_stack).startswith("python"):
            return "3.8"
        elif self._get_tech_stack_name(tech_stack).startswith("nodejs"):
            return "16.0.0"
        elif self._get_tech_stack_name(tech_stack).startswith("java"):
            return "17"
        elif self._get_tech_stack_name(tech_stack).startswith("go"):
            return "1.21"
        else:
            return "latest"
    
    def _get_build_commands(self, tech_stack: TechStack) -> List[str]:
        """获取构建命令"""
        if self._get_tech_stack_name(tech_stack).startswith("python"):
            return ["pip install -r requirements.txt"]
        elif self._get_tech_stack_name(tech_stack).startswith("nodejs"):
            return ["npm install"]
        elif self._get_tech_stack_name(tech_stack).startswith("java"):
            return ["mvn clean compile"]
        elif self._get_tech_stack_name(tech_stack).startswith("go"):
            return ["go mod tidy", "go build"]
        else:
            return []
    
    def _get_run_commands(self, tech_stack: TechStack) -> List[str]:
        """获取运行命令"""
        if self._get_tech_stack_name(tech_stack).startswith("python"):
            return ["python main.py"]
        elif self._get_tech_stack_name(tech_stack).startswith("nodejs"):
            return ["npm start"]
        elif self._get_tech_stack_name(tech_stack).startswith("java"):
            return ["mvn spring-boot:run"]
        elif self._get_tech_stack_name(tech_stack).startswith("go"):
            return ["./main"]
        else:
            return []
    
    def _get_test_commands(self, tech_stack: TechStack) -> List[str]:
        """获取测试命令"""
        if self._get_tech_stack_name(tech_stack).startswith("python"):
            return ["pytest"]
        elif self._get_tech_stack_name(tech_stack).startswith("nodejs"):
            return ["npm test"]
        elif self._get_tech_stack_name(tech_stack).startswith("java"):
            return ["mvn test"]
        elif self._get_tech_stack_name(tech_stack).startswith("go"):
            return ["go test ./..."]
        else:
            return []
    
    def get_conversation_summary(self) -> str:
        """获取对话摘要"""
        summary = f"📊 对话摘要\n"
        summary += f"总轮次: {len(self.conversation_history)}\n"
        summary += f"成功轮次: {len([r for r in self.conversation_history if r.success])}\n"
        summary += f"失败轮次: {len([r for r in self.conversation_history if not r.success])}\n"
        
        if self.conversation_history:
            summary += f"最后对话: {self.conversation_history[-1].timestamp}\n"
        
        return summary
