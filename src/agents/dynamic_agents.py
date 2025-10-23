"""
动态Agent系统
支持动态创建和配置不同类型的专家Agent
"""
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from legacy.requirement_parser import ProjectRequirement, TechStack, ProjectType

class AgentRole(Enum):
    """Agent角色枚举"""
    REQUIREMENT_ANALYZER = "requirement_analyzer"
    TECH_STACK_EXPERT = "tech_stack_expert"
    CODE_GENERATOR = "code_generator"
    TEST_SPECIALIST = "test_specialist"
    SECURITY_EXPERT = "security_expert"
    DEPLOYMENT_SPECIALIST = "deployment_specialist"
    DOCUMENTATION_EXPERT = "documentation_expert"
    QUALITY_ASSURANCE = "quality_assurance"
    PROJECT_MANAGER = "project_manager"

@dataclass
class AgentConfig:
    """Agent配置结构"""
    name: str
    role: AgentRole
    description: str
    system_message: str
    capabilities: List[str]
    priority: int = 1
    dependencies: List[AgentRole] = None

@dataclass
class AgentTask:
    """Agent任务结构"""
    task_id: str
    agent_role: AgentRole
    description: str
    input_data: Any
    expected_output: str
    priority: int = 1
    dependencies: List[str] = None

@dataclass
class AgentResult:
    """Agent执行结果"""
    task_id: str
    agent_role: AgentRole
    success: bool
    output: Any
    error_message: Optional[str] = None
    execution_time: float = 0.0

class DynamicAgentManager:
    """动态Agent管理器"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.agents = {}
        self.agent_configs = {}
        self.task_queue = []
        self.results = {}
        self._initialize_agent_configs()
    
    def _initialize_agent_configs(self):
        """初始化Agent配置"""
        # 需求分析专家
        self.agent_configs[AgentRole.REQUIREMENT_ANALYZER] = AgentConfig(
            name="需求分析专家",
            role=AgentRole.REQUIREMENT_ANALYZER,
            description="分析用户需求，提取关键信息",
            system_message="""你是需求分析专家。你的任务是：
1. 分析用户的自然语言需求
2. 提取项目类型、技术栈、功能需求
3. 识别潜在的技术挑战
4. 提供需求优化建议

请以结构化的方式输出分析结果。""",
            capabilities=["需求分析", "技术选型", "风险评估"],
            priority=1
        )
        
        # 技术栈专家
        self.agent_configs[AgentRole.TECH_STACK_EXPERT] = AgentConfig(
            name="技术栈专家",
            role=AgentRole.TECH_STACK_EXPERT,
            description="提供技术栈选择和架构建议",
            system_message="""你是技术栈专家。你的任务是：
1. 根据需求推荐最适合的技术栈
2. 分析技术栈的优缺点
3. 提供架构设计建议
4. 考虑性能和可扩展性

请提供详细的技术选型理由。""",
            capabilities=["技术选型", "架构设计", "性能优化"],
            priority=2,
            dependencies=[AgentRole.REQUIREMENT_ANALYZER]
        )
        
        # 代码生成专家
        self.agent_configs[AgentRole.CODE_GENERATOR] = AgentConfig(
            name="代码生成专家",
            role=AgentRole.CODE_GENERATOR,
            description="根据需求生成高质量代码",
            system_message="""你是代码生成专家。你的任务是：
1. 根据需求和技术栈生成完整代码
2. 遵循最佳实践和编码规范
3. 确保代码可读性和可维护性
4. 包含适当的错误处理

请生成完整、可运行的代码。""",
            capabilities=["代码生成", "最佳实践", "错误处理"],
            priority=3,
            dependencies=[AgentRole.TECH_STACK_EXPERT]
        )
        
        # 测试专家
        self.agent_configs[AgentRole.TEST_SPECIALIST] = AgentConfig(
            name="测试专家",
            role=AgentRole.TEST_SPECIALIST,
            description="生成测试用例和测试策略",
            system_message="""你是测试专家。你的任务是：
1. 生成全面的测试用例
2. 设计测试策略和测试计划
3. 确保测试覆盖率
4. 提供自动化测试方案

请生成完整的测试套件。""",
            capabilities=["测试设计", "测试自动化", "质量保证"],
            priority=4,
            dependencies=[AgentRole.CODE_GENERATOR]
        )
        
        # 安全专家
        self.agent_configs[AgentRole.SECURITY_EXPERT] = AgentConfig(
            name="安全专家",
            role=AgentRole.SECURITY_EXPERT,
            description="提供安全建议和实现安全功能",
            system_message="""你是安全专家。你的任务是：
1. 识别潜在的安全风险
2. 提供安全实现方案
3. 生成安全配置
4. 建议安全最佳实践

请提供全面的安全解决方案。""",
            capabilities=["安全分析", "安全实现", "安全配置"],
            priority=3,
            dependencies=[AgentRole.CODE_GENERATOR]
        )
        
        # 部署专家
        self.agent_configs[AgentRole.DEPLOYMENT_SPECIALIST] = AgentConfig(
            name="部署专家",
            role=AgentRole.DEPLOYMENT_SPECIALIST,
            description="提供部署和运维建议",
            system_message="""你是部署专家。你的任务是：
1. 设计部署架构
2. 生成部署配置
3. 提供监控和日志方案
4. 建议运维最佳实践

请提供完整的部署解决方案。""",
            capabilities=["部署设计", "配置管理", "运维监控"],
            priority=4,
            dependencies=[AgentRole.CODE_GENERATOR]
        )
        
        # 文档专家
        self.agent_configs[AgentRole.DOCUMENTATION_EXPERT] = AgentConfig(
            name="文档专家",
            role=AgentRole.DOCUMENTATION_EXPERT,
            description="生成项目文档和API文档",
            system_message="""你是文档专家。你的任务是：
1. 生成项目README文档
2. 创建API文档
3. 编写用户指南
4. 提供开发文档

请生成清晰、完整的文档。""",
            capabilities=["文档编写", "API文档", "用户指南"],
            priority=3,
            dependencies=[AgentRole.CODE_GENERATOR]
        )
        
        # 质量保证专家
        self.agent_configs[AgentRole.QUALITY_ASSURANCE] = AgentConfig(
            name="质量保证专家",
            role=AgentRole.QUALITY_ASSURANCE,
            description="进行代码质量检查和优化建议",
            system_message="""你是质量保证专家。你的任务是：
1. 检查代码质量
2. 提供优化建议
3. 确保代码规范
4. 评估性能指标

请提供详细的质量评估报告。""",
            capabilities=["质量检查", "性能优化", "代码规范"],
            priority=5,
            dependencies=[AgentRole.CODE_GENERATOR, AgentRole.TEST_SPECIALIST]
        )
        
        # 项目经理
        self.agent_configs[AgentRole.PROJECT_MANAGER] = AgentConfig(
            name="项目经理",
            role=AgentRole.PROJECT_MANAGER,
            description="协调整个项目开发流程",
            system_message="""你是项目经理。你的任务是：
1. 协调各个专家Agent的工作
2. 制定项目计划和时间表
3. 监控项目进度
4. 处理项目风险

请确保项目按时、高质量完成。""",
            capabilities=["项目管理", "进度监控", "风险控制"],
            priority=1,
            dependencies=[]
        )
    
    async def create_dynamic_agents(self, requirements: ProjectRequirement) -> Dict[AgentRole, Any]:
        """根据需求动态创建Agent"""
        print("🤖 根据需求动态创建Agent...")
        
        # 确定需要的Agent角色
        required_roles = self._determine_required_roles(requirements)
        print(f"📋 需要的Agent角色: {[role.value for role in required_roles]}")
        
        # 创建Agent
        agents = {}
        for role in required_roles:
            if role in self.agent_configs:
                agent = await self._create_agent(role, requirements)
                agents[role] = agent
                print(f"✅ 创建Agent: {self.agent_configs[role].name}")
        
        return agents
    
    def _determine_required_roles(self, requirements: ProjectRequirement) -> List[AgentRole]:
        """确定需要的Agent角色"""
        required_roles = [
            AgentRole.PROJECT_MANAGER,
            AgentRole.REQUIREMENT_ANALYZER,
            AgentRole.TECH_STACK_EXPERT,
            AgentRole.CODE_GENERATOR
        ]
        
        # 根据需求添加特定Agent
        if requirements.authentication_required:
            required_roles.append(AgentRole.SECURITY_EXPERT)
        
        if requirements.database_required:
            required_roles.append(AgentRole.DEPLOYMENT_SPECIALIST)
        
        # 总是包含测试和质量保证
        required_roles.extend([
            AgentRole.TEST_SPECIALIST,
            AgentRole.QUALITY_ASSURANCE,
            AgentRole.DOCUMENTATION_EXPERT
        ])
        
        return required_roles
    
    async def _create_agent(self, role: AgentRole, requirements: ProjectRequirement) -> Any:
        """创建单个Agent"""
        config = self.agent_configs[role]
        
        # 根据角色创建特定的Agent实现
        if role == AgentRole.REQUIREMENT_ANALYZER:
            return RequirementAnalyzerAgent(config, self.llm_client)
        elif role == AgentRole.TECH_STACK_EXPERT:
            return TechStackExpertAgent(config, self.llm_client)
        elif role == AgentRole.CODE_GENERATOR:
            return CodeGeneratorAgent(config, self.llm_client)
        elif role == AgentRole.TEST_SPECIALIST:
            return TestSpecialistAgent(config, self.llm_client)
        elif role == AgentRole.SECURITY_EXPERT:
            return SecurityExpertAgent(config, self.llm_client)
        elif role == AgentRole.DEPLOYMENT_SPECIALIST:
            return DeploymentSpecialistAgent(config, self.llm_client)
        elif role == AgentRole.DOCUMENTATION_EXPERT:
            return DocumentationExpertAgent(config, self.llm_client)
        elif role == AgentRole.QUALITY_ASSURANCE:
            return QualityAssuranceAgent(config, self.llm_client)
        elif role == AgentRole.PROJECT_MANAGER:
            return ProjectManagerAgent(config, self.llm_client)
        else:
            return BaseAgent(config, self.llm_client)
    
    async def execute_agent_workflow(self, requirements: ProjectRequirement, agents: Dict[AgentRole, Any]) -> Dict[str, AgentResult]:
        """执行Agent工作流"""
        print("🔄 开始执行Agent工作流...")
        
        # 创建任务队列
        tasks = self._create_task_queue(requirements, agents)
        
        # 执行任务
        results = {}
        for task in tasks:
            print(f"📋 执行任务: {task.description}")
            
            try:
                agent = agents[task.agent_role]
                result = await agent.execute_task(task)
                results[task.task_id] = result
                
                if result.success:
                    print(f"✅ 任务完成: {task.description}")
                else:
                    print(f"❌ 任务失败: {task.description} - {result.error_message}")
                    
            except Exception as e:
                print(f"❌ 任务执行异常: {task.description} - {str(e)}")
                results[task.task_id] = AgentResult(
                    task_id=task.task_id,
                    agent_role=task.agent_role,
                    success=False,
                    output=None,
                    error_message=str(e)
                )
        
        return results
    
    def _create_task_queue(self, requirements: ProjectRequirement, agents: Dict[AgentRole, Any]) -> List[AgentTask]:
        """创建任务队列"""
        tasks = []
        
        # 需求分析任务
        if AgentRole.REQUIREMENT_ANALYZER in agents:
            tasks.append(AgentTask(
                task_id="req_analysis_001",
                agent_role=AgentRole.REQUIREMENT_ANALYZER,
                description="分析用户需求",
                input_data=requirements,
                expected_output="需求分析报告"
            ))
        
        # 技术栈选择任务
        if AgentRole.TECH_STACK_EXPERT in agents:
            tasks.append(AgentTask(
                task_id="tech_stack_001",
                agent_role=AgentRole.TECH_STACK_EXPERT,
                description="选择技术栈",
                input_data=requirements,
                expected_output="技术栈建议"
            ))
        
        # 代码生成任务
        if AgentRole.CODE_GENERATOR in agents:
            tasks.append(AgentTask(
                task_id="code_gen_001",
                agent_role=AgentRole.CODE_GENERATOR,
                description="生成项目代码",
                input_data=requirements,
                expected_output="完整项目代码"
            ))
        
        # 测试生成任务
        if AgentRole.TEST_SPECIALIST in agents:
            tasks.append(AgentTask(
                task_id="test_gen_001",
                agent_role=AgentRole.TEST_SPECIALIST,
                description="生成测试用例",
                input_data=requirements,
                expected_output="测试套件"
            ))
        
        # 安全配置任务
        if AgentRole.SECURITY_EXPERT in agents and requirements.authentication_required:
            tasks.append(AgentTask(
                task_id="security_001",
                agent_role=AgentRole.SECURITY_EXPERT,
                description="配置安全功能",
                input_data=requirements,
                expected_output="安全配置"
            ))
        
        # 部署配置任务
        if AgentRole.DEPLOYMENT_SPECIALIST in agents:
            tasks.append(AgentTask(
                task_id="deployment_001",
                agent_role=AgentRole.DEPLOYMENT_SPECIALIST,
                description="配置部署方案",
                input_data=requirements,
                expected_output="部署配置"
            ))
        
        # 文档生成任务
        if AgentRole.DOCUMENTATION_EXPERT in agents:
            tasks.append(AgentTask(
                task_id="doc_gen_001",
                agent_role=AgentRole.DOCUMENTATION_EXPERT,
                description="生成项目文档",
                input_data=requirements,
                expected_output="项目文档"
            ))
        
        # 质量检查任务
        if AgentRole.QUALITY_ASSURANCE in agents:
            tasks.append(AgentTask(
                task_id="qa_check_001",
                agent_role=AgentRole.QUALITY_ASSURANCE,
                description="进行质量检查",
                input_data=requirements,
                expected_output="质量报告"
            ))
        
        return tasks

class BaseAgent:
    """基础Agent类"""
    
    def __init__(self, config: AgentConfig, llm_client=None):
        self.config = config
        self.llm_client = llm_client
    
    async def execute_task(self, task: AgentTask) -> AgentResult:
        """执行任务"""
        import time
        start_time = time.time()
        
        try:
            # 构建提示
            prompt = self._build_prompt(task)
            
            # 调用LLM
            if self.llm_client and not getattr(self.llm_client, 'use_mock', True):
                messages = [{"role": "user", "content": prompt}]
                response = await self.llm_client.create(messages)
                output = response["choices"][0]["message"]["content"]
            else:
                output = self._mock_execution(task)
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                task_id=task.task_id,
                agent_role=task.agent_role,
                success=True,
                output=output,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return AgentResult(
                task_id=task.task_id,
                agent_role=task.agent_role,
                success=False,
                output=None,
                error_message=str(e),
                execution_time=execution_time
            )
    
    def _build_prompt(self, task: AgentTask) -> str:
        """构建提示"""
        return f"""
{self.config.system_message}

任务描述: {task.description}
输入数据: {task.input_data}
期望输出: {task.expected_output}

请根据你的专业领域完成任务。
"""
    
    def _mock_execution(self, task: AgentTask) -> str:
        """模拟执行"""
        return f"[{self.config.name}] 模拟执行任务: {task.description}"

class RequirementAnalyzerAgent(BaseAgent):
    """需求分析专家Agent"""
    
    def _mock_execution(self, task: AgentTask) -> str:
        """模拟需求分析"""
        return f"""
需求分析报告
================

项目名称: {task.input_data.project_name}
技术栈: {task.input_data.tech_stack.value}
项目类型: {task.input_data.project_type.value}

功能需求:
{chr(10).join(f"- {feature}" for feature in task.input_data.features)}

技术要求:
- 数据库: {'是' if task.input_data.database_required else '否'}
- 认证: {'是' if task.input_data.authentication_required else '否'}
- API: {'是' if task.input_data.api_required else '否'}
- 前端: {'是' if task.input_data.frontend_required else '否'}

复杂度评估: {task.input_data.complexity_level}
"""

class TechStackExpertAgent(BaseAgent):
    """技术栈专家Agent"""
    
    def _mock_execution(self, task: AgentTask) -> str:
        """模拟技术栈分析"""
        return f"""
技术栈分析报告
================

推荐技术栈: {task.input_data.tech_stack.value}
技术栈优势:
- 性能优秀
- 生态丰富
- 社区活跃
- 文档完善

架构建议:
- 采用分层架构
- 使用依赖注入
- 实现错误处理
- 添加日志记录
"""

class CodeGeneratorAgent(BaseAgent):
    """代码生成专家Agent"""
    
    def _mock_execution(self, task: AgentTask) -> str:
        """模拟代码生成"""
        return f"""
代码生成报告
================

已生成项目代码:
- 主应用文件
- 配置文件
- 依赖管理
- 测试文件
- 文档文件

代码特性:
- 遵循最佳实践
- 包含错误处理
- 支持扩展
- 易于维护
"""

class TestSpecialistAgent(BaseAgent):
    """测试专家Agent"""
    
    def _mock_execution(self, task: AgentTask) -> str:
        """模拟测试生成"""
        return f"""
测试策略报告
================

测试覆盖:
- 单元测试: 80%
- 集成测试: 60%
- 端到端测试: 40%

测试用例:
- 功能测试
- 性能测试
- 安全测试
- 兼容性测试

自动化测试:
- CI/CD集成
- 持续监控
- 质量门禁
"""

class SecurityExpertAgent(BaseAgent):
    """安全专家Agent"""
    
    def _mock_execution(self, task: AgentTask) -> str:
        """模拟安全分析"""
        return f"""
安全分析报告
================

安全措施:
- 输入验证
- 身份认证
- 授权控制
- 数据加密

安全配置:
- HTTPS强制
- 安全头设置
- 跨域控制
- 敏感信息保护
"""

class DeploymentSpecialistAgent(BaseAgent):
    """部署专家Agent"""
    
    def _mock_execution(self, task: AgentTask) -> str:
        """模拟部署分析"""
        return f"""
部署策略报告
================

部署方案:
- 容器化部署
- 微服务架构
- 负载均衡
- 自动扩缩容

监控告警:
- 性能监控
- 错误追踪
- 日志分析
- 健康检查
"""

class DocumentationExpertAgent(BaseAgent):
    """文档专家Agent"""
    
    def _mock_execution(self, task: AgentTask) -> str:
        """模拟文档生成"""
        return f"""
文档生成报告
================

已生成文档:
- README.md
- API文档
- 用户指南
- 开发文档

文档特性:
- 结构清晰
- 内容完整
- 示例丰富
- 易于理解
"""

class QualityAssuranceAgent(BaseAgent):
    """质量保证专家Agent"""
    
    def _mock_execution(self, task: AgentTask) -> str:
        """模拟质量检查"""
        return f"""
质量检查报告
================

代码质量:
- 语法检查: 通过
- 规范检查: 通过
- 复杂度: 适中
- 可读性: 良好

测试质量:
- 覆盖率: 85%
- 通过率: 100%
- 性能: 优秀
- 稳定性: 良好
"""

class ProjectManagerAgent(BaseAgent):
    """项目经理Agent"""
    
    def _mock_execution(self, task: AgentTask) -> str:
        """模拟项目管理"""
        return f"""
项目管理报告
================

项目状态:
- 进度: 100%
- 质量: 优秀
- 风险: 低
- 交付: 按时

团队协作:
- 任务分配: 完成
- 进度跟踪: 正常
- 质量把控: 严格
- 风险控制: 有效
"""
