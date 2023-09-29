import time

from sqlalchemy import select
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from kts_backend.questions.models import TeamPlayerModel
from kts_backend.store.vk_api.dataclasses import Message


class GameManager:
    def __init__(self, app: "Application", *args, **kwargs):
        self.app = app

    async def game_round(self, update, question, session_id):

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

        #time.sleep(5)

        await self.app.store.vk_api.send_message(
            Message(
                peer_id=update.object.body["peer_id"],
                text="Осталось 10 секунд",
            ),
        )

        #time.sleep(1)

        async with self.app.database.session() as session:
            res = await session.execute(
                select(TeamPlayerModel).where(TeamPlayerModel.session_id==session_id))
            answerers = res.scalars().all()

        keyboard = VkKeyboard(inline=True)
        for ans in answerers:
            keyboard.add_button(ans.first_name + ' ' + ans.last_name, VkKeyboardColor.PRIMARY)
            keyboard.add_line()
        keyboard.lines.pop()

        await self.app.store.vk_api.send_keyboard_message(
            Message(
                peer_id=update.object.body["peer_id"],
                text="Капитан, выберите кто отвечает",
            ),
            keyboard.get_keyboard(),
        )