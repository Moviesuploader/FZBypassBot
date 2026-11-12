import asyncio
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from FZBypass.bypass import checker, ddl
from FZBypass.core.exceptions import DDLException


def test_shrinkme_click_routes_to_dedicated_handler(monkeypatch):
    calls = []

    async def fake_shrinkme(url):
        calls.append(url)
        return "https://destination.example/file"

    monkeypatch.setattr(checker, "shrinkme", fake_shrinkme)
    result = asyncio.run(
        checker.direct_link_checker("https://shrinkme.click/dtRhBl8X", onlylink=True)
    )

    assert result == "https://destination.example/file"
    assert calls == ["https://shrinkme.click/dtRhBl8X"]


def test_shrinkme_resolver_posts_go_form_and_returns_external_target():
    form_html = """
    <html><body>
      <form id="go-link" action="/links/go">
        <input type="hidden" name="_csrfToken" value="csrf-value">
        <input type="hidden" name="ad_form_data" value="encoded-value">
      </form>
      <script>var counter_value = 1;</script>
    </body></html>
    """
    page = SimpleNamespace(
        text=form_html,
        url="https://en.mrproblogger.com/dtRhBl8X",
        status_code=200,
        request=SimpleNamespace(headers={"User-Agent": "test-agent"}),
    )
    result = SimpleNamespace(
        status_code=200,
        json=lambda: {"url": "https://destination.example/real-file"},
    )
    session = SimpleNamespace(
        get=lambda *args, **kwargs: page,
        post=lambda *args, **kwargs: result,
        close=lambda: None,
    )

    with patch.object(ddl, "Session", return_value=session), patch.object(ddl, "sleep"):
        final = ddl._shrinkme_sync("https://shrinkme.click/dtRhBl8X")

    assert final == "https://destination.example/real-file"


@pytest.mark.parametrize(
    "destination",
    [
        "https://en.mrproblogger.com/another-hop",
        "https://themezon.net/link.php?link=abc",
        "https://shrinkme.click/another-hop",
        "javascript:alert(1)",
        "",
    ],
)
def test_shrinkme_does_not_accept_intermediate_or_invalid_destinations(destination):
    form_html = """
    <html><body><form id="go-link" action="/links/go">
      <input type="hidden" name="_csrfToken" value="csrf-value">
    </form><script>var counter_value = 1;</script></body></html>
    """
    page = SimpleNamespace(
        text=form_html,
        url="https://en.mrproblogger.com/dtRhBl8X",
        status_code=200,
        request=SimpleNamespace(headers={"User-Agent": "test-agent"}),
    )
    result = SimpleNamespace(status_code=200, json=lambda: {"url": destination})
    session = SimpleNamespace(
        get=lambda *args, **kwargs: page,
        post=lambda *args, **kwargs: result,
        close=lambda: None,
    )

    with patch.object(ddl, "Session", return_value=session), patch.object(ddl, "sleep"):
        with pytest.raises(DDLException):
            ddl._shrinkme_sync("https://shrinkme.click/dtRhBl8X")


def test_shrinkme_rejects_invalid_alias():
    with pytest.raises(DDLException):
        ddl._shrinkme_sync("https://shrinkme.click/")
