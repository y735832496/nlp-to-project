"""
执行沙箱模块
在 subprocess 中执行生成的项目代码，捕获输出，支持超时控制
"""
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class ExecutionResult:
    """结构化的执行结果"""
    success: bool
    return_code: int
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool = False
    command: str = ""
    working_dir: str = ""

    def summary(self) -> str:
        """返回人类可读的摘要"""
        lines = [
            f"命令: {self.command}",
            f"退出码: {self.return_code}",
            f"耗时: {self.duration_ms:.0f}ms",
            f"状态: {'超时' if self.timed_out else ('成功' if self.success else '失败')}",
        ]
        if self.stdout.strip():
            lines.append(f"stdout:\n{self.stdout[:2000]}")
        if self.stderr.strip():
            lines.append(f"stderr:\n{self.stderr[:2000]}")
        return "\n".join(lines)


class ExecutionSandbox:
    """
    执行沙箱：在受限的 subprocess 中运行代码，捕获 stdout/stderr/returncode。
    支持超时控制和环境变量注入。
    """

    def __init__(self, timeout: int = 30, env: Optional[Dict[str, str]] = None):
        """
        Args:
            timeout: 单次执行的超时秒数，默认30秒
            env: 额外的环境变量（会继承当前进程环境）
        """
        self.timeout = timeout
        self.extra_env = env or {}

    def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> ExecutionResult:
        """
        执行一条 shell 命令。

        Args:
            command: 要执行的命令
            cwd: 工作目录，默认使用当前目录
            timeout: 本次执行的超时秒数，None 则用实例默认值
            env: 本次执行的额外环境变量

        Returns:
            ExecutionResult 结构化结果
        """
        actual_timeout = timeout or self.timeout

        # 合并环境变量
        full_env = os.environ.copy()
        full_env.update(self.extra_env)
        if env:
            full_env.update(env)

        start = time.monotonic()
        timed_out = False

        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=actual_timeout,
                env=full_env,
            )
            duration_ms = (time.monotonic() - start) * 1000

            return ExecutionResult(
                success=proc.returncode == 0,
                return_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_ms=duration_ms,
                timed_out=False,
                command=command,
                working_dir=cwd or os.getcwd(),
            )

        except subprocess.TimeoutExpired as e:
            duration_ms = (time.monotonic() - start) * 1000
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout=e.stdout or "" if hasattr(e, "stdout") and e.stdout else "",
                stderr=e.stderr or "" if hasattr(e, "stderr") and e.stderr else f"命令超时（{actual_timeout}秒）",
                duration_ms=duration_ms,
                timed_out=True,
                command=command,
                working_dir=cwd or os.getcwd(),
            )

        except Exception as e:
            duration_ms = (time.monotonic() - start) * 1000
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=str(e),
                duration_ms=duration_ms,
                timed_out=False,
                command=command,
                working_dir=cwd or os.getcwd(),
            )

    def execute_python(
        self,
        script_path: str,
        cwd: Optional[str] = None,
        args: Optional[List[str]] = None,
        timeout: Optional[int] = None,
    ) -> ExecutionResult:
        """快捷方法：执行 Python 脚本"""
        cmd = f"python {script_path}"
        if args:
            cmd += " " + " ".join(args)
        return self.execute(cmd, cwd=cwd, timeout=timeout)

    def execute_node(
        self,
        script_path: str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> ExecutionResult:
        """快捷方法：执行 Node.js 脚本"""
        return self.execute(f"node {script_path}", cwd=cwd, timeout=timeout)
