from __future__ import annotations

import http.client
import json
import socket
import ssl
import sys
import time
import urllib.parse
from typing import Any, Optional

CHUNK_SIZE = 8 * 1024
MAX_REDIRECTS = 10
REDIRECT_STATUSES = {301, 302, 303, 307, 308}

__all__ = [
    "HttpClient",
    "HttpClientError",
    "InvalidUrlError",
    "DnsError",
    "ConnectionFailedError",
    "RequestTimeoutError",
    "TooManyRedirectsError",
    "SslError",
]


class HttpClientError(Exception):
    """Base class for all mycurl network errors."""

    exit_code = 1


class InvalidUrlError(HttpClientError):
    """Malformed URL or unsupported scheme."""

    exit_code = 3


class DnsError(HttpClientError):
    """Could not resolve the host name."""

    exit_code = 6


class ConnectionFailedError(HttpClientError):
    """Could not connect to the server (e.g. connection refused)."""

    exit_code = 7


class SslError(HttpClientError):
    """TLS/SSL handshake or certificate error."""

    exit_code = 60


class RequestTimeoutError(HttpClientError):
    """Connection or transfer timed out."""

    exit_code = 28


class TooManyRedirectsError(HttpClientError):
    """Redirect limit was exceeded."""

    exit_code = 47


class HttpClient:
    """Minimal HTTP client built only on http.client and urllib.parse.

    The response body is always consumed in small chunks (CHUNK_SIZE), so
    saving a large file via ``output`` keeps memory usage flat instead of
    loading the whole payload into RAM.
    """

    def __init__(self, verbose: bool = False, timeout: float = 10.0) -> None:
        self.verbose = verbose
        self.timeout = timeout

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[dict[str, str]] = None,
        body: Optional[Any] = None,
        output: Optional[str] = None,
        follow_redirects: bool = False,
    ) -> Optional[str]:
        """Send an HTTP request and return the response body as a string.

        When ``output`` is given the body is streamed to that file in chunks
        and ``None`` is returned. When ``follow_redirects`` is enabled the
        3xx Location responses are chased (max MAX_REDIRECTS hops).
        """
        deadline = time.monotonic() + self.timeout
        current_url = url
        current_method = method.upper()
        header_dict = {str(k): str(v) for k, v in (headers or {}).items()}
        redirect_count = 0
        conn: Optional[http.client.HTTPConnection] = None

        try:
            while True:
                if conn is not None:
                    conn.close()
                    conn = None

                parsed = urllib.parse.urlsplit(current_url)
                scheme = (parsed.scheme or "http").lower()
                host = parsed.hostname
                if not host:
                    raise InvalidUrlError(f"invalid URL: {current_url!r}")
                if scheme not in ("http", "https"):
                    raise InvalidUrlError(f"unsupported scheme: {scheme!r}")
                port = parsed.port or (443 if scheme == "https" else 80)
                path = parsed.path or "/"
                if parsed.query:
                    path = f"{path}?{parsed.query}"

                body_data = self._normalize_body(body)
                sent_headers = header_dict
                if body_data is not None and "Content-Type" not in sent_headers:
                    content_type = (
                        "application/json"
                        if isinstance(body, (dict, list)) or isinstance(body_data, bytes)
                        else "application/x-www-form-urlencoded"
                    )
                    sent_headers = {**header_dict, "Content-Type": content_type}

                if self.verbose:
                    print(f"* Connecting to {host} via {scheme.upper()}", file=sys.stderr)
                    print(f"> {current_method} {path} HTTP/1.1", file=sys.stderr)
                    print(f"> Host: {host}", file=sys.stderr)
                    for name, value in sent_headers.items():
                        print(f"> {name}: {value}", file=sys.stderr)
                    if body_data is not None:
                        print(f"> Content-Length: {len(body_data)}", file=sys.stderr)
                    print(">", file=sys.stderr)

                self._check_deadline(deadline)
                conn_cls = (
                    http.client.HTTPSConnection if scheme == "https" else http.client.HTTPConnection
                )
                conn = conn_cls(host, port, timeout=self.timeout)
                conn.request(current_method, path, body=body_data, headers=sent_headers)
                resp = conn.getresponse()

                if self.verbose:
                    print(f"< HTTP/1.1 {resp.status} {resp.reason}", file=sys.stderr)
                    for name, value in resp.getheaders():
                        print(f"< {name}: {value}", file=sys.stderr)
                    print("<", file=sys.stderr)

                if follow_redirects and resp.status in REDIRECT_STATUSES:
                    location = resp.getheader("Location")
                    if location:
                        if redirect_count >= MAX_REDIRECTS:
                            raise TooManyRedirectsError(
                                f"maximum ({MAX_REDIRECTS}) redirects followed"
                            )
                        redirect_count += 1
                        if resp.status == 303:
                            current_method = "GET"
                            body = None
                        current_url = urllib.parse.urljoin(current_url, location)
                        if self.verbose:
                            print(f"* Redirect #{redirect_count} -> {current_url}", file=sys.stderr)
                        continue

                if output is not None:
                    with open(output, "wb") as fh:
                        for chunk in self._read_chunks(resp, deadline):
                            fh.write(chunk)
                    return None

                parts: list[bytes] = []
                for chunk in self._read_chunks(resp, deadline):
                    parts.append(chunk)
                return b"".join(parts).decode("utf-8", errors="replace")
        except HttpClientError:
            raise
        except TimeoutError as exc:
            raise RequestTimeoutError(
                f"operation timed out after {self.timeout:.1f} seconds"
            ) from exc
        except ssl.SSLError as exc:
            raise SslError(f"SSL error: {exc}") from exc
        except socket.gaierror as exc:
            raise DnsError(f"could not resolve host: {self._host(current_url)}") from exc
        except ConnectionRefusedError as exc:
            host, port = self._host_port(current_url)
            raise ConnectionFailedError(f"failed to connect to {host}:{port}: {exc}") from exc
        except OSError as exc:
            host, port = self._host_port(current_url)
            raise ConnectionFailedError(f"connection to {host}:{port} failed: {exc}") from exc
        finally:
            if conn is not None:
                conn.close()

    @staticmethod
    def _normalize_body(body: Any) -> Optional[Any]:
        if isinstance(body, (dict, list)):
            return json.dumps(body)
        if isinstance(body, bytes):
            return body
        if body is None:
            return None
        return str(body)

    def _check_deadline(self, deadline: float) -> None:
        if time.monotonic() > deadline:
            raise RequestTimeoutError(
                f"operation timed out after {self.timeout:.1f} seconds"
            )

    def _read_chunks(self, resp, deadline: float):
        while True:
            chunk = resp.read(CHUNK_SIZE)
            if not chunk:
                break
            self._check_deadline(deadline)
            yield chunk

    @staticmethod
    def _host(url: str) -> str:
        return urllib.parse.urlsplit(url).hostname or "unknown"

    @staticmethod
    def _host_port(url: str) -> tuple[str, int]:
        parsed = urllib.parse.urlsplit(url)
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        return parsed.hostname or "unknown", port