"""
扩展性架构
支持新项目类型和技术的快速接入
"""
import os
import json
import importlib
from typing import Dict, List, Any, Optional, Type, Callable
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
from legacy.requirement_parser import TechStack, ProjectType, ProjectRequirement

class ExtensionType(Enum):
    """扩展类型枚举"""
    TECH_STACK = "tech_stack"
    PROJECT_TEMPLATE = "project_template"
    AGENT_ROLE = "agent_role"
    CODE_GENERATOR = "code_generator"
    QUALITY_CHECKER = "quality_checker"
    DEPLOYMENT_STRATEGY = "deployment_strategy"

@dataclass
class ExtensionMetadata:
    """扩展元数据"""
    name: str
    version: str
    description: str
    author: str
    extension_type: ExtensionType
    dependencies: List[str]
    config_schema: Dict[str, Any]

class ExtensionInterface(ABC):
    """扩展接口基类"""
    
    @abstractmethod
    def get_metadata(self) -> ExtensionMetadata:
        """获取扩展元数据"""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化扩展"""
        pass
    
    @abstractmethod
    def execute(self, input_data: Any) -> Any:
        """执行扩展功能"""
        pass

class TechStackExtension(ExtensionInterface):
    """技术栈扩展接口"""
    
    @abstractmethod
    def get_tech_stack_info(self) -> Dict[str, Any]:
        """获取技术栈信息"""
        pass
    
    @abstractmethod
    def generate_project_structure(self, requirements: ProjectRequirement) -> List[str]:
        """生成项目结构"""
        pass
    
    @abstractmethod
    def generate_dependencies(self, requirements: ProjectRequirement) -> Dict[str, Any]:
        """生成依赖配置"""
        pass

class AgentRoleExtension(ExtensionInterface):
    """Agent角色扩展接口"""
    
    @abstractmethod
    def get_agent_config(self) -> Dict[str, Any]:
        """获取Agent配置"""
        pass
    
    @abstractmethod
    def get_system_message(self) -> str:
        """获取系统消息"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """获取能力列表"""
        pass

class ExtensionRegistry:
    """扩展注册表"""
    
    def __init__(self):
        self.extensions = {}
        self.extension_paths = []
        self._load_builtin_extensions()
    
    def _load_builtin_extensions(self):
        """加载内置扩展"""
        # 注册内置技术栈扩展
        self._register_builtin_tech_stacks()
        
        # 注册内置Agent角色扩展
        self._register_builtin_agent_roles()
    
    def _register_builtin_tech_stacks(self):
        """注册内置技术栈"""
        # Python FastAPI
        self.register_extension(
            "python_fastapi",
            PythonFastAPIExtension(),
            ExtensionType.TECH_STACK
        )
        
        # Node.js Express
        self.register_extension(
            "nodejs_express",
            NodeJSExpressExtension(),
            ExtensionType.TECH_STACK
        )
        
        # Java Spring Boot
        self.register_extension(
            "java_spring_boot",
            JavaSpringBootExtension(),
            ExtensionType.TECH_STACK
        )
        
        # Go Gin
        self.register_extension(
            "go_gin",
            GoGinExtension(),
            ExtensionType.TECH_STACK
        )
    
    def _register_builtin_agent_roles(self):
        """注册内置Agent角色"""
        # 需求分析专家
        self.register_extension(
            "requirement_analyzer",
            RequirementAnalyzerExtension(),
            ExtensionType.AGENT_ROLE
        )
        
        # 代码生成专家
        self.register_extension(
            "code_generator",
            CodeGeneratorExtension(),
            ExtensionType.AGENT_ROLE
        )
        
        # 测试专家
        self.register_extension(
            "test_specialist",
            TestSpecialistExtension(),
            ExtensionType.AGENT_ROLE
        )
    
    def register_extension(self, name: str, extension: ExtensionInterface, extension_type: ExtensionType):
        """注册扩展"""
        if extension_type not in self.extensions:
            self.extensions[extension_type] = {}
        
        self.extensions[extension_type][name] = extension
        print(f"✅ 注册扩展: {name} ({extension_type.value})")
    
    def get_extension(self, name: str, extension_type: ExtensionType) -> Optional[ExtensionInterface]:
        """获取扩展"""
        if extension_type in self.extensions and name in self.extensions[extension_type]:
            return self.extensions[extension_type][name]
        return None
    
    def list_extensions(self, extension_type: ExtensionType) -> List[str]:
        """列出扩展"""
        if extension_type in self.extensions:
            return list(self.extensions[extension_type].keys())
        return []
    
    def load_external_extension(self, path: str) -> bool:
        """加载外部扩展"""
        try:
            # 动态导入扩展模块
            spec = importlib.util.spec_from_file_location("extension", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 获取扩展实例
            if hasattr(module, 'get_extension'):
                extension = module.get_extension()
                metadata = extension.get_metadata()
                
                # 注册扩展
                self.register_extension(
                    metadata.name,
                    extension,
                    metadata.extension_type
                )
                
                return True
            else:
                print(f"❌ 扩展文件缺少get_extension函数: {path}")
                return False
                
        except Exception as e:
            print(f"❌ 加载扩展失败: {path} - {e}")
            return False
    
    # def create_extension_template(self, extension_type: ExtensionType, name: str, output_path: str) -> bool:
    #     """创建扩展模板"""
    #     try:
    #         template_content = self._get_extension_template(extension_type, name)
    #
    #         with open(output_path, 'w', encoding='utf-8') as f:
    #             f.write(template_content)
    #
    #         print(f"✅ 创建扩展模板: {output_path}")
    #         return True
    #
    #     except Exception as e:
    #         print(f"❌ 创建扩展模板失败: {e}")
    #         return False
    
#     def _get_extension_template(self, extension_type: ExtensionType, name: str) -> str:
#         """获取扩展模板"""
#         if extension_type == ExtensionType.TECH_STACK:
#             return f'''"""
# {name} 技术栈扩展
# """
# from extensibility import TechStackExtension, ExtensionMetadata, ExtensionType
#
# class {name}Extension(TechStackExtension):
#     """{name}技术栈扩展"""
#
#     def get_metadata(self):
#         return ExtensionMetadata(
#             name="{name}",
#             version="1.0.0",
#             description="{name}技术栈扩展",
#             author="AI Agent",
#             extension_type=ExtensionType.TECH_STACK,
#             dependencies=[],
#             config_schema={{}}
#         )
#
#     def initialize(self, config):
#         return True
#
#     def execute(self, input_data):
#         return self.generate_project_structure(input_data)
#
#     def get_tech_stack_info(self):
#         return {{
#             "language": "Python",
#             "framework": "{name}",
#             "description": "{name}技术栈",
#             "dependencies": [],
#             "port": 8000,
#             "entry_point": "main.py"
#         }}
#
#     def generate_project_structure(self, requirements):
#         return [
#             "main.py",
#             "requirements.txt",
#             "README.md"
#         ]
#
#     def generate_dependencies(self, requirements):
#         return {{
#             "python": ">=3.8",
#             "packages": ["{name.lower()}"]
#         }}
#
# def get_extension():
#     return {name}Extension()
# '''
#
#         elif extension_type == ExtensionType.AGENT_ROLE:
#             return f'''"""
# {name} Agent角色扩展
# """
# from extensibility import AgentRoleExtension, ExtensionMetadata, ExtensionType
#
# class {name}Extension(AgentRoleExtension):
#     """{name}Agent角色扩展"""
#
#     def get_metadata(self):
#         return ExtensionMetadata(
#             name="{name}",
#             version="1.0.0",
#             description="{name}Agent角色扩展",
#             author="AI Agent",
#             extension_type=ExtensionType.AGENT_ROLE,
#             dependencies=[],
#             config_schema={{}}
#         )
#
#     def initialize(self, config):
#         return True
#
#     def execute(self, input_data):
#         return f"[{name}] 处理: {{input_data}}"
#
#     def get_agent_config(self):
#         return {{
#             "name": "{name}",
#             "description": "{name}专家",
#             "capabilities": ["专业能力1", "专业能力2"]
#         }}
#
#     def get_system_message(self):
#         return f"你是{name}专家。请根据你的专业领域提供建议。"
#
#     def get_capabilities(self):
#         return ["专业能力1", "专业能力2"]
#
# def get_extension():
#     return {name}Extension()
# '''
#
#         else:
#             return f'''"""
# {name} 扩展
# """
# from extensibility import ExtensionInterface, ExtensionMetadata, ExtensionType
#
# class {name}Extension(ExtensionInterface):
#     """{name}扩展"""
#
#     def get_metadata(self):
#         return ExtensionMetadata(
#             name="{name}",
#             version="1.0.0",
#             description="{name}扩展",
#             author="AI Agent",
#             extension_type=ExtensionType.{extension_type.name},
#             dependencies=[],
#             config_schema={{}}
#         )
#
#     def initialize(self, config):
#         return True
#
#     def execute(self, input_data):
#         return f"[{name}] 处理: {{input_data}}"
#
# def get_extension():
#     return {name}Extension()
# '''

# 内置扩展实现
class PythonFastAPIExtension(TechStackExtension):
    """Python FastAPI扩展"""
    
    def get_metadata(self):
        return ExtensionMetadata(
            name="python_fastapi",
            version="1.0.0",
            description="Python FastAPI技术栈扩展",
            author="AI Agent",
            extension_type=ExtensionType.TECH_STACK,
            dependencies=[],
            config_schema={}
        )
    
    def initialize(self, config):
        return True
    
    def execute(self, input_data):
        return self.generate_project_structure(input_data)
    
    def get_tech_stack_info(self):
        return {
            "language": "Python",
            "framework": "FastAPI",
            "description": "现代、快速的Python Web框架",
            "dependencies": ["fastapi", "uvicorn", "pydantic"],
            "port": 8000,
            "entry_point": "main.py"
        }
    
    def generate_project_structure(self, requirements):
        return [
            "main.py",
            "requirements.txt",
            "README.md",
            "tests/",
            "tests/test_main.py"
        ]
    
    def generate_dependencies(self, requirements):
        deps = {
            "python": ">=3.8",
            "packages": ["fastapi", "uvicorn", "pydantic"]
        }
        
        if requirements.database_required:
            deps["packages"].extend(["sqlalchemy", "alembic"])
        
        if requirements.authentication_required:
            deps["packages"].extend(["python-jose", "passlib"])
        
        return deps

class NodeJSExpressExtension(TechStackExtension):
    """Node.js Express扩展"""
    
    def get_metadata(self):
        return ExtensionMetadata(
            name="nodejs_express",
            version="1.0.0",
            description="Node.js Express技术栈扩展",
            author="AI Agent",
            extension_type=ExtensionType.TECH_STACK,
            dependencies=[],
            config_schema={}
        )
    
    def initialize(self, config):
        return True
    
    def execute(self, input_data):
        return self.generate_project_structure(input_data)
    
    def get_tech_stack_info(self):
        return {
            "language": "JavaScript",
            "framework": "Express.js",
            "description": "Node.js Web应用框架",
            "dependencies": ["express", "cors", "helmet"],
            "port": 3000,
            "entry_point": "app.js"
        }
    
    def generate_project_structure(self, requirements):
        return [
            "app.js",
            "package.json",
            "README.md",
            "tests/",
            "tests/app.test.js"
        ]
    
    def generate_dependencies(self, requirements):
        deps = {
            "node": ">=16.0.0",
            "packages": ["express", "cors", "helmet"]
        }
        
        if requirements.database_required:
            deps["packages"].append("mongoose")
        
        if requirements.authentication_required:
            deps["packages"].extend(["jsonwebtoken", "bcryptjs"])
        
        return deps

class JavaSpringBootExtension(TechStackExtension):
    """Java Spring Boot扩展"""
    
    def get_metadata(self):
        return ExtensionMetadata(
            name="java_spring_boot",
            version="1.0.0",
            description="Java Spring Boot技术栈扩展",
            author="AI Agent",
            extension_type=ExtensionType.TECH_STACK,
            dependencies=[],
            config_schema={}
        )
    
    def initialize(self, config):
        return True
    
    def execute(self, input_data):
        return self.generate_project_structure(input_data)
    
    def get_tech_stack_info(self):
        return {
            "language": "Java",
            "framework": "Spring Boot",
            "description": "Java企业级应用框架",
            "dependencies": ["spring-boot-starter-web"],
            "port": 8080,
            "entry_point": "Application.java"
        }
    
    def generate_project_structure(self, requirements):
        return [
            "pom.xml",
            "src/main/java/",
            "src/main/resources/",
            "src/test/java/",
            "README.md"
        ]
    
    def generate_dependencies(self, requirements):
        deps = {
            "java": ">=17",
            "maven": ">=3.6",
            "packages": ["spring-boot-starter-web"]
        }
        
        if requirements.database_required:
            deps["packages"].extend(["spring-boot-starter-data-jpa", "h2"])
        
        if requirements.authentication_required:
            deps["packages"].extend(["spring-boot-starter-security", "jwt"])
        
        return deps

class GoGinExtension(TechStackExtension):
    """Go Gin扩展"""
    
    def get_metadata(self):
        return ExtensionMetadata(
            name="go_gin",
            version="1.0.0",
            description="Go Gin技术栈扩展",
            author="AI Agent",
            extension_type=ExtensionType.TECH_STACK,
            dependencies=[],
            config_schema={}
        )
    
    def initialize(self, config):
        return True
    
    def execute(self, input_data):
        return self.generate_project_structure(input_data)
    
    def get_tech_stack_info(self):
        return {
            "language": "Go",
            "framework": "Gin",
            "description": "Go语言Web框架",
            "dependencies": ["github.com/gin-gonic/gin"],
            "port": 8080,
            "entry_point": "main.go"
        }
    
    def generate_project_structure(self, requirements):
        return [
            "main.go",
            "go.mod",
            "go.sum",
            "README.md",
            "tests/",
            "tests/main_test.go"
        ]
    
    def generate_dependencies(self, requirements):
        deps = {
            "go": ">=1.21",
            "packages": ["github.com/gin-gonic/gin"]
        }
        
        if requirements.database_required:
            deps["packages"].extend(["gorm.io/gorm", "gorm.io/driver/postgres"])
        
        if requirements.authentication_required:
            deps["packages"].extend(["github.com/golang-jwt/jwt/v5", "golang.org/x/crypto/bcrypt"])
        
        return deps

# Agent角色扩展
class RequirementAnalyzerExtension(AgentRoleExtension):
    """需求分析专家扩展"""
    
    def get_metadata(self):
        return ExtensionMetadata(
            name="requirement_analyzer",
            version="1.0.0",
            description="需求分析专家Agent扩展",
            author="AI Agent",
            extension_type=ExtensionType.AGENT_ROLE,
            dependencies=[],
            config_schema={}
        )
    
    def initialize(self, config):
        return True
    
    def execute(self, input_data):
        return f"[需求分析专家] 分析需求: {input_data}"
    
    def get_agent_config(self):
        return {
            "name": "需求分析专家",
            "description": "分析用户需求，提取关键信息",
            "capabilities": ["需求分析", "技术选型", "风险评估"]
        }
    
    def get_system_message(self):
        return """你是需求分析专家。你的任务是：
1. 分析用户的自然语言需求
2. 提取项目类型、技术栈、功能需求
3. 识别潜在的技术挑战
4. 提供需求优化建议

请以结构化的方式输出分析结果。"""
    
    def get_capabilities(self):
        return ["需求分析", "技术选型", "风险评估"]

class CodeGeneratorExtension(AgentRoleExtension):
    """代码生成专家扩展"""
    
    def get_metadata(self):
        return ExtensionMetadata(
            name="code_generator",
            version="1.0.0",
            description="代码生成专家Agent扩展",
            author="AI Agent",
            extension_type=ExtensionType.AGENT_ROLE,
            dependencies=[],
            config_schema={}
        )
    
    def initialize(self, config):
        return True
    
    def execute(self, input_data):
        return f"[代码生成专家] 生成代码: {input_data}"
    
    def get_agent_config(self):
        return {
            "name": "代码生成专家",
            "description": "根据需求生成高质量代码",
            "capabilities": ["代码生成", "最佳实践", "错误处理"]
        }
    
    def get_system_message(self):
        return """你是代码生成专家。你的任务是：
1. 根据需求和技术栈生成完整代码
2. 遵循最佳实践和编码规范
3. 确保代码可读性和可维护性
4. 包含适当的错误处理

请生成完整、可运行的代码。"""
    
    def get_capabilities(self):
        return ["代码生成", "最佳实践", "错误处理"]

class TestSpecialistExtension(AgentRoleExtension):
    """测试专家扩展"""
    
    def get_metadata(self):
        return ExtensionMetadata(
            name="test_specialist",
            version="1.0.0",
            description="测试专家Agent扩展",
            author="AI Agent",
            extension_type=ExtensionType.AGENT_ROLE,
            dependencies=[],
            config_schema={}
        )
    
    def initialize(self, config):
        return True
    
    def execute(self, input_data):
        return f"[测试专家] 生成测试: {input_data}"
    
    def get_agent_config(self):
        return {
            "name": "测试专家",
            "description": "生成测试用例和测试策略",
            "capabilities": ["测试设计", "测试自动化", "质量保证"]
        }
    
    def get_system_message(self):
        return """你是测试专家。你的任务是：
1. 生成全面的测试用例
2. 设计测试策略和测试计划
3. 确保测试覆盖率
4. 提供自动化测试方案

请生成完整的测试套件。"""
    
    def get_capabilities(self):
        return ["测试设计", "测试自动化", "质量保证"]

class ExtensionManager:
    """扩展管理器"""
    
    def __init__(self):
        self.registry = ExtensionRegistry()
        self.active_extensions = {}
    
    def load_extension(self, name: str, extension_type: ExtensionType, config: Dict[str, Any] = None) -> bool:
        """加载扩展"""
        extension = self.registry.get_extension(name, extension_type)
        if not extension:
            print(f"❌ 扩展不存在: {name}")
            return False
        
        try:
            if extension.initialize(config or {}):
                self.active_extensions[f"{extension_type.value}_{name}"] = extension
                print(f"✅ 扩展加载成功: {name}")
                return True
            else:
                print(f"❌ 扩展初始化失败: {name}")
                return False
        except Exception as e:
            print(f"❌ 扩展加载异常: {name} - {e}")
            return False
    
    def execute_extension(self, name: str, extension_type: ExtensionType, input_data: Any) -> Any:
        """执行扩展"""
        extension_key = f"{extension_type.value}_{name}"
        if extension_key not in self.active_extensions:
            print(f"❌ 扩展未加载: {name}")
            return None
        
        try:
            extension = self.active_extensions[extension_key]
            return extension.execute(input_data)
        except Exception as e:
            print(f"❌ 扩展执行失败: {name} - {e}")
            return None
    
    def list_active_extensions(self) -> List[str]:
        """列出活跃扩展"""
        return list(self.active_extensions.keys())
    
    def unload_extension(self, name: str, extension_type: ExtensionType) -> bool:
        """卸载扩展"""
        extension_key = f"{extension_type.value}_{name}"
        if extension_key in self.active_extensions:
            del self.active_extensions[extension_key]
            print(f"✅ 扩展卸载成功: {name}")
            return True
        else:
            print(f"❌ 扩展未加载: {name}")
            return False
    
    # def create_extension_template(self, extension_type: ExtensionType, name: str, output_path: str) -> bool:
    #     """创建扩展模板"""
    #     return self.registry.create_extension_template(extension_type, name, output_path)
