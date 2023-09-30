import typing

from kts_backend.store.database.database import Database

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application
class Store:
    def __init__(self, app: "Application", *args, **kwargs):
        from kts_backend.users.accessor import UserAccessor

        self.user = UserAccessor(app)

        from kts_backend.store.bot.manager import BotManager
        from kts_backend.store.vk_api.accessor import VkApiAccessor
        from kts_backend.store.bot.game_manager import GameManager

        self.vk_api = VkApiAccessor(app)
        self.bots_manager = BotManager(app)
        self.game_manager = GameManager(app)

def setup_store(app: "Application"):
    app.store = Store(app)
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)