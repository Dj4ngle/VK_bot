import json
import random
import typing
from typing import Optional

from aiohttp import TCPConnector
from aiohttp.client import ClientSession
from vk_api.keyboard import VkKeyboard

from kts_backend.base.base_accessor import BaseAccessor
from kts_backend.store.vk_api.dataclasses import Message, Update, UpdateObject, User
from kts_backend.store.vk_api.poller import Poller
from kts_backend.users.schema import UserSchema

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application

API_PATH = "https://api.vk.com/method/"


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: ClientSession | None = None
        self.key: str | None = None
        self.server: str | None = None
        self.poller: Poller | None = None
        self.ts: int | None = None
        self.capitan_id: int | None = None

    async def connect(self, app: "Application"):
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))
        try:
            await self._get_long_poll_service()
        except Exception as e:
            self.logger.error("Exception", exc_info=e)
        self.poller = Poller(app.store)
        self.logger.info("start polling")
        await self.poller.start()

    async def disconnect(self, app: "Application"):
        if self.session:
            await self.session.close()
        if self.poller:
            await self.poller.stop()

    @staticmethod
    def _build_query(host: str, method: str, params: dict) -> str:
        url = host + method + "?"
        if "v" not in params:
            params["v"] = "5.131"
        url += "&".join([f"{k}={v}" for k, v in params.items()])
        return url

    async def _get_long_poll_service(self):
        async with self.session.get(
            self._build_query(
                host=API_PATH,
                method="groups.getLongPollServer",
                params={
                    "group_id": self.app.config.bot.group_id,
                    "access_token": self.app.config.bot.token,
                },
            )
        ) as resp:
            data = (await resp.json())["response"]
            self.logger.info(data)
            self.key = data["key"]
            self.server = data["server"]
            self.ts = data["ts"]
            self.logger.info(self.server)

    async def poll(self):
        async with self.session.get(
            self._build_query(
                host=self.server,
                method="",
                params={
                    "act": "a_check",
                    "key": self.key,
                    "wait": 10,
                    "mode": 2,
                    "ts": self.ts
                },
            )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)
            self.ts = data["ts"]
            raw_updates = data.get("updates", [])
            updates = []
            for update in raw_updates:
                if update["type"] == "message_new":
                    updates.append(
                        Update(
                            type=update["type"],
                            object=UpdateObject(
                                id=update["object"]["message"]["id"],
                                user_id=update["object"]["message"]["from_id"],
                                body=update["object"]["message"],
                            ),
                        )
                    )
            await self.app.store.bots_manager.handle_updates(updates)

    async def send_message_start(self, message: Message) -> None:

        json_button = '{"inline": true, "buttons": [[{"action": {"type": "text","label": "Начать"}},{"action": {"type": "text","label": "Таблица игроков"}}]]}'

        async with self.session.get(
            self._build_query(
                API_PATH,
                "messages.send",
                params={
                    #"user_id": message.user_id,
                    "random_id": random.randint(1, 2**32),
                    "peer_id": message.peer_id,
                    "message": message.text,
                    "access_token": self.app.config.bot.token,
                    "keyboard": json_button
                },
            )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)

    async def send_message_start_game(self, message: Message) -> None:

        users_list = await self.get_all_users_from_chat(message.peer_id)
        random_user = random.choice(users_list)
        self.capitan_id = random_user.id
        message_to_user = f"Капитан команды @id{random_user.id} ({random_user.first_name} {random_user.last_name}!)"

        json_button = '{"inline": true, "buttons": [[{"action": {"type": "text","label": "Старт игры!!!"}}]]}'

        async with self.session.get(
            self._build_query(
                API_PATH,
                "messages.send",
                params={
                    "random_id": random.randint(1, 2**32),
                    "peer_id": message.peer_id,
                    "message": message_to_user,
                    "access_token": self.app.config.bot.token,
                    "keyboard": json_button
                },
            )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)
    async def get_all_users_from_chat(self, peer_id) -> None:

            async with self.session.get(
                self._build_query(
                    API_PATH,
                    "messages.getConversationMembers",
                    params={
                        "peer_id": peer_id,
                        "access_token": self.app.config.bot.token,
                        "fields": "first_name",
                    },
                )
            ) as resp:
                users = await resp.json()
            self.logger.info(users)
            list_users = []
            for user in users["response"]["profiles"]:

                list_users.append(User(
                    id=user['id'],
                    first_name=user['first_name'],
                    last_name=user['last_name'],
                ))
            return list_users


    async def send_message_question(self, message: Message, question_number) -> None:

        questions = ["«Всегда открыта, всегда закрыта» — такой рекламный слоган появился в 1899 году на здании одного нью-йоркского ресторана. Что впервые там было установлено?",
                     "Карикатурист Эшли Бриллиант справедливо полагает, что жить на земле дорого, зато каждый из нас ежегодно получает бесплатный круиз. Что это за круиз?"]

        answers = ["вращающаяся дверь", "вокруг солнца"]

        async with self.session.get(
            self._build_query(
                API_PATH,
                "messages.send",
                params={
                    "random_id": random.randint(1, 2**32),
                    "peer_id": message.peer_id,
                    "message": questions[question_number],
                    "access_token": self.app.config.bot.token,
                },
            )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)