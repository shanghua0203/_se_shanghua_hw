import pytest

from mycurl.cli import build_parser, main, parse_headers
from mycurl.client import HttpClient, HttpClientError


def test_default_values():
    args = build_parser().parse_args(["http://example.com/"])
    assert args.url == "http://example.com/"
    assert args.request == "GET"
    assert args.headers is None
    assert args.data is None
    assert args.output is None
    assert args.verbose is False
    assert args.max_time == 30.0
    assert args.location is False


def test_short_and_long_option_aliases():
    short = build_parser().parse_args(
        ["-X", "PUT", "-H", "A: 1", "-d", "x", "-o", "f.txt", "-v", "-m", "1.5", "-L",
         "http://example.com/"]
    )
    long = build_parser().parse_args(
        [
            "--request", "PUT",
            "--header", "A: 1",
            "--data", "x",
            "--output", "f.txt",
            "--verbose",
            "--max-time", "1.5",
            "--location",
            "http://example.com/",
        ]
    )
    for args in (short, long):
        assert args.request == "PUT"
        assert args.headers == ["A: 1"]
        assert args.data == "x"
        assert args.output == "f.txt"
        assert args.verbose is True
        assert args.max_time == 1.5
        assert args.location is True


def test_repeated_headers_are_collected():
    args = build_parser().parse_args(
        ["-H", "A: 1", "-H", "B: 2", "http://example.com/"]
    )
    assert args.headers == ["A: 1", "B: 2"]


def test_headers_parsed_into_dict():
    headers = parse_headers(["A: 1", "B: 2", "C:  x  y "])
    assert isinstance(headers, dict)
    assert headers == {"A": "1", "B": "2", "C": "x  y"}


def test_parse_headers_with_none_returns_empty_dict():
    assert parse_headers(None) == {}


def test_invalid_header_returns_exit_code_2(capsys):
    code = main(["-H", "BAD-HEADER", "http://example.com/"])
    assert code == 2
    assert "invalid header" in capsys.readouterr().err


def test_missing_url_exits_with_code_2():
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code == 2


def test_main_performs_request_and_prints_body(monkeypatch, capsys):
    class FakeClient:
        def __init__(self, verbose=False, timeout=30.0):
            assert verbose is True
            assert timeout == 30.0

        def request(self, method, url, headers, body, output, follow_redirects=False):
            assert method == "POST"
            assert url == "http://example.com/"
            assert headers == {"A": "1"}
            assert body == "hello"
            assert output is None
            return "response-body"

    monkeypatch.setattr("mycurl.cli.HttpClient", FakeClient)
    code = main(["-X", "POST", "-H", "A: 1", "-d", "hello", "-v", "http://example.com/"])

    assert code == 0
    assert capsys.readouterr().out == "response-body\n"


def test_main_output_file_does_not_print_body(monkeypatch, capsys):
    class FakeClient:
        def __init__(self, verbose=False, timeout=30.0):
            pass

        def request(self, method, url, headers, body, output, follow_redirects=False):
            return "file-body"

    monkeypatch.setattr("mycurl.cli.HttpClient", FakeClient)
    code = main(["-o", "out.txt", "http://example.com/"])

    assert code == 0
    assert capsys.readouterr().out == ""


def test_data_implies_post_method(monkeypatch, capsys):
    captured = {}

    class FakeClient:
        def __init__(self, verbose=False, timeout=30.0):
            pass

        def request(self, method, url, headers, body, output, follow_redirects=False):
            captured["method"] = method
            return "ok"

    monkeypatch.setattr("mycurl.cli.HttpClient", FakeClient)
    code = main(["-d", "name=test", "http://example.com/"])

    assert code == 0
    assert captured["method"] == "POST"


def test_explicit_request_overrides_data_implied_post(monkeypatch, capsys):
    captured = {}

    class FakeClient:
        def __init__(self, verbose=False, timeout=30.0):
            pass

        def request(self, method, url, headers, body, output, follow_redirects=False):
            captured["method"] = method
            return "ok"

    monkeypatch.setattr("mycurl.cli.HttpClient", FakeClient)
    code = main(["-X", "PUT", "-d", "name=test", "http://example.com/"])

    assert code == 0
    assert captured["method"] == "PUT"


def test_location_flag_sets_follow_redirects(monkeypatch, capsys):
    captured = {}

    class FakeClient:
        def __init__(self, verbose=False, timeout=30.0):
            pass

        def request(self, method, url, headers, body, output, follow_redirects=False):
            captured["follow_redirects"] = follow_redirects
            return "ok"

    monkeypatch.setattr("mycurl.cli.HttpClient", FakeClient)
    code = main(["-L", "http://example.com/"])

    assert code == 0
    assert captured["follow_redirects"] is True


def test_max_time_flag_and_default(monkeypatch, capsys):
    captured = []

    class FakeClient:
        def __init__(self, verbose=False, timeout=30.0):
            captured.append(timeout)

        def request(self, method, url, headers, body, output, follow_redirects=False):
            return "ok"

    monkeypatch.setattr("mycurl.cli.HttpClient", FakeClient)
    code = main(["http://example.com/"])
    assert code == 0
    assert captured == [30.0]

    code = main(["-m", "1.5", "http://example.com/"])
    assert code == 0
    assert captured == [30.0, 1.5]


def test_main_returns_1_on_http_error(monkeypatch, capsys):
    def failing_request(
        self, method, url, headers=None, body=None, output=None, follow_redirects=False
    ):
        raise HttpClientError("boom")

    monkeypatch.setattr(HttpClient, "request", failing_request)
    code = main(["http://example.com/"])

    assert code == 1
    assert "boom" in capsys.readouterr().err