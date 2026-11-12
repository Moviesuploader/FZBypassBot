from asyncio import to_thread
from re import search
from urllib.parse import parse_qs, urlparse

from requests import Session


def _recaptcha_v3(anchor_url):
    parsed = urlparse(anchor_url)
    match = search(r"/recaptcha/(api2|enterprise)/anchor$", parsed.path)
    if not match:
        raise ValueError("Invalid reCAPTCHA anchor URL")

    api = match.group(1)
    params = parse_qs(parsed.query)
    required = ("k", "v", "co")
    if any(not params.get(key) for key in required):
        raise ValueError("reCAPTCHA anchor URL is missing required parameters")

    base_url = f"{parsed.scheme}://{parsed.netloc}/recaptcha/{api}"
    with Session() as session:
        session.headers.update(
            {"content-type": "application/x-www-form-urlencoded"}
        )
        response = session.get(
            f"{base_url}/anchor",
            params=params,
            timeout=(5, 15),
        )
        response.raise_for_status()
        token_match = search(
            r'name="recaptcha-token" value="([^"]+)"',
            response.text,
        )
        if not token_match:
            raise RuntimeError("reCAPTCHA anchor token was not found")

        response = session.post(
            f"{base_url}/reload",
            params={"k": params["k"][0]},
            data={
                "v": params["v"][0],
                "reason": "q",
                "c": token_match.group(1),
                "k": params["k"][0],
                "co": params["co"][0],
            },
            timeout=(5, 15),
        )
        response.raise_for_status()
        result = search(r'"rresp","([^"]+)"', response.text)
        if not result:
            raise RuntimeError("reCAPTCHA response token was not found")
        return result.group(1)


async def recaptchaV3(
    ANCHOR_URL="https://www.google.com/recaptcha/api2/anchor?ar=1&k=6Lcr1ncUAAAAAH3cghg6cOTPGARa8adOf-y9zv2x&co=aHR0cHM6Ly9vdW8ucHJlc3M6NDQz&hl=en&v=pCoGBhjs9s8EhFOHJFe8cqis&size=invisible&cb=ahgyd1gkfkhe",
):
    # requests is synchronous; keep its network waits off the bot event loop.
    return await to_thread(_recaptcha_v3, ANCHOR_URL)
