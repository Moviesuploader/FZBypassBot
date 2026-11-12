from re import escape, match, search
from urllib.parse import parse_qs, urlparse

from requests import get as rget
from wzgram.enums import MessageEntityType
from wzgram.filters import create

from FZBypass import Config
from FZBypass.core.commands import BotCommands

BYPASS_CMDS = "|".join(escape(command) for command in BotCommands.BypassCommand)
EXEC_CMDS = "|".join(escape(command) for command in BotCommands.ExecCommands)


async def auth_topic(_, __, message):
    for chat in Config.AUTH_CHATS:
        try:
            if ":" in chat:
                chat_id, topic_id = chat.split(":", maxsplit=1)
                if (
                    int(chat_id) == message.chat.id
                    and message.is_topic_message
                    and message.message_thread_id == int(topic_id)
                ):
                    return True
            elif int(chat) == message.chat.id:
                return True
        except (TypeError, ValueError):
            continue
    return False


AuthChatsTopics = create(auth_topic)


async def auto_bypass(_, client, message):
    txt = message.text or ""
    if (
        Config.AUTO_BYPASS
        and message.entities
        and not match(rf"^/({EXEC_CMDS})(?:@{client.me.username})?(?:$| )", txt)
        and any(
            entity.type in (MessageEntityType.TEXT_LINK, MessageEntityType.URL)
            for entity in message.entities
        )
    ):
        return True

    return bool(
        not Config.AUTO_BYPASS
        and txt
        and match(rf"^/({BYPASS_CMDS})(?:@{client.me.username})?(?:$| )", txt)
        and not match(rf"^/({EXEC_CMDS})(?:$| )", txt)
    )


BypassFilter = create(auto_bypass)


def get_gdriveid(link):
    parsed = urlparse(link)
    found = search(
        r"(?:/folders/|/file/d/|/d/)([-A-Za-z0-9_]+)",
        parsed.path,
    )
    if found:
        return found.group(1)
    file_id = parse_qs(parsed.query).get("id")
    if file_id and file_id[0]:
        return file_id[0]
    raise ValueError("Google Drive file/folder ID was not found in the URL")


def get_dl(link, direct_mode=False):
    if not Config.DIRECT_INDEX:
        return "No Direct Index Added !"
    file_id = get_gdriveid(link)
    endpoint = f"{Config.DIRECT_INDEX}/generate.aspx"
    try:
        response = rget(
            endpoint,
            params={"id": file_id},
            timeout=(5, 20),
        )
        response.raise_for_status()
        result = response.json().get("link")
        if result:
            return result
    except Exception:
        pass
    return f"{Config.DIRECT_INDEX}/direct.aspx?id={file_id}"


def convert_time(seconds):
    milliseconds = max(0, int(seconds * 1000))
    periods = [
        ("d", 86400000),
        ("h", 3600000),
        ("m", 60000),
        ("s", 1000),
        ("ms", 1),
    ]
    result = ""
    for period_name, period_ms in periods:
        if milliseconds >= period_ms:
            value, milliseconds = divmod(milliseconds, period_ms)
            result += f"{int(value)}{period_name}"
    return result or "0ms"


SIZE_UNITS = ["B", "KB", "MB", "GB", "TB", "PB"]


def get_readable_size(size):
    if not size:
        return "0B"
    index = 0
    while size >= 1024 and index < len(SIZE_UNITS) - 1:
        size /= 1024
        index += 1
    return f"{size:.2f}{SIZE_UNITS[index]}"


def progress_bar(percent, slots=12):
    percent = min(max(float(percent or 0), 0), 100)
    filled = int(percent / 100 * slots)
    return f"[{'■' * filled}{'□' * (slots - filled)}]"
