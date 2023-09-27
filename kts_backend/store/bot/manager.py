import typing, random, time
from logging import getLogger

from sqlalchemy import select

from kts_backend.questions.models import QuestionModel
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
        self.guestions: []

    async def handle_updates(self, updates: list[Update]):

        if not updates:
            return
        else:
            for update in updates:
                # Команда для запуска бота
                if update.object.body["text"] == "/start":
                    self.bot_started = True
                    self.game_started = False
                    keyboard = VkKeyboard(inline=True)
                    keyboard.add_button("Начать", VkKeyboardColor.POSITIVE)
                    keyboard.add_button("Таблица игроков", VkKeyboardColor.NEGATIVE)

                    await self.app.store.vk_api.send_keyboard_message(
                        Message(
                            peer_id=update.object.peer_id,
                            text="Привет!",
                        ),
                        keyboard.get_keyboard(),
                    )

                # Проверка, что собщение является командой боту
                elif update.object.body["text"].startswith(f'[club{self.app.config.bot.group_id}|@') and self.bot_started:

                    index = update.object.body["text"].index(" ")
                    command = update.object.body["text"][index + 1:]

                    if command == 'Начать' and not self.game_started:
                        self.game_started = True
                        # Исполнение команды начало игры
                        self.users_list = await self.app.store.vk_api.get_all_users_from_chat(update.object.body["peer_id"])
                        random_user = random.choice(self.users_list)
                        self.capitan_id = random_user.id
                        message_to_user = f"Капитан команды @id{random_user.id} ({random_user.first_name} {random_user.last_name}!)"

                        keyboard = VkKeyboard(inline=True)
                        keyboard.add_button("Старт игры!!!", VkKeyboardColor.PRIMARY)

                        await self.app.store.vk_api.send_keyboard_message(
                            Message(
                                peer_id=update.object.peer_id,
                                text=message_to_user,
                            ),
                            keyboard.get_keyboard(),
                        )

                    elif update.object.user_id == self.capitan_id and self.game_started:
                        if command == 'Старт игры!!!':

                            async with self.app.database.session() as session:
                                res = await session.execute(select(QuestionModel))
                                self.guestions = res.scalars().all()


                            # Старт вопросов после решения капитана о начале игры
                            await self.app.store.game.game_round(update, self.guestions[self.current_question].title)

                        elif self.game_started:
                            # Информирование всех, кто выбран отвечающим для данного вопроса
                            for user in self.users_list:
                                if user.first_name+' '+user.last_name == command:
                                    self.answerer_id = user.id
                            message_to_user = f"@id{self.answerer_id} ({command})  выбран отвечающим"

                            await self.app.store.vk_api.send_message(
                                Message(
                                    peer_id=update.object.peer_id,
                                    text=message_to_user,
                                ),
                            )

                elif update.object.user_id == self.answerer_id and self.game_started:
                # Проверка правильности ответа на вопрос
                    if update.object.body["text"].lower() == self.guestions[self.current_question].answer:
                        await self.app.store.vk_api.send_message(
                            Message(
                                peer_id=update.object.peer_id,
                                text="Ответ правильный!!!!!!",
                            )
                        )
                        self.users_points+=1
                    else:
                        await self.app.store.vk_api.send_message(
                            Message(
                                peer_id=update.object.peer_id,
                                text=f"Ответ неправильный!!! Правильный ответ: {self.guestions[self.current_question].answer}",
                            )
                        )
                        self.bot_points+=1
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