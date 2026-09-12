from unittest import mock

import pytest

from mycurl.client import HttpClient, HttpClientError


class FakeResponse:
    def __init__(self, status=200, reason="OK", headers=None, body=b""):
        self.status = status
        self.reason = reason
        self._headers = headers or [("Content-Type", "text/plain")]
        self._body = body

    def read(self):
        return self._body

    def getheaders(self):
        return self._headers


@pytest.fixture
def fake_conn():
    conn = mock.MagicMock()
    conn.getresponse.return_value = FakeResponse(body=b"hello world")
    with mock.patch("http.client.HTTPConnection", return_value=conn) as patched_http, mock.patch(
        "http.client.HTTPSConnection", return_value=conn
    ) as patched_https:
        yield conn, patched_http, patched_https


def test_get_request_success(fake_conn):
    conn, patched_http, patched_https = fake_conn
    client = HttpClient()
    result = client.request("GET", "http://example.com/path?a=1&b=2")

    assert result == "hello world"
    patched_http.assert_called_once_with("example.com", 80, timeout=10.0)
    conn.request.assert_called_once_with(
        "GET", "/path?a=1&b=2", body=None, headers={}
    )
    conn.getresponse.assert_called_once()


def test_put_and_delete_methods(fake_conn):
    conn, patched_http, patched_https = fake_conn
    client = HttpClient()

    client.request("PUT", "http://example.com/resource")
    conn.request.assert_called_with("PUT", "/resource", body=None, headers={})

    client.request("DELETE", "http://example.com/resource")
    conn.request.assert_called_with("DELETE", "/resource", body=None, headers={})


def test_post_with_headers_and_body(fake_conn):
    conn, patched_http, patched_https = fake_conn
    client = HttpClient()
    result = client.request(
        "POST",
        "https://example.com/submit",
        headers={"Content-Type": "application/json", "X-Custom": "abc"},
        body='{"name": "test"}',
    )

    assert result == "hello world"
    conn.request.assert_called_once_with(
        "POST",
        "/submit",
        body='{"name": "test"}',
        headers={"Content-Type": "application/json", "X-Custom": "abc"},
    )


def test_dict_body_serialized_to_json(fake_conn):
    conn, patched_http, patched_https = fake_conn
    client = HttpClient()
    client.request("POST", "http://example.com/api", body={"a": 1})

    conn.request.assert_called_once_with(
        "POST",
        "/api",
        body='{"a": 1}',
        headers={"Content-Type": "application/json"},
    )


def test_connection_failure_raises_error(fake_conn):
    conn, patched_http, patched_https = fake_conn
    conn.request.side_effect = ConnectionRefusedError("connection refused")
    client = HttpClient()

    with pytest.raises(HttpClientError, match="connection refused"):
        client.request("GET", "http://example.com/")


def test_invalid_url_raises_error():
    client = HttpClient()
    with pytest.raises(HttpClientError):
        client.request("GET", "not-a-url")


def test_output_saves_response_to_file(fake_conn, tmp_path):
    conn, patched_http, patched_https = fake_conn
    out_path = tmp_path / "out.txt"
    client = HttpClient()

    result = client.request("GET", "http://example.com/", output=str(out_path))

    assert result == "hello world"
    assert out_path.read_text(encoding="utf-8") == "hello world"


def test_verbose_outputs_headers_to_stderr(fake_conn, capsys):
    conn, patched_http, patched_https = fake_conn
    conn.getresponse.return_value = FakeResponse(
        body=b"data",
        headers=[("Content-Type", "text/plain"), ("X-Server", "test")],
    )
    client = HttpClient(verbose=True)
    client.request("GET", "http://example.com/")

    captured = capsys.readouterr()
    assert "> GET / HTTP/1.1" in captured.err
    assert "< HTTP/1.1 200 OK" in captured.err
    assert "< X-Server: test" in captured.err
    assert captured.out == ""