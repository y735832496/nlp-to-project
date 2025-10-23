"""
用户交互确认机制
在生成过程中让用户确认关键决策
"""
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from legacy.requirement_parser import ProjectRequirement, TechStack, ProjectType

class ConfirmationType(Enum):
    """确认类型枚举"""
    TECH_STACK = "tech_stack"
    PROJECT_NAME = "project_name"
    FEATURES = "features"
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    DEPLOYMENT = "deployment"
    COMPLEXITY = "complexity"

@dataclass
class ConfirmationRequest:
    """确认请求结构"""
    type: ConfirmationType
    title: str
    description: str
    current_value: Any
    options: List[Any]
    required: bool = True
    default_value: Any = None

@dataclass
class ConfirmationResult:
    """确认结果结构"""
    type: ConfirmationType
    confirmed: bool
    value: Any
    user_input: str

class UserInteractionManager:
    """用户交互管理器"""
    
    def __init__(self, interactive_mode: bool = True):
        self.interactive_mode = interactive_mode
        self.confirmation_history = []
    
    async def get_user_confirmations(self, requirements: ProjectRequirement) -> Dict[str, Any]:
        """获取用户确认信息"""
        confirmations = {}
        
        if not self.interactive_mode:
            # 非交互模式，使用默认值
            return self._get_default_confirmations(requirements)
        
        print("🤔 需要您的确认来优化项目生成...")
        print("=" * 50)
        
        # 技术栈确认
        if self._should_confirm_tech_stack(requirements):
            confirmation = await self._confirm_tech_stack(requirements)
            # 支持灵活的技术栈，直接使用当前技术栈
            confirmations["tech_stack"] = requirements.tech_stack
        
        # 项目名称确认
        if self._should_confirm_project_name(requirements):
            confirmation = await self._confirm_project_name(requirements)
            confirmations["project_name"] = confirmation.value
        
        # 功能需求确认
        if self._should_confirm_features(requirements):
            confirmation = await self._confirm_features(requirements)
            confirmations["features"] = confirmation.value
        
        # 数据库需求确认
        if self._should_confirm_database(requirements):
            confirmation = await self._confirm_database(requirements)
            confirmations["database"] = confirmation.value
        
        # 认证需求确认
        if self._should_confirm_authentication(requirements):
            confirmation = await self._confirm_authentication(requirements)
            confirmations["authentication"] = confirmation.value
        
        # 部署方式确认
        if self._should_confirm_deployment(requirements):
            confirmation = await self._confirm_deployment(requirements)
            confirmations["deployment"] = confirmation.value
        
        print("✅ 确认完成，开始生成项目...")
        print("=" * 50)
        
        return confirmations
    
    def _should_confirm_tech_stack(self, requirements: ProjectRequirement) -> bool:
        """判断是否需要确认技术栈"""
        # 如果技术栈不明确或用户输入模糊，需要确认
        return requirements.tech_stack == TechStack.PYTHON_FASTAPI and "python" not in requirements.description.lower()
    
    def _should_confirm_project_name(self, requirements: ProjectRequirement) -> bool:
        """判断是否需要确认项目名称"""
        return requirements.project_name == "ai-generated-project"
    
    def _should_confirm_features(self, requirements: ProjectRequirement) -> bool:
        """判断是否需要确认功能需求"""
        return len(requirements.features) == 0 or "基础功能" in requirements.features
    
    def _should_confirm_database(self, requirements: ProjectRequirement) -> bool:
        """判断是否需要确认数据库需求"""
        return not requirements.database_required and any(keyword in requirements.description.lower() 
                                                         for keyword in ["数据", "存储", "database", "db"])
    
    def _should_confirm_authentication(self, requirements: ProjectRequirement) -> bool:
        """判断是否需要确认认证需求"""
        return not requirements.authentication_required and any(keyword in requirements.description.lower() 
                                                              for keyword in ["用户", "登录", "认证", "auth", "user"])
    
    def _should_confirm_deployment(self, requirements: ProjectRequirement) -> bool:
        """判断是否需要确认部署方式"""
        return requirements.deployment_type == "local"
    
    async def _confirm_tech_stack(self, requirements: ProjectRequirement) -> ConfirmationResult:
        """确认技术栈"""
        print("\n🔧 技术栈选择")
        print("请选择您希望使用的技术栈：")
        
        # 支持灵活的技术栈，直接返回当前技术栈
        current_tech = getattr(requirements.tech_stack, 'name', str(requirements.tech_stack))
        print(f"✅ 当前技术栈: {current_tech}")
        print("✅ 技术栈已确认")
        
        return ConfirmationResult(
            type=ConfirmationType.TECH_STACK,
            confirmed=True,
            value=requirements.tech_stack,
            user_input=current_tech
        )
    
    async def _confirm_project_name(self, requirements: ProjectRequirement) -> ConfirmationResult:
        """确认项目名称"""
        print("\n📝 项目名称")
        print("请为您的项目输入一个名称：")
        
        while True:
            name = input(f"项目名称 (默认: {requirements.project_name}): ").strip()
            if not name:
                name = requirements.project_name
            
            # 验证项目名称
            if self._validate_project_name(name):
                print(f"✅ 项目名称: {name}")
                return ConfirmationResult(
                    type=ConfirmationType.PROJECT_NAME,
                    confirmed=True,
                    value=name,
                    user_input=name
                )
            else:
                print("❌ 项目名称只能包含字母、数字、连字符和下划线")
    
    async def _confirm_features(self, requirements: ProjectRequirement) -> ConfirmationResult:
        """确认功能需求"""
        print("\n⚡ 功能需求")
        print("请选择您需要的功能（可多选，用逗号分隔）：")
        
        feature_options = [
            ("用户认证", "authentication", "登录、注册、用户管理"),
            ("数据管理", "data_management", "CRUD操作、数据存储"),
            ("API接口", "api", "RESTful API、接口文档"),
            ("前端界面", "frontend", "Web界面、用户交互"),
            ("文件上传", "file_upload", "文件上传下载功能"),
            ("搜索功能", "search", "数据搜索和过滤"),
            ("统计分析", "analytics", "数据统计和分析"),
            ("实时通信", "realtime", "WebSocket、实时更新"),
            ("支付功能", "payment", "支付集成"),
            ("通知系统", "notification", "消息通知"),
        ]
        
        for i, (name, key, desc) in enumerate(feature_options, 1):
            print(f"{i}. {name} - {desc}")
        
        while True:
            try:
                choices = input(f"\n请选择功能 (1-{len(feature_options)}, 用逗号分隔): ").strip()
                if not choices:
                    selected_features = ["基础功能"]
                else:
                    choice_indices = [int(x.strip()) - 1 for x in choices.split(",")]
                    selected_features = [feature_options[i][0] for i in choice_indices if 0 <= i < len(feature_options)]
                
                if selected_features:
                    print(f"✅ 已选择功能: {', '.join(selected_features)}")
                    return ConfirmationResult(
                        type=ConfirmationType.FEATURES,
                        confirmed=True,
                        value=selected_features,
                        user_input=choices
                    )
                else:
                    print("❌ 请至少选择一个功能")
            except ValueError:
                print("❌ 请输入有效的数字")
    
    async def _confirm_database(self, requirements: ProjectRequirement) -> ConfirmationResult:
        """确认数据库需求"""
        print("\n🗄️ 数据库需求")
        print("您的项目是否需要数据库？")
        
        options = [
            ("是", True, "需要数据库存储数据"),
            ("否", False, "不需要数据库，使用内存存储"),
        ]
        
        for i, (name, value, desc) in enumerate(options, 1):
            print(f"{i}. {name} - {desc}")
        
        while True:
            try:
                choice = input(f"\n请选择 (1-{len(options)}, 默认1): ").strip()
                if not choice:
                    choice = "1"
                
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(options):
                    selected_value = options[choice_idx][1]
                    print(f"✅ 数据库需求: {'是' if selected_value else '否'}")
                    return ConfirmationResult(
                        type=ConfirmationType.DATABASE,
                        confirmed=True,
                        value=selected_value,
                        user_input=choice
                    )
                else:
                    print("❌ 无效选择，请重新输入")
            except ValueError:
                print("❌ 请输入有效数字")
    
    async def _confirm_authentication(self, requirements: ProjectRequirement) -> ConfirmationResult:
        """确认认证需求"""
        print("\n🔐 认证需求")
        print("您的项目是否需要用户认证？")
        
        options = [
            ("是", True, "需要用户登录、注册、权限管理"),
            ("否", False, "不需要用户认证，公开访问"),
        ]
        
        for i, (name, value, desc) in enumerate(options, 1):
            print(f"{i}. {name} - {desc}")
        
        while True:
            try:
                choice = input(f"\n请选择 (1-{len(options)}, 默认1): ").strip()
                if not choice:
                    choice = "1"
                
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(options):
                    selected_value = options[choice_idx][1]
                    print(f"✅ 认证需求: {'是' if selected_value else '否'}")
                    return ConfirmationResult(
                        type=ConfirmationType.AUTHENTICATION,
                        confirmed=True,
                        value=selected_value,
                        user_input=choice
                    )
                else:
                    print("❌ 无效选择，请重新输入")
            except ValueError:
                print("❌ 请输入有效数字")
    
    async def _confirm_deployment(self, requirements: ProjectRequirement) -> ConfirmationResult:
        """确认部署方式"""
        print("\n🚀 部署方式")
        print("您希望如何部署项目？")
        
        options = [
            ("本地运行", "local", "在本地开发环境运行"),
            ("Docker容器", "docker", "使用Docker容器化部署"),
            ("云服务", "cloud", "部署到云平台（如AWS、Azure、GCP）"),
        ]
        
        for i, (name, value, desc) in enumerate(options, 1):
            print(f"{i}. {name} - {desc}")
        
        while True:
            try:
                choice = input(f"\n请选择 (1-{len(options)}, 默认1): ").strip()
                if not choice:
                    choice = "1"
                
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(options):
                    selected_value = options[choice_idx][1]
                    print(f"✅ 部署方式: {options[choice_idx][0]}")
                    return ConfirmationResult(
                        type=ConfirmationType.DEPLOYMENT,
                        confirmed=True,
                        value=selected_value,
                        user_input=choice
                    )
                else:
                    print("❌ 无效选择，请重新输入")
            except ValueError:
                print("❌ 请输入有效数字")
    
    def _validate_project_name(self, name: str) -> bool:
        """验证项目名称"""
        import re
        # 项目名称只能包含字母、数字、连字符和下划线
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))
    
    def _get_default_confirmations(self, requirements: ProjectRequirement) -> Dict[str, Any]:
        """获取默认确认信息"""
        return {
            "tech_stack": requirements.tech_stack,
            "project_name": requirements.project_name,
            "features": requirements.features,
            "database": requirements.database_required,
            "authentication": requirements.authentication_required,
            "deployment": requirements.deployment_type
        }
    
    def get_confirmation_summary(self, confirmations: Dict[str, Any]) -> str:
        """获取确认信息摘要"""
        summary = "📋 项目确认信息：\n"
        summary += f"🔧 技术栈: {confirmations.get('tech_stack', 'N/A')}\n"
        summary += f"📝 项目名称: {confirmations.get('project_name', 'N/A')}\n"
        summary += f"⚡ 功能需求: {', '.join(confirmations.get('features', []))}\n"
        summary += f"🗄️ 数据库: {'是' if confirmations.get('database') else '否'}\n"
        summary += f"🔐 认证: {'是' if confirmations.get('authentication') else '否'}\n"
        summary += f"🚀 部署方式: {confirmations.get('deployment', 'N/A')}\n"
        return summary
