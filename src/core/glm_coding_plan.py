"""
GLM-5 Coding Plan 引擎

利用 GLM-5 的 thinking + function calling 实现类似 Claude Code 的编码规划能力。
工作流：
  1. create_plan  — thinking 模式深度分析需求，输出结构化编码计划
  2. execute_plan — function calling 模式，让模型自主选择工具完成编码
  3. review_and_fix — thinking 模式审查结果，发现问题自动修复
"""
import os
import json
import uuid
import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from src.core.agent_tools import (
    GLM5_TOOL_DEFINITIONS,
    TOOL_REGISTRY,
    call_tool,
    ToolResult,
)


# ─── 数据结构 ───────────────────────────────────────────────────────────────

@dataclass
class PlanTask:
    """单个编码任务"""
    task_id: str
    description: str
    files: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    priority: int = 0
    status: str = "pending"  # pending / in_progress / completed


@dataclass
class CodingPlan:
    """编码计划"""
    plan_id: str
    requirement: str
    thinking_process: str = ""
    tasks: List[PlanTask] = field(default_factory=list)
    file_structure: Dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class PlanResult:
    """执行结果"""
    success: bool
    plan_id: str
    files_written: Dict[str, str] = field(default_factory=dict)  # path -> content
    tool_calls_count: int = 0
    errors: List[str] = field(default_factory=list)


@dataclass
class FixResult:
    """修复结果"""
    issues_found: int = 0
    issues_fixed: int = 0
    details: str = ""


# ─── 规划 Prompt ────────────────────────────────────────────────────────────

_PLAN_SYSTEM_PROMPT = """你是一个资深软件架构师。用户会给你一个项目需求，请深度思考并输出一个结构化的编码计划。

## 输出格式（严格 JSON）

```json
{
  "file_structure": {
    "文件相对路径": "文件用途说明"
  },
  "tasks": [
    {
      "task_id": "T1",
      "description": "任务描述",
      "files": ["涉及文件路径"],
      "depends_on": [],
      "priority": 1
    }
  ],
  "dependencies": ["项目外部依赖"]
}
```

## 要求
- 任务按优先级排序（数字越小越先执行）
- 依赖关系要清晰（depends_on 引用其他 task_id）
- 文件结构要完整，包含所有需要创建的文件
- 只输出 JSON，不要输出其他内容"""


_REVIEW_SYSTEM_PROMPT = """你是一个代码审查专家。请审查以下编码执行结果，检查：
1. 代码逻辑是否正确
2. 文件是否完整
3. 是否有明显 bug
4. 是否遗漏了需求中的功能

## 输出格式（严格 JSON）

```json
{
  "issues_found": 0,
  "issues": [
    {
      "file": "文件路径",
      "description": "问题描述",
      "fix": "修复建议"
    }
  ]
}
```

如果没有问题，issues_found 为 0，issues 为空数组。只输出 JSON。"""


# ─── Coding Plan 引擎 ───────────────────────────────────────────────────────

class GLMCodingPlan:
    """GLM-5 Coding Plan 引擎"""

    def __init__(self, llm_client, project_path: str = ""):
        """
        Args:
            llm_client: RealLLMClient 实例
            project_path: 项目根目录
        """
        self.llm_client = llm_client
        self.project_path = project_path
        self.plan_history: List[CodingPlan] = []

    async def create_plan(self, requirement: str) -> CodingPlan:
        """
        创建编码计划：用 thinking 模式让 GLM-5 深度分析需求。

        Returns:
            CodingPlan 结构化编码计划
        """
        plan_id = str(uuid.uuid4())[:8]

        response = await self.llm_client.create(
            messages=[
                {"role": "system", "content": _PLAN_SYSTEM_PROMPT},
                {"role": "user", "content": f"项目需求：{requirement}"},
            ],
            model="glm-5",
            thinking=True,
            temperature=1.0,
            max_tokens=8192,
        )

        # 提取 thinking 和 content
        choice = response["choices"][0]["message"]
        thinking_process = choice.get("reasoning_content", "")
        content = choice.get("content", "")

        # 解析 JSON 计划
        plan_data = self._extract_json(content)

        tasks = []
        for t in plan_data.get("tasks", []):
            tasks.append(PlanTask(
                task_id=t.get("task_id", str(uuid.uuid4())[:6]),
                description=t.get("description", ""),
                files=t.get("files", []),
                depends_on=t.get("depends_on", []),
                priority=t.get("priority", 99),
                status="pending",
            ))
        tasks.sort(key=lambda x: x.priority)

        plan = CodingPlan(
            plan_id=plan_id,
            requirement=requirement,
            thinking_process=thinking_process,
            tasks=tasks,
            file_structure=plan_data.get("file_structure", {}),
            dependencies=plan_data.get("dependencies", []),
        )
        self.plan_history.append(plan)
        return plan

    async def execute_plan(self, plan: CodingPlan) -> PlanResult:
        """
        执行编码计划：用 function calling 让 GLM-5 自主选择工具完成编码。

        对每个任务：
        1. 构建 prompt 包含任务描述和上下文
        2. GLM-5 通过 tool_calls 调用工具（read_file, write_file, execute 等）
        3. 执行工具，结果作为 role=tool 消息喂回
        4. 循环直到模型不再调用工具
        """
        result = PlanResult(success=True, plan_id=plan.plan_id)
        all_files: Dict[str, str] = {}  # path -> content

        # 按优先级执行任务
        for task in plan.tasks:
            task.status = "in_progress"
            print(f"  📋 执行任务 {task.task_id}: {task.description[:60]}")

            # 构建任务上下文
            context = self._build_task_context(plan, task, all_files)
            messages = [
                {"role": "system", "content": "你是一个智能编码助手，请使用工具完成以下编码任务。"},
                {"role": "user", "content": context},
            ]

            # 工具调用循环
            max_rounds = 15
            for round_i in range(max_rounds):
                response = await self.llm_client.create(
                    messages=messages,
                    model="glm-5",
                    tools=GLM5_TOOL_DEFINITIONS,
                    tool_choice="auto",
                    max_tokens=8192,
                )

                choice = response["choices"][0]["message"]
                tool_calls = choice.get("tool_calls", [])

                if not tool_calls:
                    # 没有工具调用，任务完成
                    break

                # 将 assistant 消息加入历史
                messages.append(choice)

                # 执行每个 tool_call
                for tc in tool_calls:
                    fn_name = tc["function"]["name"]
                    try:
                        fn_args = json.loads(tc["function"]["arguments"])
                    except json.JSONDecodeError:
                        fn_args = {}

                    print(f"    🔧 {fn_name}({json.dumps(fn_args, ensure_ascii=False)[:80]})")
                    tool_result = call_tool(fn_name, fn_args, self.project_path)
                    result.tool_calls_count += 1

                    status_icon = "✅" if tool_result.success else "❌"
                    print(f"    {status_icon} {tool_result.output[:100]}")

                    # 记录写入的文件
                    if fn_name == "write_file" and tool_result.success:
                        path = fn_args.get("path", "")
                        content = fn_args.get("content", "")
                        abs_path = path if os.path.isabs(path) else os.path.join(self.project_path, path)
                        all_files[abs_path] = content

                    # 构造 role=tool 消息喂回
                    tool_msg_content = json.dumps({
                        "success": tool_result.success,
                        "output": tool_result.output[:3000],
                        "error": tool_result.error,
                    }, ensure_ascii=False)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": tool_msg_content,
                    })

            task.status = "completed"

        result.files_written = all_files
        if not all_files:
            result.success = False
            result.errors.append("未生成任何文件")
        return result

    async def review_and_fix(self, execution_result: PlanResult) -> FixResult:
        """
        审查执行结果：用 thinking 模式审查，发现问题时通过 function calling 修复。
        """
        # 收集生成的文件内容摘要
        files_summary = []
        for path, content in execution_result.files_written.items():
            files_summary.append(f"### {path}\n```\n{content[:1500]}\n```")

        files_text = "\n\n".join(files_summary) if files_summary else "（无文件生成）"

        response = await self.llm_client.create(
            messages=[
                {"role": "system", "content": _REVIEW_SYSTEM_PROMPT},
                {"role": "user", "content": f"请审查以下编码执行结果：\n\n{files_text}"},
            ],
            model="glm-5",
            thinking=True,
            temperature=1.0,
            max_tokens=8192,
        )

        choice = response["choices"][0]["message"]
        content = choice.get("content", "")
        review_data = self._extract_json(content)

        issues = review_data.get("issues", [])
        issues_found = review_data.get("issues_found", len(issues))
        issues_fixed = 0

        # 自动修复发现的问题
        if issues:
            fix_context = "请修复以下问题：\n"
            for issue in issues:
                fix_context += f"- 文件 {issue.get('file', '?')}: {issue.get('description', '?')}\n"
                fix_context += f"  修复建议: {issue.get('fix', '?')}\n"

            fix_response = await self.llm_client.create(
                messages=[
                    {"role": "system", "content": "你是一个编码助手，请使用工具修复以下问题。"},
                    {"role": "user", "content": fix_context},
                ],
                model="glm-5",
                tools=GLM5_TOOL_DEFINITIONS,
                tool_choice="auto",
                max_tokens=8192,
            )

            fix_choice = fix_response["choices"][0]["message"]
            fix_tool_calls = fix_choice.get("tool_calls", [])

            if fix_tool_calls:
                # 执行修复的工具调用
                messages = [fix_choice]
                for tc in fix_tool_calls:
                    fn_name = tc["function"]["name"]
                    try:
                        fn_args = json.loads(tc["function"]["arguments"])
                    except json.JSONDecodeError:
                        fn_args = {}

                    tool_result = call_tool(fn_name, fn_args, self.project_path)
                    if tool_result.success:
                        issues_fixed += 1
                        if fn_name == "write_file":
                            path = fn_args.get("path", "")
                            abs_path = path if os.path.isabs(path) else os.path.join(self.project_path, path)
                            execution_result.files_written[abs_path] = fn_args.get("content", "")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps({"success": tool_result.success, "output": tool_result.output[:2000]}, ensure_ascii=False),
                    })

        return FixResult(
            issues_found=issues_found,
            issues_fixed=issues_fixed,
            details=content[:500],
        )

    def _build_task_context(self, plan: CodingPlan, task: PlanTask, existing_files: Dict) -> str:
        """构建单个任务的上下文 prompt"""
        ctx_parts = [
            f"## 项目需求\n{plan.requirement}",
            f"\n## 当前任务\n{task.description}",
            f"\n## 需要操作的文件\n" + "\n".join(f"- {f}" for f in task.files) if task.files else "",
            f"\n## 项目文件结构\n" + "\n".join(f"- {p}: {desc}" for p, desc in plan.file_structure.items()) if plan.file_structure else "",
            f"\n## 外部依赖\n" + ", ".join(plan.dependencies) if plan.dependencies else "",
        ]

        if existing_files:
            ctx_parts.append("\n## 已生成的文件\n" + "\n".join(f"- {p}" for p in existing_files.keys()))

        ctx_parts.append("\n请使用工具完成当前任务。先 read_file 查看已有内容（如果有），再 write_file 创建/修改文件。")
        return "\n".join(p for p in ctx_parts if p)

    def _extract_json(self, text: str) -> Dict:
        """从文本中提取 JSON（支持 ```json 块包裹）"""
        # 尝试提取 ```json ... ``` 块
        import re
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试直接解析整个文本
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试找到第一个 { 和最后一个 }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

        return {}
