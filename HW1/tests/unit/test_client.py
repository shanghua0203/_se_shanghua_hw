import socket
import ssl
from unittest import mock

import pytest

from mycurl import client as client_module
from mycurl.client import (
    ConnectionFailedError,
    DnsError,
    HttpClient,
    HttpClientError,
    RequestTimeoutError,
    SslError,
    TooManyRedirectsError,
)


class FakeResponse:
    def __init__(self, status=200, reason="OK", headers=None, body=b""):
        self.status = status
        self.reason = reason
        self._headers = headers or [("Content-Type", "text/plain")]
        self._body = body

    def read(self, amt=-1):
        if not self._body:
            return b""
        data, self._body = self._body, b""
        return data

    def getheaders(self):
        return self._headers

    def getheader(self, name, default=None):
        for key, value in self._headers:
            if key.lower() == name.lower():
                return value
        return default


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

    assert result is None
    assert out_path.read_bytes() == b"hello world"


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


class RecordingResponse:
    def __init__(self, data):
        self.data = data
        self.status = 200
        self.reason = "OK"
        self.read_sizes = []

    def read(self, amt=-1):
        self.read_sizes.append(amt)
        if not self.data:
            return b""
        chunk, self.data = self.data[:amt], self.data[amt:]
        return chunk

    def getheaders(self):
        return [("Content-Type", "application/octet-stream")]

    def getheader(self, name, default=None):
        return default

    def close(self):
        pass


def test_body_read_in_chunks(fake_conn):
    conn, patched_http, patched_https = fake_conn
    response = RecordingResponse(b"a" * (client_module.CHUNK_SIZE * 3))
    conn.getresponse.return_value = response

    HttpClient(timeout=5.0).request("GET", "http://example.com/big")

    assert response.read_sizes == [client_module.CHUNK_SIZE] * 4


def test_timeout_passed_to_connection(fake_conn):
    conn, patched_http, patched_https = fake_conn

    HttpClient(timeout=12.5).request("GET", "http://example.com/")

    patched_http.assert_called_once_with("example.com", 80, timeout=12.5)


def test_timeout_error_maps_to_exit_code_28(fake_conn):
    conn, patched_http, patched_https = fake_conn
    conn.request.side_effect = TimeoutError("timed out")

    with pytest.raises(RequestTimeoutError) as exc_info:
        HttpClient().request("GET", "http://example.com/")

    assert exc_info.value.exit_code == 28


def test_dns_error_maps_to_exit_code_6(fake_conn):
    conn, patched_http, patched_https = fake_conn
    conn.request.side_effect = socket.gaierror("getaddrinfo failed")

    with pytest.raises(DnsError) as exc_info:
        HttpClient().request("GET", "http://no-such-host.example/")

    assert exc_info.value.exit_code == 6
    assert "no-such-host.example" in str(exc_info.value)


def test_connection_refused_maps_to_exit_code_7(fake_conn):
    conn, patched_http, patched_https = fake_conn
    conn.request.side_effect = ConnectionRefusedError("refused")

    with pytest.raises(ConnectionFailedError) as exc_info:
        HttpClient().request("GET", "https://example.com:9999/")

    assert exc_info.value.exit_code == 7


def test_ssl_error_maps_to_ssl_exit_code(fake_conn):
    conn, patched_http, patched_https = fake_conn
    conn.request.side_effect = ssl.SSLError("certificate verify failed")

    with pytest.raises(SslError) as exc_info:
        HttpClient().request("GET", "https://example.com/")

    assert exc_info.value.exit_code == 60
    assert "certificate verify failed" in str(exc_info.value)


def test_single_redirect_followed(fake_conn):
    conn, patched_http, patched_https = fake_conn
    conn.getresponse.side_effect = [
        FakeResponse(
            status=302,
            reason="Found",
            headers=[("Location", "/final")],
            body=b"",
        ),
        FakeResponse(status=200, reason="OK", body=b"done"),
    ]

    result = HttpClient().request(
        "GET", "http://example.com/start", follow_redirects=True
    )

    assert result == "done"
    paths = [call.args[1] for call in conn.request.call_args_list]
    assert paths == ["/start", "/final"]


def test_too_many_redirects_maps_to_exit_code_47(fake_conn):
    conn, patched_http, patched_https = fake_conn
    conn.getresponse.return_value = FakeResponse(
        status=302,
        reason="Found",
        headers=[("Location", "/loop")],
        body=b"",
    )

    with pytest.raises(TooManyRedirectsError) as exc_info:
        HttpClient().request(
            "GET", "http://example.com/start", follow_redirects=True
        )

    assert exc_info.value.exit_code == 47
    assert "10" in str(exc_info.value)


def test_redirect_without_flag_is_not_followed(fake_conn):
    conn, patched_http, patched_https = fake_conn
    conn.getresponse.return_value = FakeResponse(
        status=302,
        reason="Found",
        headers=[("Location", "/final")],
        body=b"",
    )

    result = HttpClient().request("GET", "http://example.com/start")

    assert result == ""
    assert len(conn.request.call_args_list) == 1