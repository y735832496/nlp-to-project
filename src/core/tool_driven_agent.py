"""
工具驱动的 Agent
核心循环：LLM → 选择工具+参数 → 执行工具 → 结果喂回 LLM → 继续
支持 GLM-4 function calling（如果可用），否则用 prompt 模拟
"""
import os
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.core.agent_tools import TOOL_DEFINITIONS, call_tool, ToolResult
from src.core.context_manager import ContextManager
from dataclasses import dataclass, field


@dataclass
class ToolCallRecord:
    """单次工具调用记录"""
    tool_name: str
    arguments: Dict[str, Any]
    result: ToolResult
    timestamp: str

from dataclasses import dataclass, field


class ToolDrivenAgent:
    """
    工具驱动 Agent：让 LLM 自己决定用什么工具、生成什么文件、按什么顺序。

    工作流程：
    1. 给 LLM 一个任务描述 + 可用工具列表
    2. LLM 返回要调用的工具和参数
    3. 执行工具，把结果喂回 LLM
    4. 重复直到 LLM 认为任务完成
    """

    def __init__(
        self,
        llm_client=None,
        max_iterations: int = 20,
        project_root: str = "",
    ):
        """
        Args:
            llm_client: LLM 客户端（需要有 create 方法）
            max_iterations: 最大工具调用轮数
            project_root: 项目根目录
        """
        self.llm_client = llm_client
        self.max_iterations = max_iterations
        self.project_root = project_root
        self.conversation_history: List[Dict[str, str]] = []
        self.tool_records: List[ToolCallRecord] = []
        self.context_manager = ContextManager(max_context_tokens=6000)

        # 检测是否支持 function calling
        self.supports_tools = False
        if llm_client and hasattr(llm_client, "model_info"):
            self.supports_tools = llm_client.model_info.get("supports_tools", False)

    async def run(self, task_description: str) -> Dict[str, Any]:
        """
        执行一个任务。

        Args:
            task_description: 任务描述

        Returns:
            包含结果和历史的 dict
        """
        # 初始化对话
        system_prompt = self._build_system_prompt()
        self.conversation_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_description},
        ]
        self.tool_records = []

        for i in range(self.max_iterations):
            print(f"\n🔁 Agent 迭代 {i + 1}/{self.max_iterations}")

            # 检查上下文长度，超限时自动压缩
            self._maybe_compress_context()

            # 调用 LLM
            llm_response = await self._call_llm()
            if not llm_response:
                print("   ⚠️ LLM 未返回有效响应")
                break

            # 解析工具调用
            tool_call = self._parse_tool_call(llm_response)

            if tool_call is None:
                # LLM 没有调用工具，可能是最终回复
                print(f"   💬 LLM 回复: {llm_response[:200]}...")
                break

            tool_name, arguments = tool_call
            print(f"   🔧 调用工具: {tool_name}({json.dumps(arguments, ensure_ascii=False)[:100]})")

            # 读取文件时自动走摘要模式
            if tool_name == "read_file" and "path" in arguments:
                self._smart_read_arguments(arguments)

            # 执行工具
            result = call_tool(tool_name, arguments, self.project_root)
            now = datetime.now().isoformat()
            self.tool_records.append(ToolCallRecord(
                tool_name=tool_name,
                arguments=arguments,
                result=result,
                timestamp=now,
            ))

            status = "✅" if result.success else "❌"
            print(f"   {status} 工具结果: {result.output[:200]}...")

            # 把结果喂回 LLM
            tool_message = self._format_tool_result(tool_name, result)
            self.conversation_history.append({"role": "assistant", "content": llm_response})
            self.conversation_history.append({"role": "user", "content": tool_message})

        return {
            "iterations": len(self.tool_records),
            "tool_records": [
                {
                    "tool": r.tool_name,
                    "args": r.arguments,
                    "success": r.result.success,
                    "output": r.result.output[:500],
                }
                for r in self.tool_records
            ],
            "final_message": llm_response if 'llm_response' in dir() else "",
            "conversation_history": self.conversation_history,
        }

    def _build_system_prompt(self) -> str:
        """构建系统提示，包含工具说明"""
        tools_desc = []
        for t in TOOL_DEFINITIONS:
            params = ", ".join(
                f"{k}: {v.get('description', '')}"
                for k, v in t["parameters"].get("properties", {}).items()
            )
            tools_desc.append(f"- {t['name']}({params}): {t['description']}")

        return f"""你是一个智能编程助手，可以使用以下工具来完成任务：

{chr(10).join(tools_desc)}

## 使用方式

在回复中，当你需要使用工具时，请用以下格式：
<<<tool_call:{"{"}"name":"工具名","arguments":{"{"}"参数名":"参数值"{"}"}{"}"}>>>

你可以连续调用多个工具。当你认为任务完成时，直接给出最终回复，不要使用工具调用格式。

## 规则
1. 先用 list_files 了解项目结构
2. 用 read_file 查看现有文件内容
3. 用 write_file 创建或修改文件
4. 用 execute 运行和测试代码
5. 用 grep 搜索代码中的特定内容
6. 每次只调用一个工具，等结果后再决定下一步"""

    async def _call_llm(self) -> Optional[str]:
        """调用 LLM 并返回文本内容"""
        if not self.llm_client:
            return None

        try:
            # 尝试 function calling（如果支持）
            if self.supports_tools:
                return await self._call_llm_with_tools()

            # 否则用普通 prompt
            response = await self.llm_client.create(self.conversation_history)
            return response["choices"][0]["message"]["content"]

        except Exception as e:
            print(f"   ❌ LLM 调用失败: {e}")
            return None

    async def _call_llm_with_tools(self) -> Optional[str]:
        """使用 function calling 模式调用（GLM-4 兼容）"""
        try:
            # GLM-4 的 tools 参数
            response = await self.llm_client.create(
                self.conversation_history,
                tools=TOOL_DEFINITIONS,
            )
            return response["choices"][0]["message"]["content"]
        except Exception:
            # 如果 function calling 失败，回退到 prompt 模式
            self.supports_tools = False
            response = await self.llm_client.create(self.conversation_history)
            return response["choices"][0]["message"]["content"]

    def _parse_tool_call(self, text: str) -> Optional[tuple]:
        """
        从 LLM 回复中解析工具调用。
        格式: <<<tool_call:{"name":"xxx","arguments":{...}}}>>>
        """
        # 匹配自定义格式
        match = re.search(r'<<<tool_call:(\{.*?\})>>>', text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                return data.get("name"), data.get("arguments", {})
            except json.JSONDecodeError:
                pass

        # 尝试匹配 ```json 块中的工具调用
        match = re.search(r'```json\s*(\{.*?"name".*?\})\s*```', text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                if "name" in data:
                    return data["name"], data.get("arguments", {})
            except json.JSONDecodeError:
                pass

        return None

    def _format_tool_result(self, tool_name: str, result: ToolResult) -> str:
        """格式化工具结果，喂回给 LLM"""
        status = "成功" if result.success else "失败"
        msg = f"工具 {tool_name} 执行{status}。\n"
        if result.output:
            msg += f"输出:\n{result.output[:2000]}\n"
        if result.error:
            msg += f"错误:\n{result.error[:1000]}\n"
        msg += "\n请根据结果继续操作，或告诉我任务已完成。"
        return msg

    def _maybe_compress_context(self):
        """检查上下文长度，超限时自动压缩历史"""
        total_text = " ".join(m.get("content", "") for m in self.conversation_history)
        tokens = self.context_manager.estimate_tokens(total_text)
        if tokens > self.context_manager.max_context_tokens:
            print(f"   📦 上下文超限 ({tokens} tokens)，自动压缩...")
            self.conversation_history = self.context_manager.compress_context(
                self.conversation_history,
                max_tokens=self.context_manager.max_context_tokens - 1000,
            )

    def _smart_read_arguments(self, arguments: Dict[str, Any]):
        """大文件自动走摘要模式：在参数中标记需要摘要"""
        path = arguments.get("path", "")
        abs_path = os.path.join(self.project_root, path) if self.project_root else path
        if os.path.isfile(abs_path):
            try:
                line_count = sum(1 for _ in open(abs_path, "r", encoding="utf-8", errors="ignore"))
                if line_count > 200:
                    summary = self.context_manager.smart_read_file(abs_path, max_lines=200)
                    # 替换 read_file 参数为摘要内容，避免全量读取
                    arguments["_use_summary"] = True
                    arguments["_summary_content"] = f"[文件过大，已自动摘要]\n{summary}"
            except Exception:
                pass

    def get_summary(self) -> str:
        """获取执行摘要"""
        total = len(self.tool_records)
        success = sum(1 for r in self.tool_records if r.result.success)
        tools_used = {}
        for r in self.tool_records:
            tools_used[r.tool_name] = tools_used.get(r.tool_name, 0) + 1

        lines = [
            f"📊 Agent 执行摘要",
            f"总迭代: {total}",
            f"成功: {success} | 失败: {total - success}",
            f"工具使用: {json.dumps(tools_used, ensure_ascii=False)}",
        ]
        return "\n".join(lines)
