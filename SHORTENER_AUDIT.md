# Shortener audit — 12 November 2026

This file separates code support from live service verification. A handler in the
repository is not proof that the third-party site still accepts bypass requests.

## Fixed in this branch

- m.easysky previously ran two unrelated transcript handlers sequentially.
  It now runs only its matching handler; linkbnao has its own route.
- v2.kpslink was shadowed by the generic kpslink route. The specific route now runs first.
- Host detection now uses parsed hostname labels, including multi-level domains such
  as new.gdtot.zip, rather than fragile substring matching.
- Only HTTP/HTTPS URLs with a hostname are accepted by the bypass dispatcher.
- The shared form handler now uses bounded aiohttp timeouts, checks HTTP status,
  requires form tokens, validates JSON, and only returns valid HTTP(S) destination URLs.
- Try2Link, GyaniLinks and common shortener handlers now return clear errors when
  forms/tokens/destination values are missing.
- Synchronous requests-based shortener handlers run through asyncio.to_thread
  and have bounded connect/read timeouts; a slow shortener no longer blocks the
  Telegram event loop.
- The old insecure TLS bypass (verify=False) was removed from the JustPaste handler.

## Service status evidence

| Service | Code status | Live verification |
|---|---|---|
| try2link.com | Disabled; obsolete route removed | Domain currently displays a domain-for-sale page |
| m.easysky.in | Routing bug fixed | Bypass flow still needs a real sample URL |
| linkbnao.com | Separate route added | Third-party support directory currently lists it as in development |
| kpslink.in / v2.kpslink.in | Route priority fixed | Real sample URL required to prove end-to-end extraction |
| Other legacy entries | Existing best-effort handlers | Not individually live-tested |

## What CI proves

The CI workflow verifies Python syntax, unit tests, shell scripts, Docker Compose
configuration, and the production image build. It does not prove every third-party
shortener's changing HTML, cookies, anti-bot challenge, or destination API.

For true end-to-end verification, test with a currently generated short URL from
each service. Never use guessed/fabricated short codes as proof of a working bypass.
