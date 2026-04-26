"""
自动修复器
接收 linter/type-check/test 报错 → 调用 LLM 生成修复 → 重新检查，形成闭环
"""
import os
import json
import re
from typing import List, Dict, Any, Optional

from src.core.quality_loop import QualityLoop, QualityReport, CheckResult, CheckStatus


class AutoFixer:
    """自动修复：报错 → LLM 修复 → 重新检查，最多迭代3轮"""

    MAX_FIX_ROUNDS = 3

    def __init__(self, llm_client=None, quality_loop: QualityLoop = None):
        """
        Args:
            llm_client: LLM 客户端（需要有 async create 方法）
            quality_loop: QualityLoop 实例，默认新建一个
        """
        self.llm_client = llm_client
        self.quality_loop = quality_loop or QualityLoop()

    async def fix(
        self,
        project_path: str,
        tech_stack: str = "",
        max_rounds: int = 0,
    ) -> QualityReport:
        """
        执行自动修复循环。

        Args:
            project_path: 项目路径
            tech_stack: 技术栈名称
            max_rounds: 最大修复轮数（默认 MAX_FIX_ROUNDS）

        Returns:
            最终的 QualityReport
        """
        if not max_rounds:
            max_rounds = self.MAX_FIX_ROUNDS

        report = self.quality_loop.check_all(project_path, tech_stack)

        for round_num in range(1, max_rounds + 1):
            if report.passed:
                print(f"   ✅ 质量检查通过，无需修复")
                return report

            # 收集所有失败的检查结果
            failed = [r for r in report.results if r.status == CheckStatus.FAIL]
            if not failed:
                return report

            print(f"   🔧 自动修复第 {round_num}/{max_rounds} 轮，{len(failed)} 项检查失败")

            # 调用 LLM 修复
            fix_applied = await self._apply_llm_fix(project_path, failed)
            if not fix_applied:
                print(f"   ⚠️ LLM 未能提供有效修复")
                break

            # 重新检查
            report = self.quality_loop.check_all(project_path, tech_stack)

        return report

    async def _apply_llm_fix(
        self,
        project_path: str,
        failed_results: List[CheckResult],
    ) -> bool:
        """
        把报错格式化成 prompt，调用 LLM，应用修复。

        Returns:
            是否成功应用了修复
        """
        if not self.llm_client:
            return False

        try:
            # 构建修复 prompt
            prompt = self._build_fix_prompt(project_path, failed_results)

            # 调用 LLM
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_client.create(messages)
            content = response["choices"][0]["message"]["content"]

            # 解析修复方案
            fixes = self._parse_fix_response(content)
            if not fixes:
                return False

            # 应用修复
            for fix in fixes.get("fixes", []):
                file_path = os.path.join(project_path, fix["file"])
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(fix["content"])
                print(f"   📝 已修复: {fix['file']}")

            return True

        except Exception as e:
            print(f"   ❌ LLM 修复过程出错: {e}")
            return False

    def _build_fix_prompt(self, project_path: str, failed_results: List[CheckResult]) -> str:
        """构建 LLM 修复 prompt"""
        error_parts = []
        for r in failed_results:
            error_parts.append(f"### {r.name}\n状态: {r.status.value}\n{r.output[:2000]}")

        errors_text = "\n\n".join(error_parts)

        # 读取项目中的关键文件内容
        file_contents = self._read_project_files(project_path, max_files=10, max_lines=50)

        return f"""你是代码修复专家。以下项目在质量检查中发现了问题，请分析并修复。

项目路径: {project_path}

## 检查报错

{errors_text}

## 项目文件内容

{file_contents}

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
```"""

    def _read_project_files(self, project_path: str, max_files: int = 10, max_lines: int = 50) -> str:
        """读取项目中的文件，返回格式化内容"""
        parts = []
        count = 0
        skip_dirs = {"__pycache__", ".git", "node_modules", "venv", ".venv"}

        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fname in sorted(files):
                ext = os.path.splitext(fname)[1]
                if ext not in {".py", ".js", ".ts", ".java", ".go", ".jsx", ".tsx"}:
                    continue
                fpath = os.path.join(root, fname)
                rel = os.path.relpath(fpath, project_path)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()[:max_lines]
                    parts.append(f"### {rel}\n```\n{''.join(lines)}\n```\n")
                    count += 1
                    if count >= max_files:
                        break
                except Exception:
                    pass
            if count >= max_files:
                break

        return "\n".join(parts)

    def _parse_fix_response(self, content: str) -> Optional[Dict[str, Any]]:
        """从 LLM 回复中提取 JSON 修复方案"""
        # ```json ... ``` 块
        match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 任意 JSON 对象
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        return None
