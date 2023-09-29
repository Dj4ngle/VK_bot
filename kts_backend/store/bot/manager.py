import typing, random, time
from logging import getLogger

from sqlalchemy import select, insert
from sqlalchemy import update as update2

from kts_backend.questions.models import QuestionModel, SessionsModel, GamesHistoryModel, Sessions, TeamPlayerModel, \
    GamesHistory
from kts_backend.store.vk_api.dataclasses import Message, Update

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application

from vk_api.keyboard import VkKeyboard, VkKeyboardColor

class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")
        self.questions: []
        self.current_question = 0

    async def handle_updates(self, update):

        if not update:
            return
        else:
            # Команда для запуска бота
            if update.object.body["text"] == "/start":

                #Выбор капитана команды
                await self.app.store.start_game.choose_the_capitan(update)

            else:

                async with self.app.database.session() as session:
                    res = await session.execute(
                        select(SessionsModel).where(SessionsModel.group_id == update.object.peer_id,
                                                    SessionsModel.status != "Closed"))
                    cur_session = res.scalars().first()
                    if cur_session == []:
                        cur_session = Sessions(id=None, group_id=None, status=None, capitan_id=None)

                    res = await session.execute(select(GamesHistoryModel).where(GamesHistoryModel.session_id==cur_session.id))
                    cur_round_info = res.scalars().first()
                    if cur_round_info == []:
                        cur_round_info = GamesHistory(id=None, session_id=None, guestion_id=None, player_id=None, is_answer_right=False)

                # Проверка, что собщение является командой боту
                if update.object.body["text"].startswith(f'[club{self.app.config.bot.group_id}|@'):

                    index = update.object.body["text"].index(" ")
                    command = update.object.body["text"][index + 1:]

                    if update.object.user_id == cur_session.capitan_id:
                        if command == 'Старт игры!!!':

                            async with self.app.database.session() as session:
                                res = await session.execute(select(QuestionModel))
                                self.questions = res.scalars().all()

                                await session.execute(
                                    update2(SessionsModel).where(SessionsModel.group_id == update.object.peer_id).values(
                                        status="Game started"))
                                await session.commit()

                            # Старт вопросов после решения капитана о начале игры
                            await self.app.store.game_round.game_round(update, self.questions[self.current_question].title, cur_session.id)

                        elif cur_session.status == "Game started":
                            # Информирование всех, кто выбран отвечающим для данного вопроса
                            async with self.app.database.session() as session:
                                res = await session.execute(select(TeamPlayerModel).where(TeamPlayerModel.first_name==command.split(' ')[0], TeamPlayerModel.last_name==command.split(' ')[1]))
                                answerer = res.scalars().first()
                                await session.execute(insert(GamesHistoryModel).values(session_id=cur_session.id, guestion_id=self.questions[self.current_question].id, player_id=answerer.player_id, is_answer_right=False))
                                await session.commit()

                            message_to_user = f"@id{answerer.player_id} ({command})  выбран отвечающим"

                            await self.app.store.vk_api.send_message(
                                Message(
                                    peer_id=update.object.peer_id,
                                    text=message_to_user,
                                ),
                            )

                elif cur_session.status == "Game started" and cur_round_info.player_id == update.object.user_id:

                    async with self.app.database.session() as session:
                        res = await session.execute(
                            select(QuestionModel).where(QuestionModel.id == cur_round_info.guestion_id))
                        cur_question = res.scalars().first()

                    # Проверка правильности ответа на вопрос
                        if update.object.body["text"].lower() == cur_question.answer:
                            await self.app.store.vk_api.send_message(
                                Message(
                                    peer_id=update.object.peer_id,
                                    text="Ответ правильный!!!!!!",
                                )
                            )

                            async with self.app.database.session() as session:
                                await session.execute(
                                    update2(GamesHistoryModel).where(GamesHistoryModel.id == cur_round_info.id).values(
                                        is_answer_right=True))
                                await session.commit()

                        else:
                            await self.app.store.vk_api.send_message(
                                Message(
                                    peer_id=update.object.peer_id,
                                    text=f"Ответ неправильный!!! Правильный ответ: {cur_question.answer}",
                                )
                            )

                            #TODO ужно или уже учитывается?
                            async with self.app.database.session() as session:
                                await session.execute(update2(GamesHistoryModel).where(GamesHistoryModel.id == cur_round_info.id).values(is_answer_right=False))
                                await session.commit()

                        if self.current_question > len(self.questions) - 1:
                            await self.app.store.vk_api.send_message(
                                Message(
                                    peer_id=update.object.peer_id,
                                    text=f"Игра окончена! "
                                         f"Бот: {self.bot_points} "
                                         f"Игроки: {self.users_points}",
                                )
                            )
                            self.bot_started = False
                            self.game_started = False
                            self.current_question = 0
                            self.bot_points = 0
                            self.users_points = 0
                        else:

                            bot_points = 0
                            users_points = 0

                            async with self.app.database.session() as session:
                                res = await session.execute(select(GamesHistoryModel).where(GamesHistoryModel.session_id == cur_session.id))
                                all_rounds = res.scalars().all()

                            for round in all_rounds:
                                if round.is_answer_right:
                                    users_points += 1
                                else:
                                    bot_points += 1


                            await self.app.store.vk_api.send_message(
                                Message(
                                    peer_id=update.object.peer_id,
                                    text=f"Текущий счёт: Бот: {bot_points} Игроки: {users_points}",
                                )
                            )
                            self.current_question += 1

                            await self.app.store.game_round.game_round(update, self.questions[self.current_question].title, cur_session.id)