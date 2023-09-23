import typing
from logging import getLogger

from kts_backend.store.vk_api.dataclasses import Message, Update

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")

    async def handle_updates(self, updates: list[Update]):
        if not updates:
            return
        else:
            for update in updates:
                if update.object.body["text"] == "/start":
                    await self.app.store.vk_api.send_message_start(
                        Message(
                            user_id=update.object.user_id,
                            peer_id=update.object.body["peer_id"],
                            text="Привет!",
                        )
                    )
                if update.object.body["text"] == '[club222654957|@club222654957] Начать':
                    await self.app.store.vk_api.send_message_start_game(
                        Message(
                            user_id=update.object.user_id,
                            peer_id=update.object.body["peer_id"],
                            text="Привет!",
                        )
                    )
                if update.object.body["text"] == '[club222654957|@club222654957] Старт игры!!!' and update.object.user_id == self.app.store.vk_api.capitan_id:
                    await self.app.store.vk_api.send_message_question(
                        Message(
                            user_id=update.object.user_id,
                            peer_id=update.object.body["peer_id"],
                            text="Привет!",
                        ),
                        0
                    )