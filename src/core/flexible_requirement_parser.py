"""
灵活的需求解析系统
支持动态技术栈和AI自主决策
"""
import json
import re
from typing import Dict, List, Any, Optional, Union
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
    RESEARCH = "research"
    DEMO = "demo"

@dataclass
class FlexibleTechStack:
    """灵活的技术栈定义"""
    name: str
    language: str
    frameworks: List[str]
    libraries: List[str]
    tools: List[str]
    description: str
    category: str  # web, ml, data, mobile, etc.
    
    def __hash__(self):
        """使FlexibleTechStack可哈希"""
        return hash((self.name, self.language, tuple(self.frameworks), tuple(self.libraries), tuple(self.tools)))
    
    def __eq__(self, other):
        """使FlexibleTechStack可比较"""
        if not isinstance(other, FlexibleTechStack):
            return False
        return (self.name == other.name and 
                self.language == other.language and
                self.frameworks == other.frameworks and
                self.libraries == other.libraries and
                self.tools == other.tools)

@dataclass
class ProjectRequirement:
    """项目需求数据结构"""
    project_name: str
    project_type: ProjectType
    tech_stack: FlexibleTechStack  # 使用灵活的技术栈
    description: str
    features: List[str]
    database_required: bool
    authentication_required: bool
    api_required: bool
    frontend_required: bool
    deployment_type: str
    complexity_level: str
    special_requirements: List[str]
    target_audience: str
    performance_requirements: List[str]
    custom_requirements: Dict[str, Any]  # 自定义需求

class FlexibleRequirementParser:
    """灵活的需求解析器"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
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
            "model": ProjectType.MACHINE_LEARNING,
            "training": ProjectType.MACHINE_LEARNING,
            "demo": ProjectType.DEMO,
            "research": ProjectType.RESEARCH,
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
    "project_type": "项目类型(web_app/api_service/desktop_app/mobile_app/data_analysis/machine_learning/microservice/cli_tool/library/game/research/demo)",
    "tech_stack": {{
        "name": "技术栈名称",
        "language": "主要编程语言",
        "frameworks": ["框架1", "框架2"],
        "libraries": ["库1", "库2"],
        "tools": ["工具1", "工具2"],
        "description": "技术栈描述",
        "category": "技术栈类别"
    }},
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
    "performance_requirements": ["性能需求1", "性能需求2"],
    "custom_requirements": {{"自定义需求": "值"}}
}}

请确保：
1. 项目名称简洁明了
2. 技术栈可以自由组合，不受限制
3. 功能列表完整
4. 布尔值准确
5. 复杂度评估合理
6. 支持任何技术栈组合，包括新的、实验性的技术
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
                
                # 解析技术栈
                tech_stack_data = data.get("tech_stack", {})
                tech_stack = FlexibleTechStack(
                    name=tech_stack_data.get("name", "custom_tech_stack"),
                    language=tech_stack_data.get("language", "python"),
                    frameworks=tech_stack_data.get("frameworks", []),
                    libraries=tech_stack_data.get("libraries", []),
                    tools=tech_stack_data.get("tools", []),
                    description=tech_stack_data.get("description", "自定义技术栈"),
                    category=tech_stack_data.get("category", "custom")
                )
                
                return ProjectRequirement(
                    project_name=data.get("project_name", "ai-generated-project"),
                    project_type=ProjectType(data.get("project_type", "demo")),
                    tech_stack=tech_stack,
                    description=data.get("description", "AI生成的项目"),
                    features=data.get("features", []),
                    database_required=data.get("database_required", False),
                    authentication_required=data.get("authentication_required", False),
                    api_required=data.get("api_required", True),
                    frontend_required=data.get("frontend_required", False),
                    deployment_type=data.get("deployment_type", "local"),
                    complexity_level=data.get("complexity_level", "simple"),
                    special_requirements=data.get("special_requirements", []),
                    target_audience=data.get("target_audience", "developers"),
                    performance_requirements=data.get("performance_requirements", []),
                    custom_requirements=data.get("custom_requirements", {})
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
        
        # 检测项目类型
        project_type = ProjectType.DEMO  # 默认
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
        
        # 创建灵活的技术栈
        tech_stack = self._create_flexible_tech_stack(user_input)
        
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
            target_audience="developers",
            performance_requirements=[],
            custom_requirements={}
        )
    
    def _create_flexible_tech_stack(self, user_input: str) -> FlexibleTechStack:
        """创建灵活的技术栈"""
        user_input_lower = user_input.lower()
        
        # 检测语言
        if "python" in user_input_lower:
            language = "python"
            frameworks = []
            libraries = []
            tools = []
            
            # 检测Python相关技术
            if "pytorch" in user_input_lower or "torch" in user_input_lower:
                libraries.append("torch")
                libraries.append("torchvision")
                libraries.append("torchaudio")
            if "tensorflow" in user_input_lower or "tf" in user_input_lower:
                libraries.append("tensorflow")
            if "keras" in user_input_lower:
                libraries.append("keras")
            if "scikit" in user_input_lower or "sklearn" in user_input_lower:
                libraries.append("scikit-learn")
            if "pandas" in user_input_lower:
                libraries.append("pandas")
            if "numpy" in user_input_lower:
                libraries.append("numpy")
            if "matplotlib" in user_input_lower:
                libraries.append("matplotlib")
            if "seaborn" in user_input_lower:
                libraries.append("seaborn")
            if "jupyter" in user_input_lower:
                tools.append("jupyter")
            if "fastapi" in user_input_lower:
                frameworks.append("fastapi")
            if "flask" in user_input_lower:
                frameworks.append("flask")
            if "django" in user_input_lower:
                frameworks.append("django")
            if "streamlit" in user_input_lower:
                frameworks.append("streamlit")
            
            category = "machine_learning" if any(ml_word in user_input_lower for ml_word in ["model", "training", "neural", "deep", "ai", "ml"]) else "web"
            
        elif "javascript" in user_input_lower or "node" in user_input_lower or "js" in user_input_lower:
            language = "javascript"
            frameworks = []
            libraries = []
            tools = []
            
            if "express" in user_input_lower:
                frameworks.append("express")
            if "react" in user_input_lower:
                frameworks.append("react")
            if "vue" in user_input_lower:
                frameworks.append("vue")
            if "angular" in user_input_lower:
                frameworks.append("angular")
            if "next" in user_input_lower:
                frameworks.append("next.js")
            
            category = "web"
            
        elif "java" in user_input_lower:
            language = "java"
            frameworks = []
            libraries = []
            tools = []
            
            if "spring" in user_input_lower:
                frameworks.append("spring-boot")
            if "maven" in user_input_lower:
                tools.append("maven")
            if "gradle" in user_input_lower:
                tools.append("gradle")
            
            category = "web"
            
        elif "go" in user_input_lower or "golang" in user_input_lower:
            language = "go"
            frameworks = []
            libraries = []
            tools = []
            
            if "gin" in user_input_lower:
                frameworks.append("gin")
            if "echo" in user_input_lower:
                frameworks.append("echo")
            if "fiber" in user_input_lower:
                frameworks.append("fiber")
            
            category = "web"
            
        else:
            # 默认Python
            language = "python"
            frameworks = []
            libraries = ["torch", "numpy", "pandas"]
            tools = ["jupyter"]
            category = "machine_learning"
        
        return FlexibleTechStack(
            name=f"{language}_{category}",
            language=language,
            frameworks=frameworks,
            libraries=libraries,
            tools=tools,
            description=f"基于{language}的{category}技术栈",
            category=category
        )
    
    def _extract_project_name(self, user_input: str) -> str:
        """提取项目名称"""
        # 简单的名称提取逻辑
        words = user_input.split()
        for i, word in enumerate(words):
            if word.lower() in ["创建", "开发", "生成", "make", "create", "develop", "build", "训练", "train"]:
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
            "训练": "模型训练",
            "预测": "预测功能",
            "识别": "意图识别",
            "注意力": "多头注意力机制",
            "数据集": "数据集处理",
            "可视化": "数据可视化",
            "评估": "模型评估",
            "优化": "模型优化",
            "部署": "模型部署",
            "api": "API接口",
            "服务": "Web服务",
            "界面": "用户界面",
            "管理": "数据管理",
            "分析": "数据分析",
            "监控": "性能监控"
        }
        
        for keyword, feature in feature_keywords.items():
            if keyword in user_input_lower:
                features.append(feature)
        
        return features if features else ["基础功能"]
    
    def _assess_complexity(self, user_input_lower: str, features: List[str]) -> str:
        """评估项目复杂度"""
        complexity_indicators = {
            "simple": ["简单", "基础", "basic", "simple", "demo", "示例"],
            "medium": ["中等", "标准", "standard", "medium", "完整"],
            "complex": ["复杂", "高级", "advanced", "complex", "企业级", "enterprise", "生产"]
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
    
    def get_tech_stack_info(self, tech_stack: FlexibleTechStack) -> Dict[str, Any]:
        """获取技术栈信息"""
        return {
            "name": tech_stack.name,
            "language": tech_stack.language,
            "frameworks": tech_stack.frameworks,
            "libraries": tech_stack.libraries,
            "tools": tech_stack.tools,
            "description": tech_stack.description,
            "category": tech_stack.category
        }
