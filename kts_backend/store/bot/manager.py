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
        self.capitan_id: int | None = None
        self.users_list: []
        self.answerer_id: int | None = None
        self.bot_points: int = 0
        self.users_points: int = 0
        self.bot_started: bool = False
        self.game_started: bool = False
        self.current_question: int = 0
        self.questions: []
        self.session: Sessions | None = None
        self.cur_round_info: GamesHistory | None = None

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
                    self.session = res.scalars().first()
                    if self.session == []:
                        self.session = Sessions(id=None, group_id=None, status=None, capitan_id=None)

                    res = await session.execute(select(GamesHistoryModel).where(GamesHistoryModel.session_id==self.session.id))
                    self.cur_round_info = res.scalars().all()
                    if self.cur_round_info == []:
                        self.cur_round_info = GamesHistory(id=None, session_id=None, guestion_id=None, player_id=None, is_answer_right=False)

                # Проверка, что собщение является командой боту
                if update.object.body["text"].startswith(f'[club{self.app.config.bot.group_id}|@'):

                    index = update.object.body["text"].index(" ")
                    command = update.object.body["text"][index + 1:]

                    if update.object.user_id == self.session.capitan_id:
                        if command == 'Старт игры!!!':

                            async with self.app.database.session() as session:
                                res = await session.execute(select(QuestionModel))
                                self.questions = res.scalars().all()

                                print("###############################")
                                print(self.questions)

                                await session.execute(
                                    update2(SessionsModel).where(SessionsModel.group_id == update.object.peer_id).values(
                                        status="Game started"))
                                await session.commit()

                            # Старт вопросов после решения капитана о начале игры
                            await self.app.store.game_round.game_round(update, self.questions[self.current_question].title, self.session.id)

                        elif self.session.status == "Game started":
                            # Информирование всех, кто выбран отвечающим для данного вопроса
                            async with self.app.database.session() as session:
                                res = await session.execute(select(TeamPlayerModel).where(TeamPlayerModel.first_name==command.split(' ')[0], TeamPlayerModel.last_name==command.split(' ')[1]))
                                answerer = res.scalars().all()
                                await session.execute(insert(GamesHistoryModel).values(session_id=self.session.id, guestion_id=self.questions[self.current_question], player_id=answerer.id, is_answer_right=False))
                                await session.commit()

                            message_to_user = f"@id{answerer.id} ({command})  выбран отвечающим"

                            await self.app.store.vk_api.send_message(
                                Message(
                                    peer_id=update.object.peer_id,
                                    text=message_to_user,
                                ),
                            )

                elif self.session.status == "Game started" and self.cur_round_info.player_id == update.object.user_id:

                    # Проверка правильности ответа на вопрос
                        if update.object.body["text"].lower() == self.guestions[self.current_question].answer:
                            await self.app.store.vk_api.send_message(
                                Message(
                                    peer_id=update.object.peer_id,
                                    text="Ответ правильный!!!!!!",
                                )
                            )

                            async with self.app.database.session() as session:
                                await session.execute(insert(GamesHistoryModel).values(session_id=update.object.peer_id, guestion_id=self.guestions[self.current_question].id, player_id=self.answerer_id, is_answer_right=True))
                                await session.commit()

                        else:
                            await self.app.store.vk_api.send_message(
                                Message(
                                    peer_id=update.object.peer_id,
                                    text=f"Ответ неправильный!!! Правильный ответ: {self.guestions[self.current_question].answer}",
                                )
                            )

                            async with self.app.database.session() as session:
                                await session.execute(insert(GamesHistoryModel).values(session_id=update.object.peer_id, guestion_id=self.guestions[self.current_question].id, player_id=self.answerer_id, is_answer_right=False))
                                await session.commit()

                        self.answerer_id = None

                        self.current_question+=1
                        if self.current_question > len(self.guestions) - 1:
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
                            await self.app.store.vk_api.send_message(
                                Message(
                                    peer_id=update.object.peer_id,
                                    text=f"Текущий счёт: Бот: {self.bot_points} Игроки: {self.users_points}",
                                )
                            )

                            await self.app.store.game.game_round(update, self.guestions[self.current_question].title)