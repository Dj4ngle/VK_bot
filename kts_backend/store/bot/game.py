import time
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from kts_backend.store.vk_api.dataclasses import Message


class GameManager:
    def __init__(self, app: "Application", *args, **kwargs):
        self.app = app
        self.bot_points: int = 0
        self.users_points: int = 0
        self.current_question: int = 0

    async def game_round(self, update, question):
        await self.app.store.vk_api.send_message(
            Message(
                peer_id=update.object.body["peer_id"],
                text=question,
            ),
        )

        await self.app.store.vk_api.send_message(
            Message(
                peer_id=update.object.body["peer_id"],
                text="На размышление одна минута",
            ),
        )

        time.sleep(5)

        await self.app.store.vk_api.send_message(
            Message(
                peer_id=update.object.body["peer_id"],
                text="Осталось 10 секунд",
            ),
        )

        time.sleep(1)

        keyboard = VkKeyboard(inline=True)
        for user in self.app.store.bots_manager.users_list:
            keyboard.add_button(user.first_name + ' ' + user.last_name, VkKeyboardColor.PRIMARY)
            keyboard.add_line()
        keyboard.lines.pop()

        await self.app.store.vk_api.send_keyboard_message(
            Message(
                peer_id=update.object.body["peer_id"],
                text="Капитан, выберите кто отвечает",
            ),
            keyboard.get_keyboard(),
        )