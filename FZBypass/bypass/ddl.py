from requests import post as rpost ,get as rget
from re import findall, compile
from time import sleep, time
from asyncio import sleep as asleep, to_thread
from urllib.parse import quote, urlparse

from bs4 import BeautifulSoup
from cloudscraper import create_scraper
from curl_cffi.requests import Session as cSession
from requests import Session, get as rget
from aiohttp import ClientSession, ClientTimeout

from FZBypass import Config
from FZBypass.core.exceptions import DDLException
from FZBypass.bypass.recaptcha import recaptchaV3

async def get_readable_time(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h{minutes}m{seconds}s"


async def yandex_disk(url: str) -> str:
    cget = create_scraper().request
    try:
        return cget(
            "get",
            f"https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={url}",
        ).json()["href"]
    except KeyError:
        raise DDLException("File not Found / Download Limit Exceeded")


async def mediafire(url: str):
    if final_link := findall(
        r"https?:\/\/download\d+\.mediafire\.com\/\S+\/\S+\/\S+", url
    ):
        return final_link[0]
    cget = create_scraper().request
    try:
        url = cget("get", url).url
        page = cget("get", url).text
    except Exception as e:
        raise DDLException(f"{e.__class__.__name__}")
    if final_link := findall(
        r"\'(https?:\/\/download\d+\.mediafire\.com\/\S+\/\S+\/\S+)\'", page
    ):
        return final_link[0]
    elif temp_link := findall(
        r'\/\/(www\.mediafire\.com\/file\/\S+\/\S+\/file\?\S+)', page
    ):
        return await mediafire("https://"+temp_link[0].strip('"'))
    else:
        raise DDLException("No links found in this page")


async def shrdsk(url: str) -> str:
    cget = create_scraper().request
    try:
        url = cget("GET", url).url
        res = cget(
            "GET",
            f'https://us-central1-affiliate2apk.cloudfunctions.net/get_data?shortid={url.split("/")[-1]}',
        )
    except Exception as e:
        raise DDLException(f"{e.__class__.__name__}")
    if res.status_code != 200:
        raise DDLException(f"Status Code {res.status_code}")
    res = res.json()
    if "type" in res and res["type"].lower() == "upload" and "video_url" in res:
        return quote(res["video_url"], safe=":/")
    raise DDLException("No Direct Link Found")


async def terabox(url: str) -> str:
    sess = Session()

    def retryme(url):
        while True:
            try:
                return sess.get(url)
            except:
                pass

    url = retryme(url).url
    key = url.split("?surl=")[-1]
    url = f"http://www.terabox.com/wap/share/filelist?surl={key}"
    sess.cookies.update({"ndus": Config.TERA_COOKIE})

    res = retryme(url)
    key = res.url.split("?surl=")[-1]
    soup = BeautifulSoup(res.content, "lxml")
    jsToken = None

    for fs in soup.find_all("script"):
        fstring = fs.string
        if fstring and fstring.startswith("try {eval(decodeURIComponent"):
            jsToken = fstring.split("%22")[1]

    res = retryme(
        f"https://www.terabox.com/share/list?app_id=250528&jsToken={jsToken}&shorturl={key}&root=1"
    )
    result = res.json()
    if result["errno"] != 0:
        raise DDLException(f"{result['errmsg']}' Check cookies")
    result = result["list"]
    if len(result) > 1:
        raise DDLException("Can't download mutiple files")
    result = result[0]

    if result["isdir"] != "0":
        raise DDLException("Can't download folder")
    try:
        return result["dlink"]
    except:
        raise DDLException("Link Extraction Failed")

async def try2link(url: str) -> str:
    code = urlparse(url).path.rstrip("/").split("/")[-1]
    if not code:
        raise DDLException("Try2Link code is missing")

    async with ClientSession(timeout=ClientTimeout(total=30, connect=8)) as session:
        html = None
        referers = [
            "https://hightrip.net/",
            "https://to-travel.net/",
            "https://world2our.com/",
        ]
        for referer in referers:
            try:
                async with session.get(
                    f"https://try2link.com/{code}", headers={"Referer": referer}
                ) as response:
                    response.raise_for_status()
                    html = await response.text()
                    break
            except Exception:
                continue
        if not html:
            raise DDLException("Try2Link landing page could not be loaded")

        soup = BeautifulSoup(html, "html.parser")
        form = soup.find(id="go-link")
        if not form:
            raise DDLException("Try2Link form was not found")
        data = {
            item.get("name"): item.get("value", "")
            for item in form.find_all("input")
            if item.get("name")
        }
        if not data:
            raise DDLException("Try2Link form tokens were not found")

        await asleep(6)
        async with session.post(
            "https://try2link.com/links/go",
            data=data,
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"https://try2link.com/{code}",
            },
        ) as response:
            response.raise_for_status()
            payload = await response.json(content_type=None)
        destination = payload.get("url") if isinstance(payload, dict) else None
        if not destination:
            raise DDLException("Try2Link did not return a destination URL")
        return destination


async def gyanilinks(url: str) -> str:
    code = urlparse(url).path.rstrip("/").split("/")[-1]
    if not code:
        raise DDLException("GyaniLinks code is missing")
    useragent = (
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    )
    domain = "https://go.bloggingaro.com"

    async with ClientSession(timeout=ClientTimeout(total=30, connect=8)) as session:
        async with session.get(
            f"{domain}/{code}",
            headers={"Referer": "https://tech.hipsonyc.com/", "User-Agent": useragent},
        ) as response:
            response.raise_for_status()
            cookies = response.cookies
        async with session.get(
            f"{domain}/{code}",
            headers={"Referer": "https://hipsonyc.com/", "User-Agent": useragent},
            cookies=cookies,
        ) as response:
            response.raise_for_status()
            html = await response.text()

        soup = BeautifulSoup(html, "html.parser")
        data = {
            item.get("name"): item.get("value", "")
            for item in soup.find_all("input")
            if item.get("name")
        }
        if not data:
            raise DDLException("GyaniLinks form tokens were not found")

        await asleep(5)
        async with session.post(
            f"{domain}/links/go",
            data=data,
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": useragent,
                "Referer": f"{domain}/{code}",
            },
            cookies=cookies,
        ) as response:
            response.raise_for_status()
            payload = await response.json(content_type=None)
        destination = payload.get("url") if isinstance(payload, dict) else None
        if not destination:
            raise DDLException("GyaniLinks did not return a destination URL")
        return destination


async def ouo(url: str):
    tempurl = url.replace("ouo.io", "ouo.press")
    p = urlparse(tempurl)
    id = tempurl.split("/")[-1]
    client = cSession(
        headers={
            "authority": "ouo.press",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "cache-control": "max-age=0",
            "referer": "http://www.google.com/ig/adde?moduleurl=",
            "upgrade-insecure-requests": "1",
        }
    )
    res = client.get(tempurl, impersonate="chrome110")
    next_url = f"{p.scheme}://{p.hostname}/go/{id}"

    for _ in range(2):
        if res.headers.get("Location"):
            break
        bs4 = BeautifulSoup(res.content, "lxml")
        inputs = bs4.form.findAll("input", {"name": compile(r"token$")})
        data = {inp.get("name"): inp.get("value") for inp in inputs}
        data["x-token"] = await recaptchaV3()
        res = client.post(
            next_url,
            data=data,
            headers={"content-type": "application/x-www-form-urlencoded"},
            allow_redirects=False,
            impersonate="chrome110",
        )
        next_url = f"{p.scheme}://{p.hostname}/xreallcygo/{id}"

    return res.headers.get("Location")


async def mdisk(url: str) -> str:
    """
    Depreciated ( Code Preserved )
    """
    header = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://mdisk.me/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
    }
    URL = f'https://diskuploader.entertainvideo.com/v1/file/cdnurl?param={url.rstrip("/").split("/")[-1]}'
    res = rget(url=URL, headers=header).json()
    return res["download"] + "\n\n" + res["source"]


async def transcript(url: str, DOMAIN: str, ref: str, sltime) -> str:
    code = urlparse(url).path.rstrip("/").split("/")[-1]
    if not code:
        raise DDLException("Shortener code is missing")
    useragent = (
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    )

    async with ClientSession(timeout=ClientTimeout(total=35, connect=8)) as session:
        async with session.get(
            f"{DOMAIN.rstrip('/')}/{code}",
            headers={"Referer": ref, "User-Agent": useragent},
        ) as response:
            response.raise_for_status()
            html = await response.text()

        soup = BeautifulSoup(html, "html.parser")
        title_tag = soup.find("title")
        if title_tag and "just a moment" in title_tag.get_text(" ", strip=True).lower():
            raise DDLException("Shortener is protected by Cloudflare; bypass unavailable")

        data = {
            item.get("name"): item.get("value", "")
            for item in soup.find_all("input")
            if item.get("name")
        }
        if not data:
            raise DDLException("Shortener form tokens were not found")

        await asleep(max(0, min(float(sltime), 20)))
        async with session.post(
            f"{DOMAIN.rstrip('/')}/links/go",
            data=data,
            headers={
                "Referer": f"{DOMAIN.rstrip('/')}/{code}",
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": useragent,
            },
        ) as response:
            response.raise_for_status()
            payload = await response.json(content_type=None)

        destination = payload.get("url") if isinstance(payload, dict) else None
        parsed_destination = urlparse(destination or "")
        if parsed_destination.scheme not in {"http", "https"} or not parsed_destination.hostname:
            raise DDLException("Shortener did not return a valid destination URL")
        return destination


def _justpaste_sync(url: str):
    resp = rget(url, timeout=(5, 20))
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    paragraphs = soup.select('div[id="articleContent"] > p')
    text = ", ".join(p.get_text(" ", strip=True) for p in paragraphs)
    if not text:
        raise DDLException("No paste content found")
    return text


def _linksxyz_sync(url: str):
    resp = rget(url, timeout=(5, 20))
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    links = soup.select('div[id="redirect-info"] > a[href]')
    if not links:
        raise DDLException("Redirect target not found")
    return links[0]["href"]


def _shareus_sync(url: str) -> str:
    domain = "https://api.shrslink.xyz"
    code = urlparse(url).path.rstrip("/").split("/")[-1]
    if not code:
        raise DDLException("ShareUs short code is missing")
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36",
        "Origin": "https://shareus.io",
    }
    response = rget(
        f"{domain}/v",
        params={"shortid": code, "initial": "true", "referrer": ""},
        headers=headers,
        timeout=(5, 20),
    )
    response.raise_for_status()
    sid = response.json().get("sid")
    if not sid:
        raise DDLException("ShareUs did not return a session ID")
    response = rget(
        f"{domain}/get_link", params={"sid": sid}, headers=headers, timeout=(5, 20)
    )
    response.raise_for_status()
    destination = response.json().get("link_info", {}).get("destination")
    if not destination:
        raise DDLException("ShareUs destination was not returned")
    return destination


def _linkvertise_sync(url: str) -> str:
    response = rget(
        "https://bypass.pm/bypass2",
        params={"url": url},
        timeout=(5, 20),
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("success") and payload.get("destination"):
        return payload["destination"]
    raise DDLException(payload.get("msg") or "Linkvertise bypass service failed")


def _rslinks_sync(url: str) -> str:
    response = rget(
        url, stream=True, allow_redirects=False, timeout=(5, 20)
    )
    location = response.headers.get("location")
    response.close()
    if not location or "ms9" not in location:
        raise DDLException("RSLinks redirect token was not found")
    code = location.split("ms9", 1)[-1]
    return f"https://techyproio.blogspot.com/p/short.html?{code}=="


def _shorter_sync(url: str) -> str:
    response = create_scraper().request(
        "GET", url, allow_redirects=True, timeout=(5, 20)
    )
    if response.url and response.url != url:
        return response.url
    location = response.headers.get("Location")
    if location:
        return location
    raise DDLException("No redirect target returned by shortener")


def _appurl_sync(url: str):
    response = create_scraper().request(
        "GET", url, allow_redirects=True, timeout=(5, 20)
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    tag = soup.select_one('meta[property="og:url"][content]')
    if not tag:
        raise DDLException("AppURL destination metadata not found")
    return tag["content"]


def _surl_sync(url: str):
    response = create_scraper().request(
        "GET", f"{url}+", timeout=(5, 20)
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    tag = soup.select_one("p.long-url")
    if not tag:
        raise DDLException("SURL destination not found")
    parts = tag.get_text(" ", strip=True).split()
    if len(parts) < 2:
        raise DDLException("SURL destination format was not recognized")
    return parts[1]


def _thinfi_sync(url: str) -> str:
    response = rget(url, timeout=(5, 20))
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    anchor = soup.select_one("p a[href]")
    if not anchor:
        raise DDLException("Thinfi destination not found")
    return anchor["href"]


# These handlers use synchronous requests/cloudscraper clients. Keep network
# I/O off the Telegram event loop.
async def justpaste(url: str):
    return await to_thread(_justpaste_sync, url)


async def linksxyz(url: str):
    return await to_thread(_linksxyz_sync, url)


async def shareus(url: str):
    return await to_thread(_shareus_sync, url)


async def linkvertise(url: str):
    return await to_thread(_linkvertise_sync, url)


async def rslinks(url: str):
    return await to_thread(_rslinks_sync, url)


async def shorter(url: str):
    return await to_thread(_shorter_sync, url)


async def appurl(url: str):
    return await to_thread(_appurl_sync, url)


async def surl(url: str):
    return await to_thread(_surl_sync, url)


async def thinfi(url: str):
    return await to_thread(_thinfi_sync, url)
