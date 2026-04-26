"""
Agent 工具集定义
为 LLM 提供可调用的结构化工具：读文件、写文件、执行命令、列文件、搜索代码
"""
import os
import subprocess
import glob as glob_module
import fnmatch
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class ToolResult:
    """工具调用的结构化返回"""
    success: bool
    output: str
    error: Optional[str] = None
    data: Optional[Any] = None  # 额外的结构化数据


# ─── 工具函数 ───────────────────────────────────────────────────────────────

def read_file(path: str, project_root: str = "") -> ToolResult:
    """
    读取项目文件内容。
    路径可以是绝对路径或相对于 project_root 的相对路径。
    """
    abs_path = path if os.path.isabs(path) else os.path.join(project_root, path)
    try:
        if not os.path.isfile(abs_path):
            return ToolResult(success=False, output="", error=f"文件不存在: {abs_path}")
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return ToolResult(success=True, output=content, data={"path": path, "size": len(content)})
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


def write_file(path: str, content: str, project_root: str = "") -> ToolResult:
    """写入/创建项目文件"""
    abs_path = path if os.path.isabs(path) else os.path.join(project_root, path)
    try:
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        return ToolResult(
            success=True,
            output=f"已写入 {path}（{len(content)} 字符）",
            data={"path": path, "size": len(content)},
        )
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


def execute(command: str, cwd: str = "", timeout: int = 30) -> ToolResult:
    """在工作目录中执行 shell 命令"""
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=cwd or None,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = proc.stdout
        if proc.stderr:
            output += f"\n[stderr]\n{proc.stderr}"
        return ToolResult(
            success=proc.returncode == 0,
            output=output,
            error=proc.stderr if proc.returncode != 0 else None,
            data={"return_code": proc.returncode},
        )
    except subprocess.TimeoutExpired:
        return ToolResult(success=False, output="", error=f"命令超时（{timeout}秒）")
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


def list_files(pattern: str = "*", project_root: str = "") -> ToolResult:
    """列出项目中匹配 pattern 的文件"""
    search_dir = project_root or "."
    try:
        matches = []
        for root, dirs, files in os.walk(search_dir):
            # 跳过隐藏目录和常见无关目录
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in (
                "node_modules", "__pycache__", ".git", "venv", ".venv"
            )]
            for name in files:
                if fnmatch.fnmatch(name, pattern):
                    rel = os.path.relpath(os.path.join(root, name), search_dir)
                    matches.append(rel)

        matches.sort()
        output = "\n".join(matches) if matches else f"没有匹配 '{pattern}' 的文件"
        return ToolResult(success=True, output=output, data={"files": matches, "count": len(matches)})
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


def grep(pattern: str, path: str = "", project_root: str = "", max_results: int = 20) -> ToolResult:
    """在项目文件中搜索匹配行"""
    search_dir = path if os.path.isabs(path) else os.path.join(project_root, path) if path else project_root or "."
    try:
        matches = []
        for root, dirs, files in os.walk(search_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in (
                "node_modules", "__pycache__", ".git", "venv", ".venv"
            )]
            for name in files:
                # 跳过二进制文件
                if any(name.endswith(ext) for ext in (".png", ".jpg", ".gif", ".zip", ".tar", ".pyc")):
                    continue
                abs_path = os.path.join(root, name)
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f, 1):
                            if pattern in line:
                                rel = os.path.relpath(abs_path, project_root or ".")
                                matches.append(f"{rel}:{i}: {line.rstrip()}")
                                if len(matches) >= max_results:
                                    break
                except Exception:
                    continue
                if len(matches) >= max_results:
                    break
            if len(matches) >= max_results:
                break

        output = "\n".join(matches) if matches else f"未找到匹配 '{pattern}' 的内容"
        return ToolResult(
            success=True,
            output=output,
            data={"matches": matches, "count": len(matches)},
        )
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


# ─── 工具注册表 ─────────────────────────────────────────────────────────────

# 工具定义：用于 LLM function calling 或 prompt 模拟
TOOL_DEFINITIONS = [
    {
        "name": "read_file",
        "description": "读取项目文件内容",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径（相对于项目根目录）"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "写入或创建项目文件",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径（相对于项目根目录）"},
                "content": {"type": "string", "description": "文件内容"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "execute",
        "description": "在工作目录中执行 shell 命令",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "要执行的命令"},
                "timeout": {"type": "integer", "description": "超时秒数，默认30", "default": 30},
            },
            "required": ["command"],
        },
    },
    {
        "name": "list_files",
        "description": "列出项目中匹配模式的文件",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "文件名匹配模式，如 '*.py'", "default": "*"},
            },
            "required": [],
        },
    },
    {
        "name": "grep",
        "description": "在项目文件中搜索匹配的文本行",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "搜索的文本模式"},
                "path": {"type": "string", "description": "搜索的目录路径，默认项目根目录", "default": ""},
            },
            "required": ["pattern"],
        },
    },
]

# 工具名 → 执行函数的映射
TOOL_REGISTRY = {
    "read_file": lambda args, root="": read_file(args["path"], project_root=root),
    "write_file": lambda args, root="": write_file(args["path"], args["content"], project_root=root),
    "execute": lambda args, root="": execute(args["command"], cwd=root, timeout=args.get("timeout", 30)),
    "list_files": lambda args, root="": list_files(args.get("pattern", "*"), project_root=root),
    "grep": lambda args, root="": grep(args["pattern"], path=args.get("path", ""), project_root=root),
}


def call_tool(name: str, arguments: Dict[str, Any], project_root: str = "") -> ToolResult:
    """
    统一的工具调用入口。

    Args:
        name: 工具名
        arguments: 工具参数
        project_root: 项目根目录

    Returns:
        ToolResult
    """
    handler = TOOL_REGISTRY.get(name)
    if not handler:
        return ToolResult(success=False, output="", error=f"未知工具: {name}")
    return handler(arguments, root=project_root)
