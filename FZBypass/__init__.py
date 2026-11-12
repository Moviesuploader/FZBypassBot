from os import getenv, makedirs
from time import time
from wzgram import Client
from wzgram.enums import ParseMode
from logging import getLogger, StreamHandler, INFO, ERROR, basicConfig
from logging.handlers import RotatingFileHandler
from uvloop import install

install()

try:
    import config
except ImportError:
    config = None

DATA_DIR = str((getattr(config, "DATA_DIR", None) if config else None) or getenv("DATA_DIR", "data"))
makedirs(DATA_DIR, exist_ok=True)
LOG_FILE = f"{DATA_DIR}/log.txt"

basicConfig(
    format="[%(asctime)s] [%(levelname)s] - %(message)s",
    datefmt="%d-%b-%y %I:%M:%S %p",
    handlers=[
        RotatingFileHandler(
            LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        ),
        StreamHandler(),
    ],
    level=INFO,
)

getLogger("pyrogram").setLevel(ERROR)
LOGGER = getLogger(__name__)


def conf(key, default=""):
    value = getattr(config, key, None) if config else None
    if value is None or value == "":
        value = getenv(key, default)
    return value


BOT_START = time()


class Config:
    BOT_TOKEN = str(conf("BOT_TOKEN")).strip()
    API_HASH = str(conf("API_HASH")).strip()
    try:
        API_ID = int(conf("API_ID", 0) or 0)
    except (TypeError, ValueError):
        API_ID = 0
    try:
        OWNER_ID = int(conf("OWNER_ID", 0) or 0)
    except (TypeError, ValueError):
        OWNER_ID = 0

    if not BOT_TOKEN or not API_HASH or API_ID <= 0 or OWNER_ID <= 0:
        LOGGER.critical(
            "Required configuration missing/invalid: BOT_TOKEN, API_ID, "
            "API_HASH and OWNER_ID must be set. See .env.example."
        )
        raise SystemExit(1)

    CMD_SUFFIX = str(conf("CMD_SUFFIX"))
    AUTO_BYPASS = str(conf("AUTO_BYPASS", "False")).strip().lower() in {
        "1", "true", "yes", "on"
    }
    _auth = conf("AUTH_CHATS")
    AUTH_CHATS = (
        _auth.split()
        if isinstance(_auth, str)
        else [str(chat) for chat in (_auth or [])]
    )
    DIRECT_INDEX = str(conf("DIRECT_INDEX")).rstrip("/")
    LARAVEL_SESSION = str(conf("LARAVEL_SESSION"))
    XSRF_TOKEN = str(conf("XSRF_TOKEN"))
    GDTOT_CRYPT = str(conf("GDTOT_CRYPT"))
    DRIVEFIRE_CRYPT = str(conf("DRIVEFIRE_CRYPT"))
    HUBDRIVE_CRYPT = str(conf("HUBDRIVE_CRYPT"))
    KATDRIVE_CRYPT = str(conf("KATDRIVE_CRYPT"))
    TERA_COOKIE = str(conf("TERA_COOKIE"))


Bypass = Client(
    "FZ",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workdir=DATA_DIR,
    plugins=dict(root="FZBypass/handlers"),
    parse_mode=ParseMode.HTML,
)
