from __future__ import annotations

import argparse
import sys
from typing import Optional

from .client import HttpClient, HttpClientError

__all__ = ["build_parser", "parse_headers", "main"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mycurl",
        description="A minimal curl-like HTTP client built on http.client.",
    )
    parser.add_argument("url", help="target URL to request")
    parser.add_argument(
        "-X",
        "--request",
        default="GET",
        help="HTTP method to use (default: GET)",
    )
    parser.add_argument(
        "-H",
        "--header",
        action="append",
        dest="headers",
        metavar="HEADER",
        help="custom header in 'Name: value' form, repeatable",
    )
    parser.add_argument(
        "-d",
        "--data",
        help="data to send as the request body",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="write the response body to this file instead of stdout",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print detailed request/response headers",
    )
    return parser


def parse_headers(lines: Optional[list[str]]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for line in lines or []:
        if ":" not in line:
            raise ValueError(f"invalid header (missing ':'): {line!r}")
        name, value = line.split(":", 1)
        headers[name.strip()] = value.strip()
    return headers


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        headers = parse_headers(args.headers)
    except ValueError as exc:
        print(f"mycurl: error: {exc}", file=sys.stderr)
        return 2

    client = HttpClient(verbose=args.verbose)
    method = "POST" if args.data is not None and args.request == "GET" else args.request
    try:
        body = client.request(
            method,
            args.url,
            headers=headers,
            body=args.data,
            output=args.output,
        )
    except HttpClientError as exc:
        print(f"mycurl: error: {exc}", file=sys.stderr)
        return 1

    if args.output is None:
        print(body)
    return 0