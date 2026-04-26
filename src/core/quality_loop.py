"""
质量闭环系统
集成 linter、类型检查、测试运行，支持优雅降级
"""
import os
import subprocess
import shutil
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class CheckStatus(Enum):
    """检查结果状态"""
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"  # 工具未安装，跳过


@dataclass
class CheckResult:
    """单次检查结果"""
    name: str           # 检查项名称（如 "ruff", "mypy", "pytest"）
    status: CheckStatus
    output: str = ""    # 工具原始输出
    errors: int = 0     # 错误数
    warnings: int = 0   # 警告数
    details: str = ""   # 人类可读摘要


@dataclass
class QualityReport:
    """完整质量报告"""
    results: List[CheckResult] = field(default_factory=list)
    total_errors: int = 0
    total_warnings: int = 0
    passed: bool = True

    def add(self, result: CheckResult):
        self.results.append(result)
        if result.status == CheckStatus.FAIL:
            self.passed = False
            self.total_errors += result.errors
        self.total_warnings += result.warnings

    def summary(self) -> str:
        lines = ["📊 质量报告"]
        for r in self.results:
            icon = {"pass": "✅", "fail": "❌", "warn": "⚠️", "skip": "⏭️"}.get(r.status.value, "?")
            lines.append(f"  {icon} {r.name}: {r.status.value} (errors={r.errors}, warnings={r.warnings})")
            if r.details:
                lines.append(f"     {r.details[:200]}")
        lines.append(f"\n总计: errors={self.total_errors}, warnings={self.total_warnings}, 通过={'是' if self.passed else '否'}")
        return "\n".join(lines)


def _run_command(cmd: List[str], cwd: str, timeout: int = 60) -> Tuple[int, str, str]:
    """运行命令，返回 (returncode, stdout, stderr)"""
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return -1, "", "命令未找到"
    except subprocess.TimeoutExpired:
        return -2, "", "超时"
    except Exception as e:
        return -3, "", str(e)


def _tool_available(name: str) -> bool:
    """检查工具是否可用"""
    return shutil.which(name) is not None


# 需要用 Tuple 但在函数签名中已导入

class QualityLoop:
    """质量闭环：linter + 类型检查 + 测试"""

    def __init__(self, timeout: int = 60):
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Linter
    # ------------------------------------------------------------------
    def run_linter(self, project_path: str, tech_stack: str = "") -> CheckResult:
        """根据技术栈选择 linter"""
        tech = tech_stack.lower() if tech_stack else ""

        if "python" in tech or tech == "":
            return self._run_python_linter(project_path)
        elif "node" in tech or "javascript" in tech or "typescript" in tech:
            return self._run_node_linter(project_path)
        elif "java" in tech:
            return self._run_java_linter(project_path)
        else:
            return CheckResult("linter", CheckStatus.SKIP, details=f"不支持的技术栈: {tech_stack}")

    def _run_python_linter(self, project_path: str) -> CheckResult:
        """Python linter：优先 ruff，其次 pylint"""
        # ruff
        if _tool_available("ruff"):
            rc, out, err = _run_command(["ruff", "check", ".", "--output-format=text"], project_path, self.timeout)
            errors = out.count("error") if rc != 0 else 0
            warnings = out.count("warning") if out else 0
            status = CheckStatus.PASS if rc == 0 else CheckStatus.FAIL
            return CheckResult("ruff", status, output=out + err, errors=errors, warnings=warnings, details=out[:300])

        # pylint
        if _tool_available("pylint"):
            py_files = []
            for root, _, files in os.walk(project_path):
                for f in files:
                    if f.endswith(".py"):
                        py_files.append(os.path.relpath(os.path.join(root, f), project_path))
            if not py_files:
                return CheckResult("pylint", CheckStatus.SKIP, details="无 Python 文件")
            rc, out, err = _run_command(["pylint"] + py_files[:20], project_path, self.timeout * 2)
            # pylint 的评分在输出里
            errors = max(0, (out.count(": error") + out.count(": fatal")))
            status = CheckStatus.PASS if rc == 0 else CheckStatus.FAIL
            return CheckResult("pylint", status, output=out + err, errors=errors, details=out[:300])

        return CheckResult("linter", CheckStatus.SKIP, details="未安装 ruff 或 pylint，跳过 lint 检查")

    def _run_node_linter(self, project_path: str) -> CheckResult:
        """Node.js linter：eslint"""
        if _tool_available("eslint"):
            rc, out, err = _run_command(
                ["npx", "eslint", ".", "--format=compact"],
                project_path, self.timeout
            )
            errors = out.count(" - error:") if out else 0
            warnings = out.count(" - warning:") if out else 0
            status = CheckStatus.PASS if rc == 0 else CheckStatus.FAIL
            return CheckResult("eslint", status, output=out + err, errors=errors, warnings=warnings, details=out[:300])

        return CheckResult("eslint", CheckStatus.SKIP, details="未安装 eslint，跳过")

    def _run_java_linter(self, project_path: str) -> CheckResult:
        """Java linter：checkstyle"""
        if _tool_available("checkstyle"):
            rc, out, err = _run_command(
                ["checkstyle", "-c", "/dev/stdin", "."],
                project_path, self.timeout
            )
            return CheckResult("checkstyle", CheckStatus.PASS if rc == 0 else CheckStatus.FAIL,
                               output=out + err, details=out[:300])

        return CheckResult("checkstyle", CheckStatus.SKIP, details="未安装 checkstyle，跳过")

    # ------------------------------------------------------------------
    # 类型检查
    # ------------------------------------------------------------------
    def run_type_check(self, project_path: str, tech_stack: str = "") -> CheckResult:
        """根据技术栈选择类型检查工具"""
        tech = tech_stack.lower() if tech_stack else ""

        if "python" in tech or tech == "":
            return self._run_python_type_check(project_path)
        elif "typescript" in tech:
            return self._run_ts_type_check(project_path)
        else:
            return CheckResult("type_check", CheckStatus.SKIP, details=f"无对应类型检查工具: {tech_stack}")

    def _run_python_type_check(self, project_path: str) -> CheckResult:
        """Python: mypy"""
        if _tool_available("mypy"):
            rc, out, err = _run_command(
                ["mypy", ".", "--ignore-missing-imports", "--no-error-summary"],
                project_path, self.timeout * 2
            )
            errors = out.count(": error:") if out else 0
            status = CheckStatus.PASS if errors == 0 else CheckStatus.FAIL
            return CheckResult("mypy", status, output=out + err, errors=errors, details=out[:300])

        return CheckResult("mypy", CheckStatus.SKIP, details="未安装 mypy，跳过类型检查")

    def _run_ts_type_check(self, project_path: str) -> CheckResult:
        """TypeScript: tsc --noEmit"""
        if _tool_available("tsc"):
            rc, out, err = _run_command(["tsc", "--noEmit"], project_path, self.timeout * 2)
            errors = out.count("error TS") if out else 0
            status = CheckStatus.PASS if errors == 0 else CheckStatus.FAIL
            return CheckResult("tsc", status, output=out + err, errors=errors, details=out[:300])

        return CheckResult("tsc", CheckStatus.SKIP, details="未安装 tsc，跳过类型检查")

    # ------------------------------------------------------------------
    # 测试
    # ------------------------------------------------------------------
    def run_tests(self, project_path: str, tech_stack: str = "") -> CheckResult:
        """自动发现并运行测试"""
        tech = tech_stack.lower() if tech_stack else ""

        if "python" in tech or tech == "":
            return self._run_python_tests(project_path)
        elif "node" in tech or "javascript" in tech or "typescript" in tech:
            return self._run_node_tests(project_path)
        elif "java" in tech:
            return self._run_java_tests(project_path)
        elif "go" in tech:
            return self._run_go_tests(project_path)
        else:
            return CheckResult("tests", CheckStatus.SKIP, details=f"未知的测试框架: {tech_stack}")

    def _run_python_tests(self, project_path: str) -> CheckResult:
        """Python: 优先 pytest，其次 unittest"""
        if _tool_available("pytest"):
            rc, out, err = _run_command(["pytest", "--tb=short", "-q"], project_path, self.timeout * 2)
            errors = out.count("FAILED") if out else 0
            status = CheckStatus.PASS if rc == 0 else CheckStatus.FAIL
            return CheckResult("pytest", status, output=out + err, errors=errors, details=out[:300])

        # unittest 兜底
        rc, out, err = _run_command(["python", "-m", "unittest", "discover", "-s", ".", "-q"],
                                     project_path, self.timeout * 2)
        errors = out.count("FAIL:") + out.count("ERROR:") if out else 0
        status = CheckStatus.PASS if rc == 0 else CheckStatus.FAIL
        return CheckResult("unittest", status, output=out + err, errors=errors, details=out[:300])

    def _run_node_tests(self, project_path: str) -> CheckResult:
        """Node.js: npm test"""
        if os.path.isfile(os.path.join(project_path, "package.json")):
            rc, out, err = _run_command(["npm", "test"], project_path, self.timeout * 2)
            status = CheckStatus.PASS if rc == 0 else CheckStatus.FAIL
            return CheckResult("npm_test", status, output=out + err, details=(out + err)[:300])

        return CheckResult("npm_test", CheckStatus.SKIP, details="无 package.json，跳过测试")

    def _run_java_tests(self, project_path: str) -> CheckResult:
        """Java: mvn test"""
        if _tool_available("mvn") and os.path.isfile(os.path.join(project_path, "pom.xml")):
            rc, out, err = _run_command(["mvn", "test", "-q"], project_path, self.timeout * 3)
            status = CheckStatus.PASS if rc == 0 else CheckStatus.FAIL
            return CheckResult("mvn_test", status, output=out + err, details=(out + err)[:300])

        return CheckResult("mvn_test", CheckStatus.SKIP, details="未安装 mvn 或无 pom.xml，跳过")

    def _run_go_tests(self, project_path: str) -> CheckResult:
        """Go: go test"""
        if _tool_available("go"):
            rc, out, err = _run_command(["go", "test", "./..."], project_path, self.timeout * 2)
            status = CheckStatus.PASS if rc == 0 else CheckStatus.FAIL
            return CheckResult("go_test", status, output=out + err, details=(out + err)[:300])

        return CheckResult("go_test", CheckStatus.SKIP, details="未安装 go，跳过")

    # ------------------------------------------------------------------
    # 一键全量检查
    # ------------------------------------------------------------------
    def check_all(self, project_path: str, tech_stack: str = "") -> QualityReport:
        """一键跑全部检查，返回 QualityReport"""
        report = QualityReport()

        report.add(self.run_linter(project_path, tech_stack))
        report.add(self.run_type_check(project_path, tech_stack))
        report.add(self.run_tests(project_path, tech_stack))

        return report
