"""
代码质量检查模块
自动生成测试用例和代码质量检查
"""
import os
import subprocess
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from legacy.requirement_parser import TechStack, ProjectRequirement

class QualityCheckType(Enum):
    """质量检查类型"""
    SYNTAX = "syntax"
    LINT = "lint"
    TEST = "test"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"

@dataclass
class QualityIssue:
    """质量问题结构"""
    type: QualityCheckType
    severity: str  # error, warning, info
    file_path: str
    line_number: int
    message: str
    suggestion: Optional[str] = None

@dataclass
class QualityReport:
    """质量报告结构"""
    overall_score: float
    issues: List[QualityIssue]
    test_coverage: float
    security_issues: int
    performance_score: float
    recommendations: List[str]

class CodeQualityChecker:
    """代码质量检查器"""
    
    def __init__(self):
        self.supported_languages = {
            TechStack.PYTHON_FASTAPI: "python",
            TechStack.PYTHON_FLASK: "python",
            TechStack.NODEJS_EXPRESS: "javascript",
            TechStack.JAVA_SPRING_BOOT: "java",
            TechStack.GO_GIN: "go"
        }
    
    async def check_project_quality(self, project_path: str, tech_stack: TechStack, requirements: ProjectRequirement) -> QualityReport:
        """检查项目代码质量"""
        print(f"🔍 开始代码质量检查: {project_path}")
        
        issues = []
        test_coverage = 0.0
        security_issues = 0
        performance_score = 100.0
        recommendations = []
        
        # 语法检查
        syntax_issues = await self._check_syntax(project_path, tech_stack)
        issues.extend(syntax_issues)
        
        # 代码规范检查
        lint_issues = await self._check_linting(project_path, tech_stack)
        issues.extend(lint_issues)
        
        # 测试覆盖率
        test_coverage = await self._check_test_coverage(project_path, tech_stack)
        
        # 安全检查
        security_issues_list = await self._check_security(project_path, tech_stack)
        issues.extend(security_issues_list)
        security_issues = len([issue for issue in security_issues_list if issue.severity == "error"])
        
        # 性能检查
        performance_issues = await self._check_performance(project_path, tech_stack)
        issues.extend(performance_issues)
        
        # 文档检查
        doc_issues = await self._check_documentation(project_path, tech_stack)
        issues.extend(doc_issues)
        
        # 生成建议
        recommendations = self._generate_recommendations(issues, test_coverage, security_issues)
        
        # 计算总体评分
        overall_score = self._calculate_overall_score(issues, test_coverage, security_issues)
        
        return QualityReport(
            overall_score=overall_score,
            issues=issues,
            test_coverage=test_coverage,
            security_issues=security_issues,
            performance_score=performance_score,
            recommendations=recommendations
        )
    
    async def _check_syntax(self, project_path: str, tech_stack: TechStack) -> List[QualityIssue]:
        """检查语法错误"""
        issues = []
        
        try:
            if tech_stack in [TechStack.PYTHON_FASTAPI, TechStack.PYTHON_FLASK]:
                # Python语法检查
                result = subprocess.run(
                    ["python", "-m", "py_compile", "--help"],
                    capture_output=True,
                    text=True,
                    cwd=project_path
                )
                
                # 检查所有Python文件
                for root, dirs, files in os.walk(project_path):
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            result = subprocess.run(
                                ["python", "-m", "py_compile", file_path],
                                capture_output=True,
                                text=True
                            )
                            if result.returncode != 0:
                                issues.append(QualityIssue(
                                    type=QualityCheckType.SYNTAX,
                                    severity="error",
                                    file_path=file_path,
                                    line_number=0,
                                    message=f"语法错误: {result.stderr.strip()}",
                                    suggestion="请检查Python语法"
                                ))
            
            elif tech_stack == TechStack.NODEJS_EXPRESS:
                # JavaScript语法检查
                result = subprocess.run(
                    ["node", "--check", "app.js"],
                    capture_output=True,
                    text=True,
                    cwd=project_path
                )
                if result.returncode != 0:
                    issues.append(QualityIssue(
                        type=QualityCheckType.SYNTAX,
                        severity="error",
                        file_path="app.js",
                        line_number=0,
                        message=f"语法错误: {result.stderr.strip()}",
                        suggestion="请检查JavaScript语法"
                    ))
            
            elif tech_stack == TechStack.JAVA_SPRING_BOOT:
                # Java语法检查
                result = subprocess.run(
                    ["mvn", "compile"],
                    capture_output=True,
                    text=True,
                    cwd=project_path
                )
                if result.returncode != 0:
                    issues.append(QualityIssue(
                        type=QualityCheckType.SYNTAX,
                        severity="error",
                        file_path="src",
                        line_number=0,
                        message=f"编译错误: {result.stderr.strip()}",
                        suggestion="请检查Java语法和依赖"
                    ))
            
            elif tech_stack == TechStack.GO_GIN:
                # Go语法检查
                result = subprocess.run(
                    ["go", "build", "./..."],
                    capture_output=True,
                    text=True,
                    cwd=project_path
                )
                if result.returncode != 0:
                    issues.append(QualityIssue(
                        type=QualityCheckType.SYNTAX,
                        severity="error",
                        file_path=".",
                        line_number=0,
                        message=f"编译错误: {result.stderr.strip()}",
                        suggestion="请检查Go语法"
                    ))
        
        except Exception as e:
            print(f"⚠️ 语法检查失败: {e}")
        
        return issues
    
    async def _check_linting(self, project_path: str, tech_stack: TechStack) -> List[QualityIssue]:
        """检查代码规范"""
        issues = []
        
        try:
            if tech_stack in [TechStack.PYTHON_FASTAPI, TechStack.PYTHON_FLASK]:
                # Python代码规范检查
                try:
                    result = subprocess.run(
                        ["flake8", "--version"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        # 使用flake8检查
                        result = subprocess.run(
                            ["flake8", project_path],
                            capture_output=True,
                            text=True
                        )
                        if result.stdout:
                            for line in result.stdout.strip().split('\n'):
                                if ':' in line:
                                    parts = line.split(':')
                                    if len(parts) >= 4:
                                        file_path = parts[0]
                                        line_num = int(parts[1])
                                        message = ':'.join(parts[3:]).strip()
                                        issues.append(QualityIssue(
                                            type=QualityCheckType.LINT,
                                            severity="warning",
                                            file_path=file_path,
                                            line_number=line_num,
                                            message=message,
                                            suggestion="遵循PEP8代码规范"
                                        ))
                except FileNotFoundError:
                    # flake8未安装，跳过检查
                    pass
            
            elif tech_stack == TechStack.NODEJS_EXPRESS:
                # JavaScript代码规范检查
                try:
                    result = subprocess.run(
                        ["eslint", "--version"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        result = subprocess.run(
                            ["eslint", "app.js"],
                            capture_output=True,
                            text=True,
                            cwd=project_path
                        )
                        if result.stdout:
                            for line in result.stdout.strip().split('\n'):
                                if ':' in line:
                                    parts = line.split(':')
                                    if len(parts) >= 3:
                                        file_path = parts[0]
                                        line_num = int(parts[1])
                                        message = ':'.join(parts[2:]).strip()
                                        issues.append(QualityIssue(
                                            type=QualityCheckType.LINT,
                                            severity="warning",
                                            file_path=file_path,
                                            line_number=line_num,
                                            message=message,
                                            suggestion="遵循JavaScript代码规范"
                                        ))
                except FileNotFoundError:
                    # eslint未安装，跳过检查
                    pass
        
        except Exception as e:
            print(f"⚠️ 代码规范检查失败: {e}")
        
        return issues
    
    async def _check_test_coverage(self, project_path: str, tech_stack: TechStack) -> float:
        """检查测试覆盖率"""
        try:
            if tech_stack in [TechStack.PYTHON_FASTAPI, TechStack.PYTHON_FLASK]:
                # Python测试覆盖率
                try:
                    result = subprocess.run(
                        ["coverage", "run", "-m", "pytest"],
                        capture_output=True,
                        text=True,
                        cwd=project_path
                    )
                    if result.returncode == 0:
                        result = subprocess.run(
                            ["coverage", "report", "--show-missing"],
                            capture_output=True,
                            text=True,
                            cwd=project_path
                        )
                        if result.stdout:
                            # 解析覆盖率
                            for line in result.stdout.split('\n'):
                                if 'TOTAL' in line:
                                    parts = line.split()
                                    if len(parts) >= 4:
                                        try:
                                            return float(parts[-1].replace('%', ''))
                                        except ValueError:
                                            pass
                except FileNotFoundError:
                    pass
            
            elif tech_stack == TechStack.NODEJS_EXPRESS:
                # JavaScript测试覆盖率
                try:
                    result = subprocess.run(
                        ["npm", "test", "--", "--coverage"],
                        capture_output=True,
                        text=True,
                        cwd=project_path
                    )
                    if result.returncode == 0:
                        # 解析覆盖率输出
                        for line in result.stdout.split('\n'):
                            if 'All files' in line or 'Lines' in line:
                                parts = line.split()
                                for part in parts:
                                    if '%' in part:
                                        try:
                                            return float(part.replace('%', ''))
                                        except ValueError:
                                            pass
                except FileNotFoundError:
                    pass
        
        except Exception as e:
            print(f"⚠️ 测试覆盖率检查失败: {e}")
        
        return 0.0
    
    async def _check_security(self, project_path: str, tech_stack: TechStack) -> List[QualityIssue]:
        """安全检查"""
        issues = []
        
        try:
            if tech_stack in [TechStack.PYTHON_FASTAPI, TechStack.PYTHON_FLASK]:
                # Python安全检查
                try:
                    result = subprocess.run(
                        ["bandit", "-r", project_path],
                        capture_output=True,
                        text=True
                    )
                    if result.stdout:
                        for line in result.stdout.split('\n'):
                            if '>> Issue:' in line:
                                # 解析bandit输出
                                parts = line.split('>> Issue:')
                                if len(parts) > 1:
                                    message = parts[1].strip()
                                    issues.append(QualityIssue(
                                        type=QualityCheckType.SECURITY,
                                        severity="warning",
                                        file_path="",
                                        line_number=0,
                                        message=message,
                                        suggestion="请检查安全漏洞"
                                    ))
                except FileNotFoundError:
                    # bandit未安装，跳过检查
                    pass
            
            elif tech_stack == TechStack.NODEJS_EXPRESS:
                # JavaScript安全检查
                try:
                    result = subprocess.run(
                        ["npm", "audit"],
                        capture_output=True,
                        text=True,
                        cwd=project_path
                    )
                    if result.stdout:
                        for line in result.stdout.split('\n'):
                            if 'vulnerability' in line.lower():
                                issues.append(QualityIssue(
                                    type=QualityCheckType.SECURITY,
                                    severity="warning",
                                    file_path="package.json",
                                    line_number=0,
                                    message=line.strip(),
                                    suggestion="请更新依赖包版本"
                                ))
                except FileNotFoundError:
                    pass
        
        except Exception as e:
            print(f"⚠️ 安全检查失败: {e}")
        
        return issues
    
    async def _check_performance(self, project_path: str, tech_stack: TechStack) -> List[QualityIssue]:
        """性能检查"""
        issues = []
        
        # 检查常见性能问题
        for root, dirs, files in os.walk(project_path):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith(('.py', '.js', '.java', '.go')):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # 检查性能问题
                        if 'for i in range(len(' in content:
                            issues.append(QualityIssue(
                                type=QualityCheckType.PERFORMANCE,
                                severity="info",
                                file_path=file_path,
                                line_number=0,
                                message="使用enumerate()替代range(len())",
                                suggestion="使用enumerate()提高性能"
                            ))
                        
                        if 'import *' in content:
                            issues.append(QualityIssue(
                                type=QualityCheckType.PERFORMANCE,
                                severity="warning",
                                file_path=file_path,
                                line_number=0,
                                message="避免使用import *",
                                suggestion="明确导入需要的模块"
                            ))
        
        return issues
    
    async def _check_documentation(self, project_path: str, tech_stack: TechStack) -> List[QualityIssue]:
        """文档检查"""
        issues = []
        
        # 检查是否有README文件
        readme_files = []
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if file.lower().startswith('readme'):
                    readme_files.append(os.path.join(root, file))
        
        if not readme_files:
            issues.append(QualityIssue(
                type=QualityCheckType.DOCUMENTATION,
                severity="warning",
                file_path="",
                line_number=0,
                message="缺少README文档",
                suggestion="添加README.md文件"
            ))
        
        # 检查代码注释
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if file.endswith(('.py', '.js', '.java', '.go')):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                        
                        # 检查函数是否有注释
                        for i, line in enumerate(lines):
                            if line.strip().startswith(('def ', 'function ', 'public ', 'func ')):
                                # 检查下一行是否有注释
                                if i + 1 < len(lines) and not lines[i + 1].strip().startswith(('"""', "'''", '//', '/*')):
                                    issues.append(QualityIssue(
                                        type=QualityCheckType.DOCUMENTATION,
                                        severity="info",
                                        file_path=file_path,
                                        line_number=i + 1,
                                        message="函数缺少文档注释",
                                        suggestion="为函数添加文档注释"
                                    ))
        
        return issues
    
    def _generate_recommendations(self, issues: List[QualityIssue], test_coverage: float, security_issues: int) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于问题类型生成建议
        error_count = len([issue for issue in issues if issue.severity == "error"])
        warning_count = len([issue for issue in issues if issue.severity == "warning"])
        
        if error_count > 0:
            recommendations.append(f"修复 {error_count} 个错误")
        
        if warning_count > 0:
            recommendations.append(f"处理 {warning_count} 个警告")
        
        if test_coverage < 80:
            recommendations.append(f"提高测试覆盖率到80%以上（当前: {test_coverage:.1f}%）")
        
        if security_issues > 0:
            recommendations.append(f"修复 {security_issues} 个安全问题")
        
        # 通用建议
        recommendations.extend([
            "添加适当的错误处理",
            "优化代码性能",
            "完善文档注释",
            "遵循代码规范"
        ])
        
        return recommendations
    
    def _calculate_overall_score(self, issues: List[QualityIssue], test_coverage: float, security_issues: int) -> float:
        """计算总体评分"""
        score = 100.0
        
        # 根据问题数量扣分
        error_count = len([issue for issue in issues if issue.severity == "error"])
        warning_count = len([issue for issue in issues if issue.severity == "warning"])
        
        score -= error_count * 10  # 每个错误扣10分
        score -= warning_count * 2  # 每个警告扣2分
        
        # 根据测试覆盖率调整分数
        if test_coverage < 50:
            score -= 20
        elif test_coverage < 80:
            score -= 10
        
        # 根据安全问题扣分
        score -= security_issues * 5
        
        return max(0.0, min(100.0, score))
    
    def generate_quality_report(self, report: QualityReport) -> str:
        """生成质量报告"""
        report_text = "📊 代码质量报告\n"
        report_text += "=" * 50 + "\n"
        report_text += f"总体评分: {report.overall_score:.1f}/100\n"
        report_text += f"测试覆盖率: {report.test_coverage:.1f}%\n"
        report_text += f"安全问题: {report.security_issues}个\n"
        report_text += f"性能评分: {report.performance_score:.1f}/100\n\n"
        
        if report.issues:
            report_text += "🔍 发现的问题:\n"
            for issue in report.issues[:10]:  # 只显示前10个问题
                report_text += f"- [{issue.severity.upper()}] {issue.file_path}:{issue.line_number} - {issue.message}\n"
                if issue.suggestion:
                    report_text += f"  建议: {issue.suggestion}\n"
        
        if report.recommendations:
            report_text += "\n💡 改进建议:\n"
            for rec in report.recommendations:
                report_text += f"- {rec}\n"
        
        return report_text
