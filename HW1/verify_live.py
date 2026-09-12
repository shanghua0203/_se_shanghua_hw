from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
PYTHON = str(PROJECT_ROOT / ".venv" / "bin" / "python")
CASE_WIDTH = 60


def run_case(name: str, args: list[str], check) -> bool:
    print("─" * CASE_WIDTH)
    print(f"測試：{name}")
    print(f"指令：python -m mycurl {' '.join(args)}")

    start = time.monotonic()
    result = subprocess.run(
        [PYTHON, "-m", "mycurl", *args],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=60,
    )
    elapsed = time.monotonic() - start

    print(f"Exit Code：{result.returncode}    耗時：{elapsed:.2f} 秒")
    if result.stdout:
        preview = result.stdout if len(result.stdout) <= 500 else result.stdout[:500] + "..."
        print(f"stdout（前 500 字元）：\n{preview}")
    if result.stderr:
        print(f"stderr：\n{result.stderr.strip()}")

    try:
        check(result)
        print("結果：PASS")
        print("─" * CASE_WIDTH)
        return True
    except AssertionError as exc:
        print(f"結果：FAIL（{exc}）")
        print("─" * CASE_WIDTH)
        return False


def test_one_get() -> bool:
    def check(result: subprocess.CompletedProcess) -> None:
        assert result.returncode == 0, f"exit code {result.returncode}"
        payload = json.loads(result.stdout)
        assert isinstance(payload, dict), "stdout 不是 JSON 物件"
        assert "url" in payload, "回應缺少 'url' 欄位"
        assert "httpbin.org/get" in payload["url"], "回應不是 httpbin.org/get"

    return run_case("一：GET https://httpbin.org/get（確認拿到 JSON）", ["https://httpbin.org/get"], check)


def test_two_post() -> bool:
    def check(result: subprocess.CompletedProcess) -> None:
        assert result.returncode == 0, f"exit code {result.returncode}"
        payload = json.loads(result.stdout)
        assert payload.get("form") == {"status": "success"}, "伺服器未收到 status=success"

    return run_case(
        "二：POST -d status=success（確認伺服器收到資料）",
        ["-X", "POST", "-d", "status=success", "https://httpbin.org/post"],
        check,
    )


def test_three_bad_url() -> bool:
    def check(result: subprocess.CompletedProcess) -> None:
        assert result.returncode != 0, "不存在網址竟回傳 0"
        assert "mycurl: error:" in result.stderr, "stderr 沒有優雅的錯誤訊息"
        assert "Traceback" not in result.stderr, "程式噴出 Traceback"

    return run_case(
        "三：隨機不存在的網址（應優雅報錯）",
        ["http://mycurl-nonexistent-8f3a9.invalid/"],
        check,
    )


def main() -> int:
    tests = [test_one_get, test_two_post, test_three_bad_url]
    failures = 0
    for test in tests:
        if not test():
            failures += 1
    print()
    print(f"共 {len(tests)} 項，失敗 {failures} 項")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())