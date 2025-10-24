#!/usr/bin/env python3
"""
Test Hardening Analyzer
Scans test files and identifies opportunities for improvement
"""

import ast
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set
import json


@dataclass
class TestIssue:
    """Represents a single issue found in a test"""
    severity: str  # 'high', 'medium', 'low'
    category: str
    message: str
    line_number: int = 0


@dataclass
class TestFileAnalysis:
    """Analysis results for a single test file"""
    filepath: Path
    total_lines: int = 0
    test_count: int = 0
    issues: List[TestIssue] = field(default_factory=list)
    long_tests: List[Dict] = field(default_factory=list)
    imports: Set[str] = field(default_factory=set)
    
    @property
    def severity_counts(self):
        return {
            'high': len([i for i in self.issues if i.severity == 'high']),
            'medium': len([i for i in self.issues if i.severity == 'medium']),
            'low': len([i for i in self.issues if i.severity == 'low']),
        }
    
    @property
    def priority_score(self):
        """Higher score = more urgent to fix"""
        return (self.severity_counts['high'] * 10 + 
                self.severity_counts['medium'] * 3 + 
                self.severity_counts['low'] * 1)


class TestAnalyzer:
    """Analyzes test files for hardening opportunities"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.results: List[TestFileAnalysis] = []
        
    def find_test_files(self) -> List[Path]:
        """Find all test files in the repository"""
        test_files = []
        
        # Common test patterns
        patterns = ['test_*.py', '*_test.py', 'test*.py']
        
        for pattern in patterns:
            test_files.extend(self.repo_path.rglob(pattern))
        
        # Deduplicate and sort
        return sorted(set(test_files))
    
    def analyze_file(self, filepath: Path) -> TestFileAnalysis:
        """Analyze a single test file"""
        analysis = TestFileAnalysis(filepath=filepath)
        
        try:
            content = filepath.read_text(encoding='utf-8')
            analysis.total_lines = len(content.splitlines())
            
            # Parse the AST
            tree = ast.parse(content, filename=str(filepath))
            
            # Analyze imports
            self._check_imports(tree, analysis)
            
            # Analyze test functions
            self._check_test_functions(tree, analysis, content)
            
            # Check for patterns in the raw content
            self._check_content_patterns(content, analysis)
            
        except Exception as e:
            analysis.issues.append(TestIssue(
                severity='high',
                category='parse_error',
                message=f"Failed to parse file: {e}"
            ))
        
        return analysis
    
    def _check_imports(self, tree: ast.AST, analysis: TestFileAnalysis):
        """Check imports for external dependencies and missing test tools"""
        external_calls = set()
        has_pytest = False
        has_mock = False
        has_unittest = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    analysis.imports.add(alias.name)
                    if 'pytest' in alias.name:
                        has_pytest = True
                    if 'mock' in alias.name or 'unittest.mock' in alias.name:
                        has_mock = True
                    if 'unittest' in alias.name:
                        has_unittest = True
                        
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    analysis.imports.add(node.module)
                    if 'pytest' in node.module:
                        has_pytest = True
                    if 'mock' in node.module:
                        has_mock = True
                    if 'unittest' in node.module:
                        has_unittest = True
        
        # Check for external dependencies without mocks
        risky_imports = {
            'requests', 'urllib', 'http.client', 'httpx',  # HTTP
            'sqlite3', 'psycopg2', 'pymongo', 'sqlalchemy',  # Databases
            'boto3', 'google.cloud', 'azure',  # Cloud services
            'smtplib', 'email',  # Email
        }
        
        found_risky = analysis.imports & risky_imports
        if found_risky and not has_mock:
            analysis.issues.append(TestIssue(
                severity='high',
                category='missing_mocks',
                message=f"External dependencies detected ({', '.join(found_risky)}) but no mock library imported. Tests may be slow or flaky."
            ))
    
    def _check_test_functions(self, tree: ast.AST, analysis: TestFileAnalysis, content: str):
        """Analyze individual test functions"""
        lines = content.splitlines()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if it's a test function
                if node.name.startswith('test_') or any(
                    isinstance(dec, ast.Name) and 'test' in dec.id.lower()
                    for dec in node.decorator_list
                ):
                    analysis.test_count += 1
                    
                    # Calculate function length
                    func_start = node.lineno
                    func_end = node.end_lineno or func_start
                    func_length = func_end - func_start + 1
                    
                    # Long test detection
                    if func_length > 50:
                        analysis.issues.append(TestIssue(
                            severity='high',
                            category='long_test',
                            message=f"Test '{node.name}' is {func_length} lines long. Consider decomposing.",
                            line_number=func_start
                        ))
                        analysis.long_tests.append({
                            'name': node.name,
                            'lines': func_length,
                            'start_line': func_start
                        })
                    elif func_length > 30:
                        analysis.issues.append(TestIssue(
                            severity='medium',
                            category='long_test',
                            message=f"Test '{node.name}' is {func_length} lines. Consider refactoring.",
                            line_number=func_start
                        ))
                    
                    # Check for poor naming
                    if len(node.name) < 10 or node.name.count('_') < 2:
                        analysis.issues.append(TestIssue(
                            severity='low',
                            category='naming',
                            message=f"Test '{node.name}' has unclear name. Use descriptive names like 'test_feature_when_condition_then_outcome'",
                            line_number=func_start
                        ))
                    
                    # Check for assertions
                    has_assert = self._has_assertions(node)
                    if not has_assert:
                        analysis.issues.append(TestIssue(
                            severity='high',
                            category='no_assertions',
                            message=f"Test '{node.name}' has no assertions. Tests without assertions don't verify anything.",
                            line_number=func_start
                        ))
                    
                    # Check for global state usage
                    if self._uses_global_state(node):
                        analysis.issues.append(TestIssue(
                            severity='high',
                            category='global_state',
                            message=f"Test '{node.name}' uses global variables. This creates test dependencies.",
                            line_number=func_start
                        ))
                    
                    # Check for time.sleep (potential flakiness)
                    if self._has_sleep_calls(node):
                        analysis.issues.append(TestIssue(
                            severity='medium',
                            category='flaky',
                            message=f"Test '{node.name}' uses time.sleep(). This makes tests slow and potentially flaky.",
                            line_number=func_start
                        ))
    
    def _check_content_patterns(self, content: str, analysis: TestFileAnalysis):
        """Check for patterns in the raw content"""
        lines = content.splitlines()
        
        # Check for hard-coded paths
        path_patterns = [
            r'["\']/(home|Users|tmp|var|etc)/[^"\']+["\']',  # Absolute paths
            r'["\'][A-Z]:\\[^"\']+["\']',  # Windows paths
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in path_patterns:
                if re.search(pattern, line):
                    analysis.issues.append(TestIssue(
                        severity='medium',
                        category='hardcoded_path',
                        message=f"Hard-coded file path detected. Use fixtures or tmp_path.",
                        line_number=i
                    ))
                    break
        
        # Check for hard-coded URLs
        url_pattern = r'https?://(?!localhost|127\.0\.0\.1|example\.com)[^\s"\')]+' 
        for i, line in enumerate(lines, 1):
            if re.search(url_pattern, line) and 'mock' not in line.lower():
                analysis.issues.append(TestIssue(
                    severity='high',
                    category='external_dependency',
                    message=f"Real URL detected without mock. This makes tests dependent on external services.",
                    line_number=i
                ))
        
        # Check for print statements (should use logging or remove)
        print_pattern = r'\bprint\s*\('
        print_count = sum(1 for line in lines if re.search(print_pattern, line))
        if print_count > 2:
            analysis.issues.append(TestIssue(
                severity='low',
                category='debug_code',
                message=f"Found {print_count} print statements. Consider removing debug code or using logging."
            ))
        
        # Check for commented out code
        commented_lines = [i for i, line in enumerate(lines, 1) 
                          if line.strip().startswith('#') and len(line.strip()) > 2]
        if len(commented_lines) > 10:
            analysis.issues.append(TestIssue(
                severity='low',
                category='commented_code',
                message=f"Many commented lines ({len(commented_lines)}). Clean up old code."
            ))
    
    def _has_assertions(self, node: ast.FunctionDef) -> bool:
        """Check if function has any assertions"""
        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                return True
            # Check for pytest assertions (assert in expression)
            if isinstance(child, ast.Expr) and isinstance(child.value, ast.Compare):
                return True
        return False
    
    def _uses_global_state(self, node: ast.FunctionDef) -> bool:
        """Check if function uses global variables"""
        for child in ast.walk(node):
            if isinstance(child, ast.Global):
                return True
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                # Check if it's modifying a potentially global variable
                if child.id.isupper() or child.id.startswith('_'):
                    return True
        return False
    
    def _has_sleep_calls(self, node: ast.FunctionDef) -> bool:
        """Check if function uses time.sleep"""
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if child.func.attr == 'sleep':
                        return True
                elif isinstance(child.func, ast.Name):
                    if child.func.id == 'sleep':
                        return True
        return False
    
    def analyze_all(self) -> List[TestFileAnalysis]:
        """Analyze all test files in the repository"""
        test_files = self.find_test_files()
        
        print(f"Found {len(test_files)} test files to analyze...")
        
        for filepath in test_files:
            print(f"  Analyzing: {filepath.relative_to(self.repo_path)}")
            analysis = self.analyze_file(filepath)
            self.results.append(analysis)
        
        # Sort by priority score
        self.results.sort(key=lambda x: x.priority_score, reverse=True)
        
        return self.results
    
    def generate_report(self, output_file: str = None):
        """Generate a detailed report"""
        report_lines = []
        
        report_lines.append("=" * 80)
        report_lines.append("TEST HARDENING ANALYSIS REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Summary statistics
        total_tests = sum(r.test_count for r in self.results)
        total_issues = sum(len(r.issues) for r in self.results)
        high_priority_files = len([r for r in self.results if r.severity_counts['high'] > 0])
        
        report_lines.append("SUMMARY")
        report_lines.append("-" * 80)
        report_lines.append(f"Total test files analyzed: {len(self.results)}")
        report_lines.append(f"Total test functions: {total_tests}")
        report_lines.append(f"Total issues found: {total_issues}")
        report_lines.append(f"High-priority files: {high_priority_files}")
        report_lines.append("")
        
        # Issue breakdown
        all_issues_by_category = {}
        for result in self.results:
            for issue in result.issues:
                all_issues_by_category.setdefault(issue.category, 0)
                all_issues_by_category[issue.category] += 1
        
        report_lines.append("ISSUES BY CATEGORY")
        report_lines.append("-" * 80)
        for category, count in sorted(all_issues_by_category.items(), key=lambda x: x[1], reverse=True):
            report_lines.append(f"  {category:30s}: {count:3d}")
        report_lines.append("")
        
        # File-by-file analysis (top 20 priority files)
        report_lines.append("TOP PRIORITY FILES TO HARDEN")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        for i, result in enumerate(self.results[:20], 1):
            if result.priority_score == 0:
                continue
                
            report_lines.append(f"\n{i}. {result.filepath.relative_to(self.repo_path)}")
            report_lines.append(f"   Priority Score: {result.priority_score} | "
                              f"Tests: {result.test_count} | "
                              f"Lines: {result.total_lines}")
            report_lines.append(f"   Issues: {result.severity_counts['high']} high, "
                              f"{result.severity_counts['medium']} medium, "
                              f"{result.severity_counts['low']} low")
            
            # Group issues by severity
            high_issues = [i for i in result.issues if i.severity == 'high']
            medium_issues = [i for i in result.issues if i.severity == 'medium']
            
            if high_issues:
                report_lines.append("\n   🔴 HIGH PRIORITY:")
                for issue in high_issues[:5]:  # Show top 5
                    line_info = f" (line {issue.line_number})" if issue.line_number else ""
                    report_lines.append(f"      • {issue.message}{line_info}")
            
            if medium_issues:
                report_lines.append("\n   🟡 MEDIUM PRIORITY:")
                for issue in medium_issues[:3]:  # Show top 3
                    line_info = f" (line {issue.line_number})" if issue.line_number else ""
                    report_lines.append(f"      • {issue.message}{line_info}")
            
            # Show long tests
            if result.long_tests:
                report_lines.append("\n   📏 LONG TESTS TO DECOMPOSE:")
                for test in result.long_tests[:3]:
                    report_lines.append(f"      • {test['name']} ({test['lines']} lines, starts at {test['start_line']})")
        
        # Files with no issues (celebrate!)
        clean_files = [r for r in self.results if r.priority_score == 0]
        if clean_files:
            report_lines.append("\n" + "=" * 80)
            report_lines.append(f"✅ CLEAN FILES ({len(clean_files)} files)")
            report_lines.append("-" * 80)
            for result in clean_files[:10]:
                report_lines.append(f"  • {result.filepath.relative_to(self.repo_path)} ({result.test_count} tests)")
        
        # Recommendations
        report_lines.append("\n" + "=" * 80)
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("-" * 80)
        report_lines.append("1. Start with the highest priority score files")
        report_lines.append("2. Focus on HIGH severity issues first")
        report_lines.append("3. Decompose long tests (>50 lines) into focused tests")
        report_lines.append("4. Mock external dependencies (HTTP, DB, file system)")
        report_lines.append("5. Remove global state and ensure test independence")
        report_lines.append("6. Add fixtures for repeated setup/teardown")
        report_lines.append("7. Replace time.sleep() with proper waits or mocks")
        report_lines.append("8. Use descriptive test names following given-when-then pattern")
        report_lines.append("")
        
        report = "\n".join(report_lines)
        
        # Output to file if specified
        if output_file:
            Path(output_file).write_text(report)
            print(f"\nReport written to: {output_file}")
        
        return report


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_analyzer.py <repo_path> [output_file]")
        print("\nExample:")
        print("  python test_analyzer.py /path/to/repo")
        print("  python test_analyzer.py /path/to/repo report.txt")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    analyzer = TestAnalyzer(repo_path)
    analyzer.analyze_all()
    report = analyzer.generate_report(output_file)
    
    if not output_file:
        print("\n" + report)


if __name__ == "__main__":
    main()
