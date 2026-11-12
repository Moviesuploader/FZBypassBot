import asyncio

import pytest

from FZBypass.bypass import checker, ddl
from FZBypass.core.exceptions import DDLException


@pytest.mark.parametrize("url", ["https://exeygo.com/oJE4X", "https://www.exeygo.com/oJE4X"])
def test_exeygo_is_recognized_but_interactive_turnstile_is_not_bypassed(url):
    with pytest.raises(DDLException, match="interactive Cloudflare Turnstile"):
        asyncio.run(checker.direct_link_checker(url, onlylink=True))


@pytest.mark.parametrize("url", ["https://cuttty.com/0U4XsB", "https://www.cuttty.com/0U4XsB"])
def test_cuttty_is_recognized_but_interactive_turnstile_is_not_bypassed(url):
    with pytest.raises(DDLException, match="interactive Cloudflare Turnstile"):
        asyncio.run(checker.direct_link_checker(url, onlylink=True))


def test_gplinks_routes_to_bounded_form_handler(monkeypatch):
    called = {}

    async def fake_transcript(url, domain, referer, wait):
        called.update(url=url, domain=domain, referer=referer, wait=wait)
        return "https://destination.example/file"

    monkeypatch.setattr(checker, "transcript", fake_transcript)
    result = asyncio.run(checker.direct_link_checker("https://gplinks.co/OblC", onlylink=True))

    assert result == "https://destination.example/file"
    assert called == {
        "url": "https://gplinks.co/OblC",
        "domain": "https://gplinks.co/",
        "referer": "https://gplinks.co/",
        "wait": 5,
    }


def test_transcript_rejects_turnstile_before_submitting_form(monkeypatch):
    class FakeResponse:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def text(self):
            return '<div class="cf-turnstile" data-sitekey="test"></div>'

        def raise_for_status(self):
            pass

    class FakeSession:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        def get(self, *args, **kwargs):
            return FakeResponse()

        def post(self, *args, **kwargs):
            raise AssertionError("Must not submit a Turnstile form without user verification")

    monkeypatch.setattr(ddl, "ClientSession", FakeSession)
    with pytest.raises(DDLException, match="interactive Cloudflare Turnstile"):
        asyncio.run(checker.transcript("https://gplinks.co/OblC", "https://gplinks.co/", "https://gplinks.co/", 0))
