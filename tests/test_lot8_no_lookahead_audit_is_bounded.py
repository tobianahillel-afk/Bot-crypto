from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    Path("scripts/audit_lot8_no_lookahead.py"),
    Path("src/crypto_quant_bot/audit/lookahead.py"),
    Path("src/crypto_quant_bot/audit/available_at.py"),
    Path("src/crypto_quant_bot/audit/forbidden_names.py"),
]
FORBIDDEN_TOKENS = [
    "os.walk",
    "rglob",
    "glob(\"**/*\")",
    "while True",
    "subprocess.run",
    "subprocess." + "Popen",
    "capture_" + "output=True",
    "stdout=subprocess." + "PIPE",
    "stderr=subprocess." + "PIPE",
    "os." + "_exit",
    "os.exec",
    "signal." + "alarm",
]


def test_lot8_no_lookahead_audit_uses_bounded_explicit_policy_only():
    for relative_path in FILES:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for token in FORBIDDEN_TOKENS:
            assert token not in text, f"{relative_path} contains forbidden unbounded token: {token}"
