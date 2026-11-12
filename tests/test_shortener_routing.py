import asyncio

import pytest

from FZBypass.bypass import checker
from FZBypass.core.exceptions import DDLException


def test_easysky_routes_once_to_easysky_transcript(monkeypatch):
    calls = []

    async def fake_transcript(*args):
        calls.append(args)
        return "https://destination.example/file"

    monkeypatch.setattr(checker, "transcript", fake_transcript)
    result = asyncio.run(checker.direct_link_checker("https://m.easysky.in/abc", onlylink=True))

    assert result == "https://destination.example/file"
    assert len(calls) == 1
    assert calls[0][1] == "https://techy.veganab.co/"


def test_linkbnao_has_its_own_handler(monkeypatch):
    calls = []

    async def fake_transcript(*args):
        calls.append(args)
        return "https://destination.example/file"

    monkeypatch.setattr(checker, "transcript", fake_transcript)
    result = asyncio.run(checker.direct_link_checker("https://vip.linkbnao.com/abc", onlylink=True))

    assert result == "https://destination.example/file"
    assert calls[0][1] == "https://vip.linkbnao.com/"


def test_v2_kpslink_handler_is_not_shadowed(monkeypatch):
    calls = []

    async def fake_transcript(*args):
        calls.append(args)
        return "https://destination.example/file"

    monkeypatch.setattr(checker, "transcript", fake_transcript)
    result = asyncio.run(checker.direct_link_checker("https://v2.kpslink.in/abc", onlylink=True))

    assert result == "https://destination.example/file"
    assert calls[0][1] == "https://v2.kpslink.in/"


def test_share_link_multi_tld_detection():
    assert checker.is_share_link("https://new.gdtot.zip/file-id")
    assert checker.is_share_link("https://filepress.store/abc")
    assert checker.is_excep_link("https://new.gdtot.zip/file-id")


def test_rejects_non_http_urls():
    with pytest.raises(DDLException):
        asyncio.run(checker.direct_link_checker("javascript:alert(1)"))


def test_rejects_urls_without_hostname():
    with pytest.raises(DDLException):
        asyncio.run(checker.direct_link_checker("https:///missing-host"))


def test_try2link_parked_domain_is_not_routed():
    with pytest.raises(DDLException):
        asyncio.run(checker.direct_link_checker("https://try2link.com/example", onlylink=True))


def test_share_link_rejects_lookalike_domain():
    assert not checker.is_share_link("https://notgdtot.example/file")
