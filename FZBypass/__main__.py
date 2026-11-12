from FZBypass import Bypass, LOGGER, Config, conf, DATA_DIR
from FZBypass.core.commands import BotCommands
from wzgram import idle
from wzgram.filters import command, user
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from os import path as ospath, execl, remove
from sys import executable
from threading import Thread

BOT_READY = False


class Health(BaseHTTPRequestHandler):
    def _respond(self, body=b""):
        status = 200 if BOT_READY else 503
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_HEAD(self):
        self._respond()

    def do_GET(self):
        body = b"FZ Bypass Bot is alive" if BOT_READY else b"Bot is starting"
        self._respond(body)

    def log_message(self, *_args):
        pass


def serve_health():
    port = int(conf("PORT", 8080))
    try:
        server = ThreadingHTTPServer(("0.0.0.0", port), Health)
        server.daemon_threads = True
        LOGGER.info("Health server listening on port %s", port)
        server.serve_forever()
    except OSError:
        LOGGER.exception("Health server could not bind to port %s", port)


@Bypass.on_message(command(BotCommands.RestartCommand) & user(Config.OWNER_ID))
async def restart(_, message):
    restart_message = await message.reply("<i>Restarting...</i>")
    restart_file = ospath.join(DATA_DIR, ".restartmsg")
    with open(restart_file, "w", encoding="utf-8") as file:
        file.write(f"{restart_message.chat.id}\n{restart_message.id}\n")
    # Restart only the current process. Deployment updates are performed by
    # rebuilding/restarting the container, never by deleting or resetting .git.
    execl(executable, executable, "-m", "FZBypass")


async def notify_restart():
    restart_file = ospath.join(DATA_DIR, ".restartmsg")
    if not ospath.isfile(restart_file):
        return
    try:
        with open(restart_file, encoding="utf-8") as file:
            chat_id, msg_id = map(int, file.read().splitlines()[:2])
        await Bypass.edit_message_text(
            chat_id=chat_id, message_id=msg_id, text="<i>Restarted!</i>"
        )
    except Exception:
        LOGGER.exception("Could not update the restart notification")
    finally:
        try:
            remove(restart_file)
        except FileNotFoundError:
            pass


async def main():
    global BOT_READY
    Thread(target=serve_health, daemon=True).start()
    await Bypass.start()
    BOT_READY = True
    LOGGER.info("FZ Bot Started!")
    await notify_restart()
    await idle()
    BOT_READY = False
    await Bypass.stop()


Bypass.loop.run_until_complete(main())
