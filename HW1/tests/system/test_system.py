import http.server
import subprocess
import sys
import threading
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON = str(PROJECT_ROOT / ".venv" / "bin" / "python")

SERVER_RESPONSE = "OK from test server"


class RecordingHandler(http.server.BaseHTTPRequestHandler):
    requests = []

    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()

    def do_PUT(self):
        self._handle()

    def do_DELETE(self):
        self._handle()

    def _handle(self):
        length = int(self.headers.get("Content-Length") or 0)
        payload = self.rfile.read(length) if length else b""
        self.__class__.requests.append(
            {
                "method": self.command,
                "path": self.path,
                "headers": dict(self.headers),
                "body": payload.decode("utf-8", errors="replace"),
            }
        )
        body = SERVER_RESPONSE.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture
def server():
    RecordingHandler.requests = []
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), RecordingHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{httpd.server_address[1]}"
    yield base_url
    httpd.shutdown()
    httpd.server_close()


def run_mycurl(base_url, *extra_args, cwd=None):
    return subprocess.run(
        [PYTHON, "-m", "mycurl", *extra_args, base_url],
        capture_output=True,
        text=True,
        cwd=cwd or PROJECT_ROOT,
    )


def test_case1_basic_get(server):
    result = run_mycurl(f"{server}/hello")

    assert result.returncode == 0
    assert result.stdout == f"{SERVER_RESPONSE}\n"

    record = RecordingHandler.requests[0]
    assert record["method"] == "GET"
    assert record["path"] == "/hello"


def test_case2_post_payload(server):
    result = run_mycurl(f"{server}/submit", "-d", "name=test")

    assert result.returncode == 0
    assert result.stdout == f"{SERVER_RESPONSE}\n"

    record = RecordingHandler.requests[0]
    assert record["method"] == "POST"
    assert record["body"] == "name=test"
    assert record["headers"]["Content-Type"].startswith(
        "application/x-www-form-urlencoded"
    )


def test_case3_file_output(server, tmp_path):
    output_file = tmp_path / "output.txt"
    result = run_mycurl(f"{server}/file", "-o", str(output_file))

    assert result.returncode == 0
    assert result.stdout == ""
    assert output_file.read_text(encoding="utf-8") == SERVER_RESPONSE


def test_case4_verbose(server):
    result = run_mycurl(f"{server}/verbose", "-v")

    assert result.returncode == 0
    assert result.stdout == f"{SERVER_RESPONSE}\n"

    stderr_lines = result.stderr.splitlines()
    assert any(line.startswith(">") for line in stderr_lines)
    assert any(line.startswith("<") for line in stderr_lines)
    assert "> GET /verbose HTTP/1.1" in result.stderr
    assert "< HTTP/1.1 200 OK" in result.stderr