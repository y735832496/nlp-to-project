"""
上下文管理器
负责管理 LLM 的上下文窗口：智能读取、结构扫描、增量 diff、token 估算、历史压缩
"""
import os
import re
import difflib
from typing import List, Dict, Any, Optional, Tuple


class ContextManager:
    """管理 LLM 上下文窗口，避免超出 token 限制"""

    # 默认上下文窗口上限
    DEFAULT_MAX_TOKENS = 4000

    def __init__(self, max_context_tokens: int = 8000):
        self.max_context_tokens = max_context_tokens

    # ------------------------------------------------------------------
    # 智能文件读取
    # ------------------------------------------------------------------
    def smart_read_file(self, path: str, max_lines: int = 200) -> str:
        """
        大文件只读关键部分（开头 + 结尾 + 函数/类签名），返回摘要。
        小文件直接返回全部内容。
        """
        if not os.path.isfile(path):
            return f"[文件不存在: {path}]"

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception as e:
            return f"[读取失败: {e}]"

        total = len(lines)

        # 小文件直接返回
        if total <= max_lines:
            return "".join(lines)

        # 大文件：开头 + 签名 + 结尾
        head_count = min(50, total // 4)
        tail_count = min(50, total // 4)

        head = lines[:head_count]
        tail = lines[-tail_count:]

        # 提取函数/类签名行
        sig_lines = []
        sig_pattern = re.compile(r"^\s*(def |class |async def |function |public |export )")
        for i, line in enumerate(lines):
            if sig_pattern.match(line):
                sig_lines.append(f"L{i + 1}: {line}")

        parts = [
            f"[文件: {os.path.basename(path)}, 共 {total} 行，已摘要]\n",
            "--- 头部 ---\n",
            *head,
            "\n--- 函数/类签名 ---\n",
            *sig_lines[:80],  # 最多80个签名
            f"\n--- 尾部 (最后 {tail_count} 行) ---\n",
            *tail,
        ]
        return "".join(parts)

    # ------------------------------------------------------------------
    # 项目结构扫描
    # ------------------------------------------------------------------
    def scan_project_structure(self, project_path: str) -> str:
        """
        自动扫描项目文件树，生成结构摘要。
        跳过 __pycache__、.git、node_modules 等目录。
        """
        skip_dirs = {
            "__pycache__", ".git", "node_modules", ".idea",
            ".vscode", "venv", ".venv", "env", ".env",
            "dist", "build", ".next",
        }
        skip_ext = {".pyc", ".pyo", ".class", ".o", ".so", ".exe"}

        summary_lines = [f"项目结构: {project_path}\n"]

        for root, dirs, files in os.walk(project_path):
            # 跳过无用目录
            dirs[:] = [d for d in dirs if d not in skip_dirs]

            rel_root = os.path.relpath(root, project_path)
            if rel_root == ".":
                rel_root = ""

            indent = "  " * rel_root.count(os.sep) if rel_root else ""
            if rel_root:
                summary_lines.append(f"{indent}📁 {os.path.basename(root)}/")

            for fname in sorted(files):
                ext = os.path.splitext(fname)[1]
                if ext in skip_ext:
                    continue
                # 标注文件大小
                fpath = os.path.join(root, fname)
                try:
                    size = os.path.getsize(fpath)
                    if size > 10_000:
                        label = f"({size // 1024}KB)"
                    else:
                        label = ""
                except OSError:
                    label = ""
                child_indent = indent + "  " if rel_root else ""
                summary_lines.append(f"{child_indent}📄 {fname} {label}")

        return "\n".join(summary_lines)

    # ------------------------------------------------------------------
    # 增量 Diff
    # ------------------------------------------------------------------
    @staticmethod
    def build_incremental_diff(old_content: str, new_content: str, context_lines: int = 3) -> str:
        """生成 unified diff 而非全量内容"""
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        diff = difflib.unified_diff(
            old_lines, new_lines,
            fromfile="原文件", tofile="新文件",
            n=context_lines,
        )
        result = "".join(diff)
        return result if result else "[无变化]"

    # ------------------------------------------------------------------
    # Token 估算
    # ------------------------------------------------------------------
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        粗略估算 token 数。
        中文按 ~2 token/字，英文按 ~0.75 token/word，其他字符按 1 token/2字符。
        """
        chinese_chars = 0
        english_words = 0
        other_chars = 0

        # 中文字符
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        # 移除中文
        remaining = re.sub(r"[\u4e00-\u9fff]", " ", text)
        # 英文单词
        english_words = len(re.findall(r"[a-zA-Z]+", remaining))
        # 其他字符（非空白）
        other_chars = len(re.findall(r"[^\s]", remaining)) - english_words

        tokens = chinese_chars * 2 + english_words * 0.75 + max(other_chars, 0) * 0.5
        return int(tokens)

    # ------------------------------------------------------------------
    # 历史压缩
    # ------------------------------------------------------------------
    def compress_context(
        self,
        history: List[Dict[str, str]],
        max_tokens: int = 0,
    ) -> List[Dict[str, str]]:
        """
        压缩对话历史，保留最近几轮 + 关键决策摘要。
        策略：
        1. 保留 system 消息
        2. 从最新消息开始保留，直到接近 max_tokens
        3. 把被裁掉的旧消息压缩成一条摘要
        """
        if not max_tokens:
            max_tokens = self.DEFAULT_MAX_TOKENS

        if not history:
            return history

        # 分离 system 和非 system 消息
        system_msgs = [m for m in history if m.get("role") == "system"]
        non_system = [m for m in history if m.get("role") != "system"]

        if not non_system:
            return history

        # 从尾部保留消息
        kept: List[Dict[str, str]] = []
        token_count = 0

        for msg in reversed(non_system):
            msg_tokens = self.estimate_tokens(msg.get("content", ""))
            if token_count + msg_tokens > max_tokens and kept:
                break
            kept.insert(0, msg)
            token_count += msg_tokens

        # 被裁掉的旧消息 → 摘要
        dropped = non_system[: len(non_system) - len(kept)]
        if dropped:
            summary = self._summarize_old_messages(dropped)
            kept.insert(0, {"role": "system", "content": f"[历史摘要] {summary}"})

        return system_msgs + kept

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------
    @staticmethod
    def _summarize_old_messages(messages: List[Dict[str, str]]) -> str:
        """把旧消息压缩成一段简短摘要"""
        key_points = []
        for msg in messages:
            content = msg.get("content", "")
            role = msg.get("role", "unknown")
            # 取每条消息的前 100 字符作为要点
            snippet = content[:100].replace("\n", " ").strip()
            if snippet:
                key_points.append(f"[{role}] {snippet}")
            if len(key_points) >= 5:
                break

        return "; ".join(key_points)
