"""
迭代循环模块
核心执行-反馈循环：运行代码 → 如果失败 → 让 LLM 修复 → 重试
"""
import os
import traceback
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from src.core.execution_sandbox import ExecutionSandbox, ExecutionResult


@dataclass
class IterationRecord:
    """单轮迭代记录"""
    round_number: int
    execution_result: ExecutionResult
    fix_applied: Optional[str] = None  # LLM 返回的修复描述
    files_modified: List[str] = field(default_factory=list)


@dataclass
class IterationOutcome:
    """迭代循环的最终结果"""
    success: bool
    total_rounds: int
    best_result: ExecutionResult
    history: List[IterationRecord]
    message: str = ""


def build_error_context(stderr: str, project_path: str, generated_files: Optional[List[str]] = None) -> str:
    """
    根据执行错误和项目文件构建上下文，喂给 LLM 做修复。

    Args:
        stderr: 执行的错误输出
        project_path: 项目根目录
        generated_files: 生成的文件列表（相对路径）

    Returns:
        拼好的错误上下文字符串
    """
    parts = [f"## 执行错误输出\n```\n{stderr[:3000]}\n```"]

    if generated_files:
        parts.append("\n## 相关项目文件内容")
        for rel_path in generated_files[:10]:  # 最多读10个文件
            abs_path = os.path.join(project_path, rel_path)
            if os.path.isfile(abs_path):
                try:
                    content = open(abs_path, "r", encoding="utf-8", errors="ignore").read()
                    parts.append(f"\n### {rel_path}\n```\n{content[:2000]}\n```")
                except Exception:
                    pass

    return "\n".join(parts)


def build_fix_prompt(error_context: str, project_path: str) -> str:
    """构建让 LLM 修复代码的 prompt"""
    return f"""你是代码修复专家。以下项目在执行时报错了，请分析错误原因并修复。

项目路径: {project_path}

{error_context}

请以如下 JSON 格式返回修复方案（用 ```json ``` 包裹）：
```json
{{
  "analysis": "错误原因分析",
  "fixes": [
    {{
      "file": "需要修改的文件相对路径",
      "content": "修改后的完整文件内容"
    }}
  ]
}}
```

注意：
1. 只修改有问题的文件
2. 返回完整的文件内容，不要用 diff 格式
3. 如果是依赖缺失，在分析中说明"""


class IterationLoop:
    """
    执行反馈循环。
    流程：执行 → 检查结果 → 失败则 LLM 修复 → 重试 → 重复直到成功或达到上限。
    """

    def __init__(
        self,
        sandbox: Optional[ExecutionSandbox] = None,
        llm_client=None,
        max_rounds: int = 3,
        timeout: int = 30,
        enable_quality_check: bool = False,
    ):
        """
        Args:
            sandbox: 执行沙箱实例，默认新建一个
            llm_client: LLM 客户端（需要有 create 方法）
            max_rounds: 最大重试轮数
            timeout: 执行超时秒数
        """
        self.sandbox = sandbox or ExecutionSandbox(timeout=timeout)
        self.llm_client = llm_client
        self.max_rounds = max_rounds
        self.timeout = timeout
        self.enable_quality_check = enable_quality_check

    async def run(
        self,
        entry_command: str,
        project_path: str,
        generated_files: Optional[List[str]] = None,
    ) -> IterationOutcome:
        """
        执行迭代循环。

        Args:
            entry_command: 入口执行命令（如 "python src/main.py"）
            project_path: 项目根目录
            generated_files: 生成的文件列表（相对路径），用于构建错误上下文

        Returns:
            IterationOutcome 最终结果
        """
        history: List[IterationRecord] = []
        best_result: Optional[ExecutionResult] = None

        for round_num in range(1, self.max_rounds + 1):
            print(f"\n🔄 迭代轮次 {round_num}/{self.max_rounds}")

            # 执行
            result = self.sandbox.execute(
                command=entry_command,
                cwd=project_path,
                timeout=self.timeout,
            )

            print(f"   退出码={result.return_code}  耗时={result.duration_ms:.0f}ms  "
                  f"{'✅ 成功' if result.success else '❌ 失败'}")

            # 记录
            record = IterationRecord(round_number=round_num, execution_result=result)
            history.append(record)

            # 更新最佳结果（优先成功，其次 stderr 最短的）
            if best_result is None or result.success or (
                not best_result.success and len(result.stderr) < len(best_result.stderr)
            ):
                best_result = result

            # 成功则退出（可选：额外做质量检查）
            if result.success:
                # 如果开启了质量检查，代码能跑但质量不达标也触发修复
                if self.enable_quality_check and round_num < self.max_rounds:
                    quality_ok = await self._run_quality_check(project_path, generated_files)
                    if not quality_ok:
                        print("   ⚠️ 执行成功但质量检查未通过，触发修复...")
                        fix_result = await self._try_fix(
                            result, project_path, generated_files,
                            extra_prompt="代码可以运行，但质量检查（linter/类型检查）未通过，请优化代码质量。"
                        )
                        continue

                print(f"   ✅ 第 {round_num} 轮执行成功！")
                return IterationOutcome(
                    success=True,
                    total_rounds=round_num,
                    best_result=result,
                    history=history,
                    message=f"执行成功，共 {round_num} 轮",
                )

            # 还有重试机会，让 LLM 修复
            if round_num < self.max_rounds:
                fix_result = await self._try_fix(
                    result, project_path, generated_files
                )
                if fix_result:
                    record.fix_applied = fix_result.get("analysis", "")
                    record.files_modified = [f["file"] for f in fix_result.get("fixes", [])]
                else:
                    print("   ⚠️ LLM 未能提供有效修复方案")

        # 达到上限
        print(f"   ⚠️ 达到最大轮数 {self.max_rounds}，未能修复所有错误")
        return IterationOutcome(
            success=False,
            total_rounds=self.max_rounds,
            best_result=best_result or result,
            history=history,
            message=f"达到最大轮数 {self.max_rounds}，项目仍有错误",
        )

    async def _try_fix(
        self,
        result: ExecutionResult,
        project_path: str,
        generated_files: Optional[List[str]],
        extra_prompt: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        让 LLM 分析错误并修复文件。

        Args:
            extra_prompt: 额外的修复指令（如质量检查未通过时的提示）

        Returns:
            修复方案 dict（含 analysis 和 fixes），失败返回 None
        """
        if not self.llm_client:
            return None

        try:
            # 构建错误上下文
            error_ctx = build_error_context(result.stderr, project_path, generated_files)
            prompt = build_fix_prompt(error_ctx, project_path)
            if extra_prompt:
                prompt = f"{extra_prompt}\n\n{prompt}"

            # 调用 LLM
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_client.create(messages)
            content = response["choices"][0]["message"]["content"]

            # 解析修复方案
            fixes = self._parse_fix_response(content)
            if not fixes:
                return None

            # 应用修复
            for fix in fixes.get("fixes", []):
                file_path = os.path.join(project_path, fix["file"])
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(fix["content"])
                print(f"   📝 已修复: {fix['file']}")

            return fixes

        except Exception as e:
            print(f"   ❌ 修复过程出错: {e}")
            return None

    async def _run_quality_check(self, project_path: str, generated_files: Optional[List[str]]) -> bool:
        """
        快速质量检查（仅 linter），不跑完整质量闭环。
        返回 True 表示通过。
        """
        try:
            from src.core.quality_loop import QualityLoop
            loop = QualityLoop(timeout=30)
            report = loop.run_linter(project_path)
            return report.status.value in ("pass", "skip")
        except Exception:
            return True  # 检查失败不影响流程

    def _parse_fix_response(self, content: str) -> Optional[Dict[str, Any]]:
        """从 LLM 回复中提取 JSON 修复方案"""
        import re
        import json

        # 尝试提取 ```json ... ``` 块
        match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试直接解析整个内容
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 尝试找任意 JSON 对象
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        return None
