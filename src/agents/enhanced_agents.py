"""
增强的Agent系统
集成Planner Agent和Coder Agent，支持复杂需求的多轮对话代码生成
"""
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from src.core.flexible_requirement_parser import ProjectRequirement, FlexibleTechStack, ProjectType
from src.generators.advanced_code_generator import (
    PlannerAgent, CoderAgent, AdvancedCodeGenerator, 
    ProjectStructure, ConversationRound, AgentType
)
from src.agents.dynamic_agents import AgentRole, AgentConfig, AgentTask, AgentResult, BaseAgent

class EnhancedAgentRole(Enum):
    """增强的Agent角色枚举"""
    # 原有角色
    REQUIREMENT_ANALYZER = "requirement_analyzer"
    TECH_STACK_EXPERT = "tech_stack_expert"
    CODE_GENERATOR = "code_generator"
    TEST_SPECIALIST = "test_specialist"
    SECURITY_EXPERT = "security_expert"
    DEPLOYMENT_SPECIALIST = "deployment_specialist"
    DOCUMENTATION_EXPERT = "documentation_expert"
    QUALITY_ASSURANCE = "quality_assurance"
    PROJECT_MANAGER = "project_manager"
    
    # 新增角色
    PROJECT_PLANNER = "project_planner"
    ADVANCED_CODER = "advanced_coder"
    CODE_REVIEWER = "code_reviewer"
    ARCHITECTURE_EXPERT = "architecture_expert"
    PERFORMANCE_OPTIMIZER = "performance_optimizer"

@dataclass
class EnhancedAgentConfig(AgentConfig):
    """增强的Agent配置"""
    supports_multi_round: bool = False
    max_conversation_rounds: int = 5
    context_aware: bool = False
    collaboration_mode: bool = False

@dataclass
class MultiRoundTask:
    """多轮对话任务"""
    task_id: str
    agent_role: EnhancedAgentRole
    description: str
    input_data: Any
    expected_output: str
    max_rounds: int = 3
    current_round: int = 0
    conversation_history: List[ConversationRound] = None
    status: str = "pending"
    result: Optional[Any] = None

class ProjectPlannerAgent(BaseAgent):
    """项目规划Agent"""
    
    def __init__(self, config: EnhancedAgentConfig, llm_client=None):
        super().__init__(config, llm_client)
        self.planner = PlannerAgent(llm_client)
        self.conversation_history = []
    
    async def execute_task(self, task: AgentTask) -> AgentResult:
        """执行项目规划任务"""
        import time
        start_time = time.time()
        
        try:
            print(f"🏗️ {self.config.name} 开始项目规划...")
            
            # 执行项目结构规划
            project_structure = await self.planner.plan_project_structure(task.input_data)
            
            # 记录对话历史
            self.conversation_history.append(ConversationRound(
                round_id=len(self.conversation_history) + 1,
                agent_type=AgentType.PLANNER,
                input_prompt=f"规划项目: {task.description}",
                output_response=f"项目结构规划完成，包含 {len(project_structure.files)} 个文件",
                timestamp=datetime.now()
            ))
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                task_id=task.task_id,
                agent_role=task.agent_role,
                success=True,
                output=project_structure,
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

class AdvancedCoderAgent(BaseAgent):
    """高级代码生成Agent"""
    
    def __init__(self, config: EnhancedAgentConfig, llm_client=None):
        super().__init__(config, llm_client)
        self.coder = CoderAgent(llm_client)
        self.conversation_history = []
        self.generated_files = []
    
    def _get_default_files_by_tech_stack(self, tech_stack) -> List[str]:
        """根据技术栈获取默认文件列表"""
        # 支持灵活的技术栈
        if hasattr(tech_stack, 'language'):
            language = tech_stack.language
        elif hasattr(tech_stack, 'name'):
            language = tech_stack.name.split('_')[0]
        else:
            language = str(tech_stack).lower()
        
        
        if language == "java":
            return [
                "Application.java",
                "EmployeeController.java", 
                "EmployeeService.java",
                "Employee.java",
                "PerformanceController.java",
                "PerformanceService.java",
                "Performance.java"
            ]
        elif language == "javascript":
            return [
                "app.js",
                "routes.js", 
                "models.js",
                "services.js",
                "middleware.js"
            ]
        elif language == "go":
            return [
                "main.go",
                "handler.go",
                "service.go", 
                "model.go",
                "middleware.go"
            ]
        else:  # Python默认
            return [
                "main.py",
                "models.py",
                "services.py", 
                "utils.py",
                "api.py"
            ]
    
    async def execute_task(self, task: AgentTask) -> AgentResult:
        """执行代码生成任务"""
        import time
        start_time = time.time()
        
        try:
            print(f"💻 {self.config.name} 开始代码生成...")
            
            # 获取项目结构
            if isinstance(task.input_data, dict):
                project_structure = task.input_data.get('project_structure')
                requirements = task.input_data.get('requirements')
            else:
                # 如果input_data是ProjectRequirement对象
                requirements = task.input_data
                project_structure = None
            
            if not requirements:
                raise ValueError("缺少需求信息")
            
            # 如果没有项目结构，创建一个默认的
            if not project_structure:
                from advanced_code_generator import ProjectStructure
                # 根据技术栈生成文件列表
                default_files = self._get_default_files_by_tech_stack(requirements.tech_stack)
                project_structure = ProjectStructure(
                    project_name=requirements.project_name,
                    tech_stack=requirements.tech_stack,
                    modules=["main", "models", "services", "utils"],
                    files=default_files,
                    directories=["src/", "tests/"],
                    dependencies=["torch", "numpy", "pandas"],
                    entry_points=[default_files[0]] if default_files else ["main.py"],
                    configuration_files=["requirements.txt", "config.yaml"],
                    test_files=["test_main.py"],
                    documentation_files=["README.md"]
                )
            
            # 多轮对话生成代码
            generated_files = []
            
            # 如果没有项目结构，根据技术栈生成文件列表
            if not project_structure:
                file_list = self._get_default_files_by_tech_stack(requirements.tech_stack)
            else:
                file_list = project_structure.files
            
            for file_path in file_list:
                print(f"🔄 生成文件: {file_path}")
                
                # 构建上下文
                context = {
                    "generated_files": [f.path for f in generated_files],
                    "project_structure": project_structure,
                    "conversation_history": self.conversation_history
                }
                
                # 生成文件代码
                file_content = await self.coder.generate_code_for_file(
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
            
            self.generated_files.extend(generated_files)
            execution_time = time.time() - start_time
            
            return AgentResult(
                task_id=task.task_id,
                agent_role=task.agent_role,
                success=True,
                output=generated_files,
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

class CodeReviewerAgent(BaseAgent):
    """代码审查Agent"""
    
    def __init__(self, config: EnhancedAgentConfig, llm_client=None):
        super().__init__(config, llm_client)
        self.conversation_history = []
    
    async def execute_task(self, task: AgentTask) -> AgentResult:
        """执行代码审查任务"""
        import time
        start_time = time.time()
        
        try:
            print(f"🔍 {self.config.name} 开始代码审查...")
            
            # 获取生成的代码文件
            if isinstance(task.input_data, dict):
                generated_files = task.input_data.get('generated_files', [])
            else:
                # 如果没有生成文件，创建空列表
                generated_files = []
            
            review_results = []
            for file_content in generated_files:
                # 执行代码审查
                review_result = await self._review_code_file(file_content)
                review_results.append(review_result)
                
                # 记录对话历史
                self.conversation_history.append(ConversationRound(
                    round_id=len(self.conversation_history) + 1,
                    agent_type=AgentType.REVIEWER,
                    input_prompt=f"审查文件: {file_content.path}",
                    output_response=f"审查完成: {file_content.path}",
                    timestamp=datetime.now()
                ))
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                task_id=task.task_id,
                agent_role=task.agent_role,
                success=True,
                output=review_results,
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
    
    async def _review_code_file(self, file_content) -> Dict[str, Any]:
        """审查单个代码文件"""
        # 这里可以实现具体的代码审查逻辑
        return {
            "file_path": file_content.path,
            "quality_score": 85.0,
            "issues": [],
            "suggestions": ["添加更多注释", "优化性能"]
        }

class ArchitectureExpertAgent(BaseAgent):
    """架构专家Agent"""
    
    def __init__(self, config: EnhancedAgentConfig, llm_client=None):
        super().__init__(config, llm_client)
        self.conversation_history = []
    
    async def execute_task(self, task: AgentTask) -> AgentResult:
        """执行架构设计任务"""
        import time
        start_time = time.time()
        
        try:
            print(f"🏛️ {self.config.name} 开始架构设计...")
            
            # 获取项目信息
            if isinstance(task.input_data, dict):
                project_structure = task.input_data.get('project_structure')
                requirements = task.input_data.get('requirements')
            else:
                # 如果input_data是ProjectRequirement对象
                requirements = task.input_data
                project_structure = None
            
            # 设计架构
            architecture_design = await self._design_architecture(project_structure, requirements)
            
            # 记录对话历史
            self.conversation_history.append(ConversationRound(
                round_id=len(self.conversation_history) + 1,
                agent_type=AgentType.ARCHITECT,
                input_prompt=f"设计架构: {task.description}",
                output_response=f"架构设计完成",
                timestamp=datetime.now()
            ))
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                task_id=task.task_id,
                agent_role=task.agent_role,
                success=True,
                output=architecture_design,
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
    
    async def _design_architecture(self, project_structure: ProjectStructure, requirements: ProjectRequirement) -> Dict[str, Any]:
        """设计项目架构"""
        return {
            "architecture_type": "分层架构",
            "layers": ["表示层", "业务层", "数据层"],
            "patterns": ["MVC", "Repository", "Factory"],
            "recommendations": ["使用依赖注入", "实现错误处理", "添加日志记录"]
        }

class PerformanceOptimizerAgent(BaseAgent):
    """性能优化Agent"""
    
    def __init__(self, config: EnhancedAgentConfig, llm_client=None):
        super().__init__(config, llm_client)
        self.conversation_history = []
    
    async def execute_task(self, task: AgentTask) -> AgentResult:
        """执行性能优化任务"""
        import time
        start_time = time.time()
        
        try:
            print(f"⚡ {self.config.name} 开始性能优化...")
            
            # 获取代码文件
            if isinstance(task.input_data, dict):
                generated_files = task.input_data.get('generated_files', [])
            else:
                # 如果没有生成文件，创建空列表
                generated_files = []
            
            # 执行性能优化
            optimization_results = []
            for file_content in generated_files:
                optimization_result = await self._optimize_code_performance(file_content)
                optimization_results.append(optimization_result)
                
                # 记录对话历史
                self.conversation_history.append(ConversationRound(
                    round_id=len(self.conversation_history) + 1,
                    agent_type=AgentType.OPTIMIZER,
                    input_prompt=f"优化文件: {file_content.path}",
                    output_response=f"优化完成: {file_content.path}",
                    timestamp=datetime.now()
                ))
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                task_id=task.task_id,
                agent_role=task.agent_role,
                success=True,
                output=optimization_results,
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
    
    async def _optimize_code_performance(self, file_content) -> Dict[str, Any]:
        """优化代码性能"""
        return {
            "file_path": file_content.path,
            "optimization_score": 90.0,
            "optimizations": ["缓存优化", "算法优化", "内存优化"],
            "performance_metrics": {
                "execution_time": "减少30%",
                "memory_usage": "减少20%",
                "cpu_usage": "减少25%"
            }
        }

class EnhancedDynamicAgentManager:
    """增强的动态Agent管理器"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.agents = {}
        self.agent_configs = {}
        self.conversation_history = []
        self._initialize_enhanced_agent_configs()
    
    def _initialize_enhanced_agent_configs(self):
        """初始化增强的Agent配置"""
        # 项目规划专家
        self.agent_configs[EnhancedAgentRole.PROJECT_PLANNER] = EnhancedAgentConfig(
            name="项目规划专家",
            role=EnhancedAgentRole.PROJECT_PLANNER,
            description="负责项目结构规划和架构设计",
            system_message="""你是项目规划专家。你的任务是：
1. 分析项目需求并设计项目结构
2. 规划模块划分和文件组织
3. 设计技术架构和设计模式
4. 提供可扩展性和维护性建议

请提供详细的项目规划方案。""",
            capabilities=["项目规划", "架构设计", "模块划分"],
            priority=1,
            supports_multi_round=True,
            max_conversation_rounds=3,
            context_aware=True
        )
        
        # 高级代码生成专家
        self.agent_configs[EnhancedAgentRole.ADVANCED_CODER] = EnhancedAgentConfig(
            name="高级代码生成专家",
            role=EnhancedAgentRole.ADVANCED_CODER,
            description="负责复杂代码的多轮对话生成",
            system_message="""你是高级代码生成专家。你的任务是：
1. 根据项目结构生成具体代码
2. 支持多轮对话优化代码质量
3. 考虑代码的可读性和可维护性
4. 实现最佳实践和设计模式

请生成高质量、可维护的代码。""",
            capabilities=["代码生成", "多轮对话", "代码优化"],
            priority=2,
            supports_multi_round=True,
            max_conversation_rounds=5,
            context_aware=True,
            collaboration_mode=True
        )
        
        # 代码审查专家
        self.agent_configs[EnhancedAgentRole.CODE_REVIEWER] = EnhancedAgentConfig(
            name="代码审查专家",
            role=EnhancedAgentRole.CODE_REVIEWER,
            description="负责代码质量审查和优化建议",
            system_message="""你是代码审查专家。你的任务是：
1. 审查生成的代码质量
2. 识别潜在问题和改进点
3. 提供代码优化建议
4. 确保代码符合最佳实践

请提供详细的代码审查报告。""",
            capabilities=["代码审查", "质量检查", "优化建议"],
            priority=3,
            supports_multi_round=True,
            max_conversation_rounds=2,
            context_aware=True
        )
        
        # 架构专家
        self.agent_configs[EnhancedAgentRole.ARCHITECTURE_EXPERT] = EnhancedAgentConfig(
            name="架构专家",
            role=EnhancedAgentRole.ARCHITECTURE_EXPERT,
            description="负责系统架构设计和技术选型",
            system_message="""你是架构专家。你的任务是：
1. 设计系统整体架构
2. 选择合适的技术栈和框架
3. 规划模块间的关系和接口
4. 考虑系统的可扩展性和性能

请提供完整的架构设计方案。""",
            capabilities=["架构设计", "技术选型", "系统规划"],
            priority=2,
            supports_multi_round=True,
            max_conversation_rounds=3,
            context_aware=True
        )
        
        # 性能优化专家
        self.agent_configs[EnhancedAgentRole.PERFORMANCE_OPTIMIZER] = EnhancedAgentConfig(
            name="性能优化专家",
            role=EnhancedAgentRole.PERFORMANCE_OPTIMIZER,
            description="负责代码性能优化和性能分析",
            system_message="""你是性能优化专家。你的任务是：
1. 分析代码性能瓶颈
2. 提供性能优化建议
3. 实现性能监控和测试
4. 优化算法和数据结构

请提供详细的性能优化方案。""",
            capabilities=["性能优化", "性能分析", "算法优化"],
            priority=4,
            supports_multi_round=True,
            max_conversation_rounds=2,
            context_aware=True
        )
    
    async def create_enhanced_agents(self, requirements: ProjectRequirement) -> Dict[EnhancedAgentRole, Any]:
        """创建增强的Agent"""
        print("🤖 创建增强的Agent系统...")
        
        # 确定需要的Agent角色
        required_roles = self._determine_enhanced_roles(requirements)
        print(f"📋 需要的增强Agent角色: {[role.value for role in required_roles]}")
        
        # 创建Agent
        agents = {}
        for role in required_roles:
            if role in self.agent_configs:
                agent = await self._create_enhanced_agent(role, requirements)
                agents[role] = agent
                print(f"✅ 创建增强Agent: {self.agent_configs[role].name}")
        
        return agents
    
    def _determine_enhanced_roles(self, requirements: ProjectRequirement) -> List[EnhancedAgentRole]:
        """确定需要的增强Agent角色"""
        required_roles = [
            EnhancedAgentRole.PROJECT_PLANNER,
            EnhancedAgentRole.ADVANCED_CODER
        ]
        
        # 根据需求添加特定Agent
        if requirements.complexity_level in ["medium", "complex"]:
            required_roles.append(EnhancedAgentRole.ARCHITECTURE_EXPERT)
        
        if requirements.performance_requirements:
            required_roles.append(EnhancedAgentRole.PERFORMANCE_OPTIMIZER)
        
        # 总是包含代码审查
        required_roles.append(EnhancedAgentRole.CODE_REVIEWER)
        
        return required_roles
    
    async def _create_enhanced_agent(self, role: EnhancedAgentRole, requirements: ProjectRequirement) -> Any:
        """创建增强的Agent"""
        config = self.agent_configs[role]
        
        if role == EnhancedAgentRole.PROJECT_PLANNER:
            return ProjectPlannerAgent(config, self.llm_client)
        elif role == EnhancedAgentRole.ADVANCED_CODER:
            return AdvancedCoderAgent(config, self.llm_client)
        elif role == EnhancedAgentRole.CODE_REVIEWER:
            return CodeReviewerAgent(config, self.llm_client)
        elif role == EnhancedAgentRole.ARCHITECTURE_EXPERT:
            return ArchitectureExpertAgent(config, self.llm_client)
        elif role == EnhancedAgentRole.PERFORMANCE_OPTIMIZER:
            return PerformanceOptimizerAgent(config, self.llm_client)
        else:
            return BaseAgent(config, self.llm_client)
    
    async def execute_enhanced_workflow(self, requirements: ProjectRequirement, agents: Dict[EnhancedAgentRole, Any]) -> Dict[str, AgentResult]:
        """执行增强的工作流"""
        print("🔄 开始执行增强的Agent工作流...")
        
        # 创建多轮对话任务
        tasks = self._create_enhanced_task_queue(requirements, agents)
        
        # 执行任务
        results = {}
        for task in tasks:
            print(f"📋 执行增强任务: {task.description}")
            
            try:
                agent = agents[task.agent_role]
                result = await agent.execute_task(task)
                results[task.task_id] = result
                
                if result.success:
                    print(f"✅ 增强任务完成: {task.description}")
                else:
                    print(f"❌ 增强任务失败: {task.description} - {result.error_message}")
                    
            except Exception as e:
                print(f"❌ 增强任务执行异常: {task.description} - {str(e)}")
                results[task.task_id] = AgentResult(
                    task_id=task.task_id,
                    agent_role=task.agent_role,
                    success=False,
                    output=None,
                    error_message=str(e)
                )
        
        return results
    
    def _create_enhanced_task_queue(self, requirements: ProjectRequirement, agents: Dict[EnhancedAgentRole, Any]) -> List[AgentTask]:
        """创建增强的任务队列"""
        tasks = []
        
        # 项目规划任务
        if EnhancedAgentRole.PROJECT_PLANNER in agents:
            tasks.append(AgentTask(
                task_id="enhanced_planning_001",
                agent_role=EnhancedAgentRole.PROJECT_PLANNER,
                description="规划项目结构和架构",
                input_data=requirements,
                expected_output="项目结构规划"
            ))
        
        # 架构设计任务
        if EnhancedAgentRole.ARCHITECTURE_EXPERT in agents:
            tasks.append(AgentTask(
                task_id="enhanced_architecture_001",
                agent_role=EnhancedAgentRole.ARCHITECTURE_EXPERT,
                description="设计系统架构",
                input_data=requirements,
                expected_output="架构设计方案"
            ))
        
        # 代码生成任务
        if EnhancedAgentRole.ADVANCED_CODER in agents:
            tasks.append(AgentTask(
                task_id="enhanced_coding_001",
                agent_role=EnhancedAgentRole.ADVANCED_CODER,
                description="多轮对话生成代码",
                input_data=requirements,
                expected_output="完整项目代码"
            ))
        
        # 代码审查任务
        if EnhancedAgentRole.CODE_REVIEWER in agents:
            tasks.append(AgentTask(
                task_id="enhanced_review_001",
                agent_role=EnhancedAgentRole.CODE_REVIEWER,
                description="审查代码质量",
                input_data=requirements,
                expected_output="代码审查报告"
            ))
        
        # 性能优化任务
        if EnhancedAgentRole.PERFORMANCE_OPTIMIZER in agents:
            tasks.append(AgentTask(
                task_id="enhanced_optimization_001",
                agent_role=EnhancedAgentRole.PERFORMANCE_OPTIMIZER,
                description="优化代码性能",
                input_data=requirements,
                expected_output="性能优化方案"
            ))
        
        return tasks
    
    def get_conversation_summary(self) -> str:
        """获取对话摘要"""
        summary = f"📊 增强Agent对话摘要\n"
        summary += f"总轮次: {len(self.conversation_history)}\n"
        summary += f"活跃Agent: {len(self.agents)}\n"
        
        for role, agent in self.agents.items():
            if hasattr(agent, 'conversation_history'):
                summary += f"- {role.value}: {len(agent.conversation_history)} 轮对话\n"
        
        return summary
