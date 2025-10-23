"""
需求解析模块
使用LLM分析用户自然语言需求，提取项目类型、技术栈、功能需求
"""
import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ProjectType(Enum):
    """项目类型枚举"""
    WEB_APP = "web_app"
    API_SERVICE = "api_service"
    DESKTOP_APP = "desktop_app"
    MOBILE_APP = "mobile_app"
    DATA_ANALYSIS = "data_analysis"
    MACHINE_LEARNING = "machine_learning"
    MICROSERVICE = "microservice"
    CLI_TOOL = "cli_tool"
    LIBRARY = "library"
    GAME = "game"

class TechStack(Enum):
    """技术栈枚举"""
    # Python
    PYTHON_FASTAPI = "python_fastapi"
    PYTHON_FLASK = "python_flask"
    PYTHON_DJANGO = "python_django"
    PYTHON_STREAMLIT = "python_streamlit"
    
    # JavaScript/Node.js
    NODEJS_EXPRESS = "nodejs_express"
    NODEJS_NESTJS = "nodejs_nestjs"
    NODEJS_NEXTJS = "nodejs_nextjs"
    NODEJS_REACT = "nodejs_react"
    NODEJS_VUE = "nodejs_vue"
    
    # Java
    JAVA_SPRING = "java_spring"
    JAVA_SPRING_BOOT = "java_spring_boot"
    JAVA_QUARKUS = "java_quarkus"
    
    # Go
    GO_GIN = "go_gin"
    GO_ECHO = "go_echo"
    GO_FIBER = "go_fiber"
    
    # C#
    CSHARP_ASP_NET = "csharp_asp_net"
    CSHARP_BLAZOR = "csharp_blazor"
    
    # Rust
    RUST_ACTIX = "rust_actix"
    RUST_WARP = "rust_warp"
    
    # PHP
    PHP_LARAVEL = "php_laravel"
    PHP_SYMFONY = "php_symfony"

@dataclass
class ProjectRequirement:
    """项目需求数据结构"""
    project_name: str
    project_type: ProjectType
    tech_stack: TechStack
    description: str
    features: List[str]
    database_required: bool
    authentication_required: bool
    api_required: bool
    frontend_required: bool
    deployment_type: str
    complexity_level: str  # simple, medium, complex
    special_requirements: List[str]
    target_audience: str
    performance_requirements: List[str]

class RequirementParser:
    """需求解析器"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.tech_stack_keywords = {
            # Python
            "fastapi": TechStack.PYTHON_FASTAPI,
            "fast api": TechStack.PYTHON_FASTAPI,
            "flask": TechStack.PYTHON_FLASK,
            "django": TechStack.PYTHON_DJANGO,
            "streamlit": TechStack.PYTHON_STREAMLIT,
            "python": TechStack.PYTHON_FASTAPI,  # 默认FastAPI
            
            # JavaScript/Node.js
            "express": TechStack.NODEJS_EXPRESS,
            "nodejs": TechStack.NODEJS_EXPRESS,
            "node.js": TechStack.NODEJS_EXPRESS,
            "node": TechStack.NODEJS_EXPRESS,
            "nestjs": TechStack.NODEJS_NESTJS,
            "nextjs": TechStack.NODEJS_NEXTJS,
            "next.js": TechStack.NODEJS_NEXTJS,
            "react": TechStack.NODEJS_REACT,
            "vue": TechStack.NODEJS_VUE,
            "javascript": TechStack.NODEJS_EXPRESS,
            "js": TechStack.NODEJS_EXPRESS,
            
            # Java
            "spring": TechStack.JAVA_SPRING_BOOT,  # 默认Spring Boot
            "spring boot": TechStack.JAVA_SPRING_BOOT,
            "springboot": TechStack.JAVA_SPRING_BOOT,
            "quarkus": TechStack.JAVA_QUARKUS,
            "java": TechStack.JAVA_SPRING_BOOT,
            
            # Go
            "gin": TechStack.GO_GIN,
            "echo": TechStack.GO_ECHO,
            "fiber": TechStack.GO_FIBER,
            "golang": TechStack.GO_GIN,
            "go": TechStack.GO_GIN,
            
            # C#
            "asp.net": TechStack.CSHARP_ASP_NET,
            "blazor": TechStack.CSHARP_BLAZOR,
            "c#": TechStack.CSHARP_ASP_NET,
            "csharp": TechStack.CSHARP_ASP_NET,
            
            # Rust
            "actix": TechStack.RUST_ACTIX,
            "warp": TechStack.RUST_WARP,
            "rust": TechStack.RUST_ACTIX,
            
            # PHP
            "laravel": TechStack.PHP_LARAVEL,
            "symfony": TechStack.PHP_SYMFONY,
            "php": TechStack.PHP_LARAVEL,
        }
        
        self.project_type_keywords = {
            "web": ProjectType.WEB_APP,
            "website": ProjectType.WEB_APP,
            "web app": ProjectType.WEB_APP,
            "webapp": ProjectType.WEB_APP,
            "api": ProjectType.API_SERVICE,
            "service": ProjectType.API_SERVICE,
            "microservice": ProjectType.MICROSERVICE,
            "desktop": ProjectType.DESKTOP_APP,
            "mobile": ProjectType.MOBILE_APP,
            "app": ProjectType.WEB_APP,
            "data": ProjectType.DATA_ANALYSIS,
            "analysis": ProjectType.DATA_ANALYSIS,
            "ml": ProjectType.MACHINE_LEARNING,
            "machine learning": ProjectType.MACHINE_LEARNING,
            "ai": ProjectType.MACHINE_LEARNING,
            "cli": ProjectType.CLI_TOOL,
            "tool": ProjectType.CLI_TOOL,
            "library": ProjectType.LIBRARY,
            "game": ProjectType.GAME,
        }
    
    async def parse_requirement(self, user_input: str) -> ProjectRequirement:
        """解析用户需求"""
        print(f"🔍 解析用户需求: {user_input}")
        
        if self.llm_client and not getattr(self.llm_client, 'use_mock', True):
            return await self._parse_with_llm(user_input)
        else:
            return self._parse_with_keywords(user_input)
    
    async def _parse_with_llm(self, user_input: str) -> ProjectRequirement:
        """使用LLM解析需求"""
        try:
            # 构建解析提示
            prompt = f"""
请分析以下用户需求，并提取关键信息：

用户需求: {user_input}

请以JSON格式返回以下信息：
{{
    "project_name": "项目名称",
    "project_type": "项目类型(web_app/api_service/desktop_app/mobile_app/data_analysis/machine_learning/microservice/cli_tool/library/game)",
    "tech_stack": "技术栈(python_fastapi/python_flask/python_django/python_streamlit/nodejs_express/nodejs_nestjs/nodejs_nextjs/nodejs_react/nodejs_vue/java_spring/java_spring_boot/java_quarkus/go_gin/go_echo/go_fiber/csharp_asp_net/csharp_blazor/rust_actix/rust_warp/php_laravel/php_symfony)",
    "description": "项目描述",
    "features": ["功能1", "功能2", "功能3"],
    "database_required": true/false,
    "authentication_required": true/false,
    "api_required": true/false,
    "frontend_required": true/false,
    "deployment_type": "部署类型(cloud/local/docker)",
    "complexity_level": "复杂度(simple/medium/complex)",
    "special_requirements": ["特殊需求1", "特殊需求2"],
    "target_audience": "目标用户",
    "performance_requirements": ["性能需求1", "性能需求2"]
}}

请确保：
1. 项目名称简洁明了
2. 技术栈选择合理
3. 功能列表完整
4. 布尔值准确
5. 复杂度评估合理
"""
            
            # 调用LLM
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_client.create(messages)
            
            # 解析响应
            content = response["choices"][0]["message"]["content"]
            
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                return ProjectRequirement(
                    project_name=data.get("project_name", "ai-generated-project"),
                    project_type=ProjectType(data.get("project_type", "web_app")),
                    tech_stack=TechStack(data.get("tech_stack", "python_fastapi")),
                    description=data.get("description", "AI生成的项目"),
                    features=data.get("features", []),
                    database_required=data.get("database_required", False),
                    authentication_required=data.get("authentication_required", False),
                    api_required=data.get("api_required", True),
                    frontend_required=data.get("frontend_required", True),
                    deployment_type=data.get("deployment_type", "local"),
                    complexity_level=data.get("complexity_level", "simple"),
                    special_requirements=data.get("special_requirements", []),
                    target_audience=data.get("target_audience", "general"),
                    performance_requirements=data.get("performance_requirements", [])
                )
            else:
                print("⚠️ LLM响应格式不正确，使用关键词解析")
                return self._parse_with_keywords(user_input)
                
        except Exception as e:
            print(f"❌ LLM解析失败: {e}，使用关键词解析")
            return self._parse_with_keywords(user_input)
    
    def _parse_with_keywords(self, user_input: str) -> ProjectRequirement:
        """使用关键词解析需求"""
        user_input_lower = user_input.lower()
        
        # 检测技术栈
        tech_stack = TechStack.PYTHON_FASTAPI  # 默认
        for keyword, stack in self.tech_stack_keywords.items():
            if keyword in user_input_lower:
                tech_stack = stack
                break
        
        # 检测项目类型
        project_type = ProjectType.WEB_APP  # 默认
        for keyword, ptype in self.project_type_keywords.items():
            if keyword in user_input_lower:
                project_type = ptype
                break
        
        # 提取项目名称
        project_name = self._extract_project_name(user_input)
        
        # 检测功能需求
        features = self._extract_features(user_input_lower)
        
        # 检测特殊需求
        database_required = any(word in user_input_lower for word in ["数据库", "database", "db", "sql", "mysql", "postgresql"])
        authentication_required = any(word in user_input_lower for word in ["登录", "注册", "认证", "auth", "login", "register", "用户"])
        api_required = any(word in user_input_lower for word in ["api", "接口", "服务", "service"])
        frontend_required = any(word in user_input_lower for word in ["前端", "界面", "页面", "frontend", "ui", "web"])
        
        # 评估复杂度
        complexity_level = self._assess_complexity(user_input_lower, features)
        
        return ProjectRequirement(
            project_name=project_name,
            project_type=project_type,
            tech_stack=tech_stack,
            description=user_input,
            features=features,
            database_required=database_required,
            authentication_required=authentication_required,
            api_required=api_required,
            frontend_required=frontend_required,
            deployment_type="local",
            complexity_level=complexity_level,
            special_requirements=[],
            target_audience="general",
            performance_requirements=[]
        )
    
    def _extract_project_name(self, user_input: str) -> str:
        """提取项目名称"""
        # 简单的名称提取逻辑
        words = user_input.split()
        for i, word in enumerate(words):
            if word.lower() in ["创建", "开发", "生成", "make", "create", "develop", "build"]:
                if i + 1 < len(words):
                    # 提取下一个词作为项目名的一部分
                    name_parts = words[i+1:i+3]  # 取1-2个词
                    return "-".join(name_parts).lower().replace("的", "").replace("一个", "")
        
        # 如果没有找到关键词，使用默认名称
        return "ai-generated-project"
    
    def _extract_features(self, user_input_lower: str) -> List[str]:
        """提取功能需求"""
        features = []
        
        # 常见功能关键词
        feature_keywords = {
            "登录": "用户登录",
            "注册": "用户注册", 
            "认证": "身份认证",
            "管理": "数据管理",
            "搜索": "搜索功能",
            "上传": "文件上传",
            "下载": "文件下载",
            "统计": "数据统计",
            "分析": "数据分析",
            "报表": "报表生成",
            "通知": "消息通知",
            "支付": "支付功能",
            "购物车": "购物车",
            "订单": "订单管理",
            "评论": "评论系统",
            "点赞": "点赞功能",
            "分享": "分享功能",
            "聊天": "聊天功能",
            "实时": "实时通信",
            "地图": "地图功能",
            "定位": "位置定位"
        }
        
        for keyword, feature in feature_keywords.items():
            if keyword in user_input_lower:
                features.append(feature)
        
        return features if features else ["基础功能"]
    
    def _assess_complexity(self, user_input_lower: str, features: List[str]) -> str:
        """评估项目复杂度"""
        complexity_indicators = {
            "simple": ["简单", "基础", "basic", "simple"],
            "medium": ["中等", "标准", "standard", "medium"],
            "complex": ["复杂", "高级", "advanced", "complex", "企业级", "enterprise"]
        }
        
        # 检查复杂度关键词
        for level, keywords in complexity_indicators.items():
            if any(keyword in user_input_lower for keyword in keywords):
                return level
        
        # 根据功能数量评估
        if len(features) <= 2:
            return "simple"
        elif len(features) <= 5:
            return "medium"
        else:
            return "complex"
    
    def get_tech_stack_info(self, tech_stack: TechStack) -> Dict[str, Any]:
        """获取技术栈信息"""
        tech_info = {
            TechStack.PYTHON_FASTAPI: {
                "language": "Python",
                "framework": "FastAPI",
                "description": "现代、快速的Python Web框架",
                "dependencies": ["fastapi", "uvicorn", "pydantic"],
                "port": 8000,
                "entry_point": "main.py"
            },
            TechStack.PYTHON_FLASK: {
                "language": "Python", 
                "framework": "Flask",
                "description": "轻量级Python Web框架",
                "dependencies": ["flask", "gunicorn"],
                "port": 5000,
                "entry_point": "app.py"
            },
            TechStack.NODEJS_EXPRESS: {
                "language": "JavaScript",
                "framework": "Express.js",
                "description": "Node.js Web应用框架",
                "dependencies": ["express", "cors", "helmet"],
                "port": 3000,
                "entry_point": "app.js"
            },
            TechStack.JAVA_SPRING_BOOT: {
                "language": "Java",
                "framework": "Spring Boot",
                "description": "Java企业级应用框架",
                "dependencies": ["spring-boot-starter-web"],
                "port": 8080,
                "entry_point": "Application.java"
            },
            TechStack.GO_GIN: {
                "language": "Go",
                "framework": "Gin",
                "description": "Go语言Web框架",
                "dependencies": ["github.com/gin-gonic/gin"],
                "port": 8080,
                "entry_point": "main.go"
            }
        }
        
        return tech_info.get(tech_stack, tech_info[TechStack.PYTHON_FASTAPI])
