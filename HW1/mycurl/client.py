from __future__ import annotations

import http.client
import json
import sys
import urllib.parse
from typing import Any, Optional

__all__ = ["HttpClient", "HttpClientError"]


class HttpClientError(Exception):
    """Raised when an HTTP request cannot be completed."""


class HttpResponse:
    """Lightweight container for the parsed response."""

    def __init__(self, status: int, reason: str, headers: list[tuple[str, str]], body: bytes) -> None:
        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")


class HttpClient:
    """Minimal HTTP client built only on http.client and urllib.parse."""

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
    ) -> str:
        """Send an HTTP request and return the response body as a string.

        If ``output`` is given, the response body is also written to that file.
        Verbose mode dumps connection details and raw headers to ``stderr``.
        """
        parsed = urllib.parse.urlsplit(url)
        scheme = (parsed.scheme or "http").lower()
        host = parsed.hostname
        if not host:
            raise HttpClientError(f"invalid URL: {url!r}")
        if scheme not in ("http", "https"):
            raise HttpClientError(f"unsupported scheme: {scheme!r}")

        port = parsed.port or (443 if scheme == "https" else 80)
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        if isinstance(body, (dict, list)):
            body_data = json.dumps(body)
        elif isinstance(body, bytes):
            body_data = body
        elif body is None:
            body_data = None
        else:
            body_data = str(body)

        header_dict = {str(k): str(v) for k, v in (headers or {}).items()}
        if body_data is not None and "Content-Type" not in header_dict:
            header_dict["Content-Type"] = (
                "application/json" if isinstance(body, (dict, list)) or isinstance(body_data, bytes)
                else "application/x-www-form-urlencoded"
            )

        if self.verbose:
            print(f"* Connecting to {host} via {scheme.upper()}", file=sys.stderr)
            print(f"> {method.upper()} {path} HTTP/1.1", file=sys.stderr)
            print(f"> Host: {host}", file=sys.stderr)
            for name, value in header_dict.items():
                print(f"> {name}: {value}", file=sys.stderr)
            if body_data is not None:
                print(f"> Content-Length: {len(body_data)}", file=sys.stderr)
            print(">", file=sys.stderr)

        connection_cls = (
            http.client.HTTPSConnection if scheme == "https" else http.client.HTTPConnection
        )
        conn: Optional[http.client.HTTPConnection] = None
        try:
            conn = connection_cls(host, port, timeout=self.timeout)
            conn.request(method.upper(), path, body=body_data, headers=header_dict)
            resp = conn.getresponse()

            if self.verbose:
                print(f"< HTTP/1.1 {resp.status} {resp.reason}", file=sys.stderr)
                for name, value in resp.getheaders():
                    print(f"< {name}: {value}", file=sys.stderr)
                print("<", file=sys.stderr)

            response = HttpResponse(resp.status, resp.reason, resp.getheaders(), resp.read())
            if output is not None:
                with open(output, "w", encoding="utf-8") as fh:
                    fh.write(response.text)
            return response.text
        except HttpClientError:
            raise
        except OSError as exc:
            raise HttpClientError(f"connection to {host}:{port} failed: {exc}") from exc
        finally:
            if conn is not None:
                conn.close()