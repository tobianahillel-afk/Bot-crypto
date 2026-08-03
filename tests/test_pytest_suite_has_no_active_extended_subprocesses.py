import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"

FORBIDDEN_ACTIVE_SNIPPETS = [
    "python -m pytest",
    "validate_all_until_lot",
    "run_required_chain_until_lot",
    "diagnose_exact_chain_until_lot10.py",
    "diagnose_lot8_no_lookahead_after_chain.py",
    "diagnose_lot7_build_after_chain.py",
]
ALLOWED_ULTRA_SHORT_SUBPROCESS_TESTS: set[str] = set()


def _constant_text(node: ast.AST) -> str:
    if isinstance(node, ast.Constant):
        return str(node.value)
    if isinstance(node, ast.JoinedStr):
        return "".join(_constant_text(value) for value in node.values)
    if isinstance(node, ast.List | ast.Tuple | ast.Set):
        return " ".join(_constant_text(value) for value in node.elts)
    if isinstance(node, ast.Dict):
        return " ".join(_constant_text(key) + " " + _constant_text(value) for key, value in zip(node.keys, node.values))
    return ""


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def test_pytest_tests_do_not_launch_active_extended_subprocesses():
    offenders: list[str] = []
    for path in sorted(TESTS.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node.func)
            if name not in {"subprocess." + "run", "subprocess." + "Popen", "subprocess." + "call"}:
                continue
            relative = path.relative_to(ROOT).as_posix()
            if relative not in ALLOWED_ULTRA_SHORT_SUBPROCESS_TESTS:
                offenders.append(f"{relative}:{node.lineno}:{name}")
                continue
            payload = " ".join(_constant_text(arg) for arg in node.args)
            payload += " " + " ".join(_constant_text(keyword.value) for keyword in node.keywords)
            for snippet in FORBIDDEN_ACTIVE_SNIPPETS:
                if snippet in payload:
                    offenders.append(f"{relative}:{node.lineno}:{name}:{snippet}")
    assert offenders == []


def test_pytest_tests_do_not_import_subprocess_for_active_execution():
    offenders: list[str] = []
    for path in sorted(TESTS.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "subprocess":
                        offenders.append(f"{path.relative_to(ROOT).as_posix()}:{node.lineno}:import subprocess")
            elif isinstance(node, ast.ImportFrom) and node.module == "subprocess":
                offenders.append(f"{path.relative_to(ROOT).as_posix()}:{node.lineno}:from subprocess")
    assert offenders == []
