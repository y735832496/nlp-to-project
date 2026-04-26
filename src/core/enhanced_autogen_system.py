"""
增强的动态AutoGen系统
集成Planner Agent和Coder Agent，支持复杂需求的多轮对话代码生成
"""
import os
import sys
import asyncio
import tempfile
import subprocess
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import shutil

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入基础模块
from src.core.flexible_requirement_parser import FlexibleRequirementParser, ProjectRequirement, FlexibleTechStack, ProjectType
from src.generators.project_templates import ProjectTemplateManager
from src.managers.user_interaction import UserInteractionManager
from src.managers.code_quality import CodeQualityChecker, QualityReport
from src.managers.configuration_management import ConfigurationManager
from src.managers.extensibility import ExtensionManager, ExtensionType

# 导入增强模块
from src.generators.advanced_code_generator import AdvancedCodeGenerator, ProjectStructure
from src.agents.enhanced_agents import EnhancedDynamicAgentManager, EnhancedAgentRole

# 导入执行反馈循环模块
from src.core.execution_sandbox import ExecutionSandbox
from src.core.iteration_loop import IterationLoop

# 导入质量闭环模块
from src.core.quality_loop import QualityLoop
from src.core.auto_fixer import AutoFixer

# 导入 GLM Coding Plan 引擎
from src.core.glm_coding_plan import GLMCodingPlan

# 导入AutoGen相关模块
try:
    from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
    from autogen_agentchat.teams import RoundRobinGroupChat
    from autogen_agentchat.messages import TextMessage
    AUTOGEN_AVAILABLE = True
    print("✅ AutoGen 0.10.0 导入成功")
except ImportError as e:
    print(f"❌ AutoGen 0.10.0 导入失败: {e}")
    AUTOGEN_AVAILABLE = False

# 导入GitHub相关模块
try:
    from github import Github
    GITHUB_AVAILABLE = True
    print("✅ PyGithub 导入成功")
except ImportError:
    print("❌ 请安装PyGithub: pip install PyGithub")
    GITHUB_AVAILABLE = False

class RealLLMClient:
    """真实的LLM客户端，支持 GLM-5 thinking + function calling"""

    # 支持的模型列表（优先级从高到低）
    SUPPORTED_MODELS = ["glm-5", "glm-4-air"]
    DEFAULT_MODEL = "glm-5"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ZHIPU_API_KEY")
        if not self.api_key:
            print("⚠️ 未配置ZHIPU_API_KEY，将使用模拟模式")
            self.use_mock = True
        else:
            self.use_mock = False
            try:
                from zhipuai import ZhipuAI
                self.client = ZhipuAI(api_key=self.api_key)
                print("✅ GLM 客户端初始化成功")
            except ImportError:
                print("❌ 请安装zhipuai: pip install zhipuai")
                self.use_mock = True

        self.model_info = {
            "vision": False,
            "max_tokens": 8192,
            "supports_streaming": True,
            "supports_tools": True,  # GLM-5 支持 function calling
            "supports_thinking": True,  # GLM-5 支持 thinking 模式
            "default_model": self.DEFAULT_MODEL,
        }

    async def create(
        self,
        messages: List[Any],
        model: str = None,
        thinking: bool = False,
        tools: List[Dict] = None,
        tool_choice: str = "auto",
        stream: bool = False,
        **kwargs,
    ) -> Dict:
        """
        创建聊天完成，支持 GLM-5 全部能力。

        Args:
            messages: 消息列表
            model: 模型名，默认 glm-5
            thinking: 是否开启深度思考模式
            tools: function calling 工具定义列表
            tool_choice: 工具选择策略 (auto/none/required)
            stream: 是否流式输出
        """
        if model is None:
            model = self.DEFAULT_MODEL

        if self.use_mock:
            return self._mock_completion(messages)

        try:
            formatted_messages = self._format_messages(messages)
            if not formatted_messages:
                formatted_messages = [{"role": "user", "content": "请生成代码"}]

            # 构建请求参数
            create_kwargs = {
                "model": model,
                "messages": formatted_messages,
                "max_tokens": kwargs.get("max_tokens", 8192),
            }

            # thinking 模式要求 temperature=1.0
            if thinking:
                create_kwargs["thinking"] = {"type": "enabled"}
                create_kwargs["temperature"] = 1.0
            else:
                create_kwargs["temperature"] = kwargs.get("temperature", 0.1)

            # function calling 工具
            if tools:
                create_kwargs["tools"] = tools
                create_kwargs["tool_choice"] = tool_choice

            # 流式输出
            if stream:
                return await self._stream_create(**create_kwargs)

            response = self.client.chat.completions.create(**create_kwargs)
            return self._parse_response(response)

        except Exception as e:
            # GLM-5 失败时自动 fallback 到 glm-4-air
            if model != "glm-4-air":
                print(f"⚠️ GLM-5 调用失败: {e}，回退到 glm-4-air")
                return await self.create(messages, model="glm-4-air", thinking=False, tools=None, **kwargs)
            print(f"❌ GLM调用失败: {e}")
            return self._mock_completion(messages)

    def _format_messages(self, messages: List[Any]) -> List[Dict]:
        """将各种消息格式统一为 dict 列表"""
        formatted = []
        for msg in messages:
            if isinstance(msg, dict):
                if msg.get("content", "").strip():
                    formatted.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "").strip(),
                    })
            elif hasattr(msg, "role") and hasattr(msg, "content"):
                content = getattr(msg, "content", "")
                if content and str(content).strip():
                    formatted.append({"role": msg.role, "content": str(content).strip()})
        return formatted

    def _parse_response(self, response) -> Dict:
        """解析 GLM API 响应，提取 content / tool_calls / reasoning_content"""
        choice = response.choices[0]
        message = choice.message

        result = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": getattr(message, "content", None),
                }
            }]
        }

        # 解析 thinking 内容
        reasoning = getattr(message, "reasoning_content", None)
        if reasoning:
            result["choices"][0]["message"]["reasoning_content"] = reasoning

        # 解析 tool_calls
        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            result["choices"][0]["message"]["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in tool_calls
            ]

        return result

    async def _stream_create(self, **kwargs) -> Dict:
        """流式输出（SSE），收集完整响应后返回"""
        import asyncio
        full_content = ""
        reasoning_content = ""
        tool_calls_list = []

        response = self.client.chat.completions.create(**kwargs, stream=True)
        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                full_content += delta.content
            if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                reasoning_content += delta.reasoning_content
            if hasattr(delta, "tool_calls") and delta.tool_calls:
                for tc in delta.tool_calls:
                    # 流式 tool_calls 需要拼接
                    if tc.index >= len(tool_calls_list):
                        tool_calls_list.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                    entry = tool_calls_list[tc.index]
                    if tc.id:
                        entry["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            entry["function"]["name"] += tc.function.name
                        if tc.function.arguments:
                            entry["function"]["arguments"] += tc.function.arguments

        msg = {"role": "assistant", "content": full_content or None}
        if reasoning_content:
            msg["reasoning_content"] = reasoning_content
        if tool_calls_list:
            msg["tool_calls"] = tool_calls_list

        return {"choices": [{"message": msg}]}
    
    def _mock_completion(self, messages: List[Any]) -> Dict:
        """模拟完成"""
        # 获取最后一条用户消息
        user_message = ""
        for msg in reversed(messages):
            if hasattr(msg, 'content'):
                user_message = msg.content
                break
            elif isinstance(msg, dict) and msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        # 根据消息内容生成响应
        if "FastAPI" in user_message or "fastapi" in user_message.lower():
            response = "基于FastAPI的现代Python Web应用已生成"
        elif "Express" in user_message or "express" in user_message.lower():
            response = "基于Express.js的Node.js Web应用已生成"
        elif "Spring" in user_message or "spring" in user_message.lower():
            response = "基于Spring Boot的Java Web应用已生成"
        elif "Gin" in user_message or "gin" in user_message.lower():
            response = "基于Gin的Go Web应用已生成"
        else:
            response = f"🤖 收到消息: {user_message[:100]}..."
        
        return {
            "choices": [{
                "message": {
                    "content": response
                }
            }]
        }

class GitHubManager:
    """GitHub项目管理器"""
    
    def __init__(self, token: str = None, username: str = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.username = username or os.getenv("GITHUB_USERNAME")
        if not self.token:
            print("⚠️ 未配置GITHUB_TOKEN")
            self.github = None
        else:
            try:
                self.github = Github(self.token, timeout=30, retry=3)
                # 获取当前用户信息
                if not self.username:
                    try:
                        user = self.github.get_user()
                        self.username = user.login
                        print(f"✅ GitHub客户端初始化成功，用户: {self.username}")
                    except Exception as e:
                        print(f"⚠️ 无法获取GitHub用户信息: {e}")
                        self.username = None
                else:
                    print(f"✅ GitHub客户端初始化成功，用户: {self.username}")
            except Exception as e:
                print(f"❌ GitHub客户端初始化失败: {e}")
                self.github = None
    
    def create_repository(self, name: str, description: str = "", private: bool = False) -> Optional[str]:
        """创建GitHub仓库"""
        if not self.github:
            print("❌ GitHub客户端未初始化")
            return None
        
        try:
            import re
            import time
            
            # 清理仓库名称
            clean_name = re.sub(r'[^a-zA-Z0-9_-]', '-', name.lower())
            clean_name = re.sub(r'-+', '-', clean_name).strip('-')
            
            # 添加时间戳避免重名
            timestamp = int(time.time())
            clean_name = f"{clean_name}-{timestamp}"
            
            print(f"🔄 正在创建仓库: {clean_name}")
            
            # 创建仓库
            repo = self.github.get_user().create_repo(
                name=clean_name,
                description=description,
                private=private,
                auto_init=False
            )
            print(f"✅ 仓库创建成功: {repo.html_url}")
            return repo.html_url
        except Exception as e:
            print(f"❌ 创建仓库失败: {e}")
            return None
    
    def push_code(self, repo_url: str, local_path: str, max_retries: int = 3) -> bool:
        """推送代码到GitHub"""
        import time
        
        try:
            print(f"🔄 正在推送代码到: {repo_url}")
            
            # 检查GitHub Token
            if not self.token:
                print("❌ 未配置GITHUB_TOKEN，无法推送代码")
                return False
            
            # 初始化git仓库
            subprocess.run(["git", "init"], cwd=local_path, check=True)
            
            # 配置git用户信息
            subprocess.run(["git", "config", "user.name", "AI Agent"], cwd=local_path, check=True)
            subprocess.run(["git", "config", "user.email", "ai-agent@example.com"], cwd=local_path, check=True)
            
            # 使用HTTPS模式
            repo_path = repo_url.replace("https://github.com/", "")
            https_url = f"https://{self.token}@github.com/{repo_path}"
            
            # 添加远程仓库
            subprocess.run(["git", "remote", "add", "origin", https_url], cwd=local_path, check=True)
            
            # 添加所有文件
            subprocess.run(["git", "add", "."], cwd=local_path, check=True)
            
            # 提交
            subprocess.run(["git", "commit", "-m", "Initial commit by AI Agent"], cwd=local_path, check=True)
            
            # 推送到GitHub
            result = subprocess.run(["git", "push", "-u", "origin", "main"], cwd=local_path, 
                                  capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"✅ 代码推送成功: {repo_url}")
                return True
            else:
                print(f"❌ 推送失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 推送代码失败: {e}")
            return False

class EnhancedDynamicAutoGenSystem:
    """增强的动态AutoGen系统"""
    
    def __init__(self, api_key: str = None, github_token: str = None, github_username: str = None, interactive_mode: bool = True, use_coding_plan: bool = True):
        self.api_key = api_key or os.getenv("ZHIPU_API_KEY")
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.github_username = github_username or os.getenv("GITHUB_USERNAME")
        self.interactive_mode = interactive_mode
        self.use_coding_plan = use_coding_plan  # 是否使用 GLM-5 Coding Plan 模式

        # 初始化LLM客户端
        self.llm_client = RealLLMClient(self.api_key)
        
        # 初始化GitHub管理器
        self.github_manager = GitHubManager(self.github_token, self.github_username)
        
        # 初始化基础模块
        self.requirement_parser = FlexibleRequirementParser(self.llm_client)
        # self.template_manager = ProjectTemplateManager()
        self.user_interaction = UserInteractionManager(interactive_mode)
        self.quality_checker = CodeQualityChecker()
        self.config_manager = ConfigurationManager()
        self.extension_manager = ExtensionManager()
        
        # 初始化增强模块
        self.advanced_code_generator = AdvancedCodeGenerator(self.llm_client)
        self.enhanced_agent_manager = EnhancedDynamicAgentManager(self.llm_client)
        
        # 初始化 GLM Coding Plan 引擎
        self.glm_coding_plan = GLMCodingPlan(self.llm_client, project_path="")

        # 初始化执行反馈循环
        self.execution_sandbox = ExecutionSandbox(timeout=30)
        self.iteration_loop = IterationLoop(
            sandbox=self.execution_sandbox,
            llm_client=self.llm_client,
            max_rounds=3,
            timeout=30,
        )

        # 初始化质量闭环
        self.quality_loop = QualityLoop(timeout=60)
        self.auto_fixer = AutoFixer(llm_client=self.llm_client, quality_loop=self.quality_loop)
        
        # 工作目录
        self.work_directory = None
        
        print(f"✅ 增强动态AutoGen系统初始化完成 (coding_plan={'启用' if use_coding_plan else '禁用'})")
    
    async def generate_complex_project(self, user_input: str) -> Dict[str, Any]:
        """生成复杂项目的主入口"""
        print("🚀 增强动态AutoGen系统启动")
        print("=" * 60)
        print(f"📝 用户需求: {user_input}")
        print()
        
        try:
            # 1. 解析用户需求
            print("🔍 步骤1: 解析用户需求...")
            requirements = await self.requirement_parser.parse_requirement(user_input)
            # 支持灵活的技术栈
            tech_stack_name = getattr(requirements.tech_stack, 'value', requirements.tech_stack.name)
            print(f"✅ 需求解析完成: {requirements.project_name} ({tech_stack_name})")
            
            # 2. 用户交互确认
            print("\n🤔 步骤2: 用户交互确认...")
            user_confirmations = await self.user_interaction.get_user_confirmations(requirements)
            print("✅ 用户确认完成")
            
            # 更新requirements对象
            if user_confirmations.get('tech_stack'):
                requirements.tech_stack = user_confirmations['tech_stack']
            if user_confirmations.get('project_name'):
                requirements.project_name = user_confirmations['project_name']
            if user_confirmations.get('database'):
                requirements.database_required = user_confirmations['database']
            if user_confirmations.get('authentication'):
                requirements.authentication_required = user_confirmations['authentication']
            if user_confirmations.get('deployment'):
                requirements.deployment_type = user_confirmations['deployment']
            
            # 支持灵活的技术栈
            tech_stack_name = getattr(requirements.tech_stack, 'value', requirements.tech_stack.name)
            print(f"✅ 需求更新完成: {requirements.project_name} ({tech_stack_name})")
            
            # 3. 创建项目目录
            self.work_directory = tempfile.mkdtemp(prefix="enhanced_ai_project_", dir="/tmp")
            project_path = os.path.join(self.work_directory, requirements.project_name)

            # ── 分支：GLM-5 Coding Plan 模式 vs 旧模式 ──
            if self.use_coding_plan and not self.llm_client.use_mock:
                print("\n🧠 步骤3: GLM-5 Coding Plan 模式...")
                self.glm_coding_plan.project_path = project_path
                plan = await self.glm_coding_plan.create_plan(user_input)
                print(f"✅ 规划完成: {len(plan.tasks)} 个任务")

                print("\n💻 步骤4: 执行编码计划...")
                plan_result = await self.glm_coding_plan.execute_plan(plan)
                print(f"✅ 执行完成: {plan_result.success}, {len(plan_result.files_written)} 个文件")

                print("\n🔍 步骤5: 审查并修复...")
                fix_result = await self.glm_coding_plan.review_and_fix(plan_result)
                if fix_result.issues_found > 0:
                    print(f"⚠️ 发现 {fix_result.issues_found} 个问题，已修复 {fix_result.issues_fixed} 个")
                else:
                    print("✅ 审查通过，无需修复")

                # 构造兼容的 code_result
                from src.generators.advanced_code_generator import GeneratedFile
                code_result_files = []
                run_commands = []
                for fp, content in plan_result.files_written.items():
                    rel = os.path.relpath(fp, project_path)
                    code_result_files.append(GeneratedFile(path=rel, content=content, is_executable=False))
                    if 'main' in rel.lower() or 'app' in rel.lower():
                        ext = rel.rsplit('.', 1)[-1] if '.' in rel else ''
                        if ext == 'py':
                            run_commands.append(f"python {rel}")
                        elif ext == 'js':
                            run_commands.append(f"node {rel}")
                        elif ext == 'go':
                            run_commands.append("go run .")

                class _CodeResult:
                    pass
                code_result = _CodeResult()
                code_result.files = code_result_files
                code_result.run_commands = run_commands

                # 写入文件（coding plan 可能已经写了，这里确保目录存在）
                os.makedirs(project_path, exist_ok=True)
                for f in code_result.files:
                    fpath = os.path.join(project_path, f.path)
                    os.makedirs(os.path.dirname(fpath), exist_ok=True)
                    with open(fpath, 'w', encoding='utf-8') as fw:
                        fw.write(f.content)
            else:
                # 旧流程
                print("\n🤖 步骤3: 创建增强Agent...")
                enhanced_agents = await self.enhanced_agent_manager.create_enhanced_agents(requirements)
                print(f"✅ 创建了 {len(enhanced_agents)} 个增强Agent")

                print("\n💻 步骤4: 高级代码生成...")
                code_result = await self.advanced_code_generator.generate_complex_project(requirements, project_path=project_path)
                if not code_result.files:
                    return {"status": "failed", "error": "高级代码生成失败"}
                print("✅ 高级代码生成完成")

            # 5. 生成配置文件
            print("\n⚙️ 步骤5: 生成配置文件...")
            config_files = self.config_manager.generate_configurations(requirements, user_confirmations)
            print(f"✅ 生成了 {len(config_files)} 个配置文件")
            
            # 6. 创建项目目录
            print("\n📁 步骤6: 创建项目目录...")
            # work_directory 已在步骤4创建
            print(f"✅ 项目目录: {project_path}")
            
            # 7. 写入文件
            print("\n📝 步骤7: 写入项目文件...")
            self._write_enhanced_project_files(project_path, code_result.files, config_files)
            print("✅ 文件写入完成")
            
            # 7.5 执行反馈循环（在质量检查之前）
            iteration_outcome = None
            entry_command = self._get_entry_command(requirements, code_result)
            if entry_command:
                print("\n🔄 步骤7.5: 执行反馈循环...")
                generated_file_paths = [f.path for f in code_result.files]
                iteration_outcome = await self.iteration_loop.run(
                    entry_command=entry_command,
                    project_path=project_path,
                    generated_files=generated_file_paths,
                )
                if iteration_outcome.success:
                    print(f"✅ 执行反馈循环成功，共 {iteration_outcome.total_rounds} 轮")
                else:
                    print(f"⚠️ 执行反馈循环未能完全修复，共 {iteration_outcome.total_rounds} 轮")
            else:
                print("\n⏭️ 步骤7.5: 无法确定入口命令，跳过执行反馈循环")
            
            # 8. 质量闭环（linter + 类型检查 + 测试 + 自动修复）
            print("\n🔍 步骤8: 质量闭环检查...")
            tech_name = getattr(requirements.tech_stack, 'value', '')
            if not tech_name and hasattr(requirements.tech_stack, 'name'):
                tech_name = requirements.tech_stack.name
            quality_report = await self.auto_fixer.fix(
                project_path=project_path,
                tech_stack=tech_name,
            )
            print(quality_report.summary())
            
            # 9. GitHub推送
            repo_url = None
            if self.github_manager.github:
                print("\n🐙 步骤9: 推送到GitHub...")
                try:
                    repo_url = self.github_manager.create_repository(
                        name=requirements.project_name,
                        description=f"AI Agent生成的{getattr(requirements.tech_stack, 'value', requirements.tech_stack.name)}项目"
                    )
                    
                    if repo_url:
                        push_success = self.github_manager.push_code(repo_url, project_path, max_retries=3)
                        if push_success:
                            print(f"✅ 项目已推送到GitHub: {repo_url}")
                        else:
                            print("❌ 代码推送失败，但项目已生成到本地")
                            print(f"📁 本地项目路径: {project_path}")
                    else:
                        print("❌ 仓库创建失败，但项目已生成到本地")
                        print(f"📁 本地项目路径: {project_path}")
                except Exception as e:
                    print(f"⚠️ GitHub推送异常: {e}")
                    print("📁 项目已生成到本地，可以手动推送到GitHub")
                    print(f"📁 本地项目路径: {project_path}")
            else:
                print("\n⚠️ 步骤10: GitHub未配置，跳过推送")
                print("💡 提示: 可以设置GITHUB_TOKEN环境变量来启用自动推送")
            
            print("\n🎉 增强项目生成完成！")
            print("=" * 60)
            
            # 显示对话摘要
            conversation_summary = self.enhanced_agent_manager.get_conversation_summary()
            print(f"\n{conversation_summary}")
            
            return {
                "status": "completed",
                "project_name": requirements.project_name,
                "tech_stack": getattr(requirements.tech_stack, 'value', requirements.tech_stack.name),
                "project_path": project_path,
                "github_url": repo_url,
                "quality_score": quality_report.overall_score,
                "agent_results": 0,  # 已删除增强Agent工作流
                "files_generated": len(code_result.files) + len(config_files),
                "work_directory": self.work_directory,
                "conversation_rounds": len(self.enhanced_agent_manager.conversation_history),
                "message": "项目已通过增强动态AutoGen系统完成生成"
            }
            
        except Exception as e:
            print(f"❌ 增强项目生成失败: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _write_enhanced_project_files(self, project_path: str, code_files: List[Any], config_files: List[Any]):
        """写入增强项目文件"""
        # 写入代码文件
        for file in code_files:
            file_path = os.path.join(project_path, file.path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file.content)
            
            # 设置执行权限
            if file.is_executable:
                os.chmod(file_path, 0o755)
        
        # 写入配置文件
        for file in config_files:
            file_path = os.path.join(project_path, file.path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file.content)
    
    def _get_entry_command(self, requirements, code_result) -> Optional[str]:
        """根据技术栈和生成结果推断入口执行命令"""
        # 从 code_result.run_commands 获取
        if hasattr(code_result, 'run_commands') and code_result.run_commands:
            return code_result.run_commands[0]
        
        # 根据技术栈推断
        tech_name = ""
        if hasattr(requirements.tech_stack, 'value'):
            tech_name = requirements.tech_stack.value.lower()
        elif hasattr(requirements.tech_stack, 'name'):
            tech_name = requirements.tech_stack.name.lower()
        elif hasattr(requirements.tech_stack, 'language'):
            tech_name = requirements.tech_stack.language.lower()
        
        # 从生成文件中找入口
        file_paths = [f.path for f in code_result.files]
        
        if 'python' in tech_name or tech_name == '':
            for p in file_paths:
                if 'main.py' in p or p.endswith('app.py'):
                    return f"python {p}"
        elif 'node' in tech_name or 'javascript' in tech_name:
            for p in file_paths:
                if 'app.js' in p or 'index.js' in p:
                    return f"node {p}"
        elif 'go' in tech_name:
            for p in file_paths:
                if 'main.go' in p:
                    return "go run ."
        
        # 默认尝试找 main 文件
        for p in file_paths:
            basename = os.path.basename(p)
            if basename.startswith('main.'):
                ext = basename.split('.')[-1]
                if ext == 'py':
                    return f"python {p}"
                elif ext == 'js':
                    return f"node {p}"
                elif ext == 'go':
                    return "go run ."
        
        return None
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            "system_name": "增强动态AutoGen系统",
            "version": "3.0.0",
            "features": [
                "多轮对话代码生成",
                "Planner Agent项目规划",
                "Coder Agent代码生成",
                "增强Agent协作",
                "复杂需求支持",
                "智能架构设计",
                "性能优化建议",
                "代码质量审查"
            ],
            "supported_tech_stacks": [
                "Python FastAPI",
                "Python Flask", 
                "Node.js Express",
                "Java Spring Boot",
                "Go Gin"
            ],
            "llm_provider": "GLM-5" if not self.llm_client.use_mock else "Mock",
            "github_available": self.github_manager.github is not None,
            "interactive_mode": self.interactive_mode,
            "enhanced_agents": len(self.enhanced_agent_manager.agent_configs),
            "multi_round_support": True
        }
    
    def cleanup(self):
        """清理工作目录"""
        if self.work_directory and os.path.exists(self.work_directory):
            try:
                shutil.rmtree(self.work_directory)
                print(f"✅ 清理工作目录: {self.work_directory}")
            except Exception as e:
                print(f"⚠️ 清理工作目录失败: {e}")

def main():
    """主函数"""
    print("🚀 增强动态AutoGen系统 - 多轮对话代码生成")
    print("=" * 60)
    
    try:
        # 初始化系统
        system = EnhancedDynamicAutoGenSystem(interactive_mode=True)
        
        # 显示系统信息
        info = system.get_system_info()
        print(f"🏗️ 系统: {info['system_name']} v{info['version']}")
        print(f"🧠 LLM提供商: {info['llm_provider']}")
        print(f"🐙 GitHub可用: {info['github_available']}")
        print(f"🤖 交互模式: {info['interactive_mode']}")
        print(f"🔧 支持的技术栈: {', '.join(info['supported_tech_stacks'])}")
        print(f"⚡ 功能特性: {', '.join(info['features'])}")
        print(f"🤖 增强Agent: {info['enhanced_agents']} 个")
        print(f"💬 多轮对话: {'支持' if info['multi_round_support'] else '不支持'}")
        print()
        
        # 获取用户输入
        print("请输入您的复杂项目需求（支持自然语言描述）：")
        user_input = input("> ").strip()
        
        if not user_input:
            print("❌ 请输入有效的项目需求")
            return
        
        # 生成项目
        result = asyncio.run(system.generate_complex_project(user_input))
        
        if result["status"] == "completed":
            print("\n🎉 增强项目生成成功！")
            print(f"📁 项目目录: {result['project_path']}")
            print(f"🔧 技术栈: {result['tech_stack']}")
            print(f"📊 质量评分: {result['quality_score']:.1f}/100")
            print(f"🤖 Agent任务: {result['agent_results']}个")
            print(f"📝 生成文件: {result['files_generated']}个")
            print(f"💬 对话轮次: {result['conversation_rounds']}轮")
            if result.get('github_url'):
                print(f"🐙 GitHub链接: {result['github_url']}")
            print(f"📋 结果: {result.get('message', '项目完成')}")
        else:
            print("❌ 增强项目生成失败")
            print(f"错误: {result.get('error', '未知错误')}")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"❌ 系统错误: {e}")
    finally:
        # 清理资源
        if 'system' in locals():
            system.cleanup()

if __name__ == "__main__":
    main()
