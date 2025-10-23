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
    """真实的LLM客户端"""
    
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
                print("✅ GLM-4-Air客户端初始化成功")
            except ImportError:
                print("❌ 请安装zhipuai: pip install zhipuai")
                self.use_mock = True
        
        # 添加model_info属性
        self.model_info = {
            "vision": False,
            "max_tokens": 4096,
            "supports_streaming": True,
            "supports_tools": False
        }
    
    async def create(self, messages: List[Any], model: str = "glm-4-air", **kwargs) -> Dict:
        """创建聊天完成"""
        if self.use_mock:
            return self._mock_completion(messages)
        
        try:
            # 转换消息格式
            formatted_messages = []
            for msg in messages:
                if hasattr(msg, 'role') and hasattr(msg, 'content'):
                    content = getattr(msg, 'content', '')
                    if content and content.strip():
                        formatted_messages.append({
                            "role": msg.role,
                            "content": content.strip()
                        })
                elif isinstance(msg, dict) and msg.get("content", "").strip():
                    formatted_messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "").strip()
                    })
            
            # 如果没有有效消息，使用默认消息
            if not formatted_messages:
                formatted_messages = [{"role": "user", "content": "请生成代码"}]
            
            response = self.client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                temperature=kwargs.get('temperature', 0.1)
            )
            return {
                "choices": [{
                    "message": {
                        "content": response.choices[0].message.content
                    }
                }]
            }
        except Exception as e:
            print(f"❌ GLM调用失败: {e}")
            return self._mock_completion(messages)
    
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
    
    def __init__(self, api_key: str = None, github_token: str = None, github_username: str = None, interactive_mode: bool = True):
        self.api_key = api_key or os.getenv("ZHIPU_API_KEY")
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.github_username = github_username or os.getenv("GITHUB_USERNAME")
        self.interactive_mode = interactive_mode
        
        # 初始化LLM客户端
        self.llm_client = RealLLMClient(self.api_key)
        
        # 初始化GitHub管理器
        self.github_manager = GitHubManager(self.github_token, self.github_username)
        
        # 初始化基础模块
        self.requirement_parser = FlexibleRequirementParser(self.llm_client)
        self.template_manager = ProjectTemplateManager()
        self.user_interaction = UserInteractionManager(interactive_mode)
        self.quality_checker = CodeQualityChecker()
        self.config_manager = ConfigurationManager()
        self.extension_manager = ExtensionManager()
        
        # 初始化增强模块
        self.advanced_code_generator = AdvancedCodeGenerator(self.llm_client)
        self.enhanced_agent_manager = EnhancedDynamicAgentManager(self.llm_client)
        
        # 工作目录
        self.work_directory = None
        
        print("✅ 增强动态AutoGen系统初始化完成")
    
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
            
            # 3. 创建增强Agent
            print("\n🤖 步骤3: 创建增强Agent...")
            enhanced_agents = await self.enhanced_agent_manager.create_enhanced_agents(requirements)
            print(f"✅ 创建了 {len(enhanced_agents)} 个增强Agent")
            
            # 4. 使用高级代码生成器生成项目代码
            print("\n💻 步骤4: 高级代码生成...")
            code_result = await self.advanced_code_generator.generate_complex_project(requirements)
            if not code_result.files:
                return {
                    "status": "failed",
                    "error": "高级代码生成失败"
                }
            print("✅ 高级代码生成完成")
            
            # 5. 生成配置文件
            print("\n⚙️ 步骤5: 生成配置文件...")
            config_files = self.config_manager.generate_configurations(requirements, user_confirmations)
            print(f"✅ 生成了 {len(config_files)} 个配置文件")
            
            # 6. 创建项目目录
            print("\n📁 步骤6: 创建项目目录...")
            self.work_directory = tempfile.mkdtemp(prefix="enhanced_ai_project_", dir="/tmp")
            project_path = os.path.join(self.work_directory, requirements.project_name)
            os.makedirs(project_path, exist_ok=True)
            print(f"✅ 项目目录: {project_path}")
            
            # 7. 写入文件
            print("\n📝 步骤7: 写入项目文件...")
            self._write_enhanced_project_files(project_path, code_result.files, config_files)
            print("✅ 文件写入完成")
            
            # 8. 代码质量检查
            print("\n🔍 步骤8: 代码质量检查...")
            quality_report = await self.quality_checker.check_project_quality(project_path, requirements.tech_stack, requirements)
            print(f"✅ 质量检查完成，评分: {quality_report.overall_score:.1f}/100")
            
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
            "llm_provider": "GLM-4-Air" if not self.llm_client.use_mock else "Mock",
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
