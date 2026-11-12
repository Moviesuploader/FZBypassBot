from time import time
from html import escape
from asyncio import Semaphore, create_task, gather, sleep as asleep, wait_for

from wzgram.filters import user
from wzgram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from wzgram.enums import MessageEntityType
from wzgram.errors import QueryIdInvalid

from FZBypass import Config, Bypass
from FZBypass.bypass.checker import direct_link_checker, is_excep_link
from FZBypass.core.bot_utils import AuthChatsTopics, convert_time, BypassFilter

MAX_LINKS_PER_MESSAGE = 25
LINK_TIMEOUT_SECONDS = 120
BYPASS_SEMAPHORE = Semaphore(8)


async def run_bypass(link, onlylink=False):
    async with BYPASS_SEMAPHORE:
        return await wait_for(
            direct_link_checker(link, onlylink),
            timeout=LINK_TIMEOUT_SECONDS,
        )


@Bypass.on_message(BypassFilter & (user(Config.OWNER_ID) | AuthChatsTopics))
async def bypass_check(_, message):
    reply_to = message.reply_to_message
    if reply_to and (reply_to.text is not None or reply_to.caption is not None):
        txt = reply_to.text or reply_to.caption
        entities = reply_to.entities or reply_to.caption_entities or []
    elif message.text and (
        Config.AUTO_BYPASS or len(message.text.split()) > 1
    ):
        txt = message.text
        entities = message.entities or []
    else:
        return await message.reply("<i>No Link Provided!</i>")

    if not txt or not entities:
        return await message.reply("<i>No valid link entities found!</i>")

    links = []
    for entity in entities:
        link = ""
        if entity.type == MessageEntityType.URL:
            link = txt[entity.offset : entity.offset + entity.length]
        elif entity.type == MessageEntityType.TEXT_LINK:
            link = entity.url
        if link:
            links.append(link)

    if not links:
        return await message.reply("<i>No valid link entities found!</i>")

    omitted = max(0, len(links) - MAX_LINKS_PER_MESSAGE)
    links = links[:MAX_LINKS_PER_MESSAGE]
    wait_msg = await message.reply("<i>Bypassing...</i>")
    started = time()

    tasks = [create_task(run_bypass(link)) for link in links]
    results = await gather(*tasks, return_exceptions=True)

    output = []
    for source, result in zip(links, results):
        if isinstance(result, Exception):
            result_text = f"\n┖ <b>Bypass Error:</b> {escape(str(result))}"
        elif is_excep_link(source):
            result_text = str(result)
        elif isinstance(result, list):
            result_text, branch = "", "┖"
            for index, target in reversed(list(enumerate(result, start=1))):
                result_text = (
                    f"\n{branch} <b>{index}x Bypass Link:</b> {target}"
                    + result_text
                )
                branch = "┠"
        else:
            result_text = f"\n┖ <b>Bypass Link:</b> {result}"

        if is_excep_link(source):
            output.append(f"{result_text}\n\n━━━━━━━✦✗✦━━━━━━━\n\n")
        else:
            output.append(
                f"┎ <b>Source Link:</b> {escape(source)}{result_text}"
                "\n\n━━━━━━━✦✗✦━━━━━━━\n\n"
            )

    elapsed = convert_time(time() - started)
    if output:
        output[-1] += (
            f"┎ <b>Total Links:</b> {len(links)}"
            f"\n┠ <b>Results In <code>{elapsed}</code></b>"
            f"\n┖ <b>By:</b> {message.from_user.mention} "
            f"(#ID{message.from_user.id})"
        )
    if omitted:
        output.append(
            f"\n<i>Note: {omitted} extra link(s) skipped; "
            f"maximum is {MAX_LINKS_PER_MESSAGE} per message.</i>"
        )

    text = "━━━━━━━✦✗✦━━━━━━━\n\n"
    for item in output:
        if len(text) + len(item) > 3900:
            await wait_msg.edit(text, disable_web_page_preview=True)
            wait_msg = await message.reply(
                "<i>Fetching remaining results...</i>",
                reply_to_message_id=wait_msg.id,
            )
            text = ""
            await asleep(1)
        text += item

    if text.strip():
        await wait_msg.edit(text, disable_web_page_preview=True)
    else:
        await wait_msg.delete()


@Bypass.on_inline_query()
async def inline_query(_, query):
    answers = []
    raw_query = query.query or ""
    if raw_query[:4].lower() == "!bp ":
        # Only the command prefix is case-insensitive. URLs themselves are not.
        link = raw_query[4:].strip()
        if not link:
            return await query.answer("Usage: !bp [link]", cache_time=0)

        started = time()
        try:
            result = await run_bypass(link, onlylink=True)
            elapsed = convert_time(time() - started)
            body = str(result)
            if not is_excep_link(link):
                body = (
                    f"┎ <b>Source Link:</b> {escape(link)}"
                    f"\n┃\n┖ <b>Bypass Link:</b> {body}"
                )
            answers.append(
                InlineQueryResultArticle(
                    title="✅️ Bypass Link Success!",
                    input_message_content=InputTextMessageContent(
                        f"{body}\n\n✎﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏"
                        f"\n\n🧭 <b>Took Only <code>{elapsed}</code></b>",
                        disable_web_page_preview=True,
                    ),
                    description=f"Bypass via !bp {link}",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton(
                            "Bypass Again",
                            switch_inline_query_current_chat="!bp ",
                        )]]
                    ),
                )
            )
        except Exception as error:
            elapsed = convert_time(time() - started)
            body = (
                f"┎ <b>Source Link:</b> {escape(link)}"
                f"\n┃\n┖ <b>Bypass Error:</b> {escape(str(error))}"
                f"\n\n🧭 <b>Took Only <code>{elapsed}</code></b>"
            )
            answers.append(
                InlineQueryResultArticle(
                    title="❌️ Bypass Link Error!",
                    input_message_content=InputTextMessageContent(
                        body, disable_web_page_preview=True
                    ),
                    description=f"Bypass via !bp {link}",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton(
                            "Bypass Again",
                            switch_inline_query_current_chat="!bp ",
                        )]]
                    ),
                )
            )
    else:
        answers.append(
            InlineQueryResultArticle(
                title="♻️ Bypass Usage: Inline",
                input_message_content=InputTextMessageContent(
                    "<b><i>FZ Bypass Bot!</i></b>\n\n"
                    "<i>A multi-threaded Telegram bot for supported shortener "
                    "and file-hosting links.</i>\n\n"
                    "🎛 <b>Inline Use:</b> <code>!bp [Single Link]</code>"
                ),
                description="Bypass via !bp [link]",
                reply_markup=InlineKeyboardMarkup(
                    [[
                        InlineKeyboardButton("FZ Channel", url="https://t.me/FXTorrentz"),
                        InlineKeyboardButton(
                            "Try Bypass", switch_inline_query_current_chat="!bp "
                        ),
                    ]]
                ),
            )
        )

    try:
        await query.answer(results=answers, cache_time=0)
    except QueryIdInvalid:
        pass
