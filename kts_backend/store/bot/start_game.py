import random

from sqlalchemy import select, insert, update
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from kts_backend.questions.models import SessionsModel, TeamPlayerModel, QuestionModel
from kts_backend.store.vk_api.dataclasses import Message


class StartGameManager:
    def __init__(self, app: "Application", *args, **kwargs):
        self.app = app
        self.guestions = []
        self.current_question: int = 0


    async def choose_the_capitan(self, _update):

        async with self.app.database.session() as session:
            res = await session.execute(
                select(SessionsModel).where(SessionsModel.group_id == _update.object.peer_id))
            is_session_opened = res.scalars().all()

            if is_session_opened == []:
                await session.execute(
                    insert(SessionsModel).values(group_id=_update.object.peer_id, status="Started",
                                                 capitan_id=None))
                await session.commit()
            else:
                await session.execute(
                    update(SessionsModel).where(SessionsModel.group_id == _update.object.peer_id).values(
                        status="Closed"))
                await session.execute(insert(SessionsModel).values(group_id=_update.object.peer_id, status="Started",
                                                   capitan_id=None))
                await session.commit()

        users_list = await self.app.store.vk_api.get_all_users_from_chat(_update.object.body["peer_id"])
        random_user = random.choice(users_list)

        async with self.app.database.session() as session:
            res =await session.execute(
                update(SessionsModel).where(SessionsModel.group_id == _update.object.peer_id, SessionsModel.status != "Closed").values(
                    capitan_id=random_user.id).returning(SessionsModel.id))
            session_id = res.scalars().first()

            for user in users_list:
                await session.execute(
                    insert(TeamPlayerModel).values(session_id=session_id, player_id=user.id,
                                                 first_name=user.first_name, last_name=user.last_name))
            await session.commit()


        message_to_user = f"Капитан команды @id{random_user.id} ({random_user.first_name} {random_user.last_name}!)"

        keyboard = VkKeyboard(inline=True)
        keyboard.add_button("Старт игры!!!", VkKeyboardColor.PRIMARY)

        await self.app.store.vk_api.send_keyboard_message(
            Message(
                peer_id=_update.object.peer_id,
                text=message_to_user,
            ),
            keyboard.get_keyboard(),
        )
