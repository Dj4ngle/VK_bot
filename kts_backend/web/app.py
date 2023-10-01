from typing import Sequence, Callable

from aiohttp.web import (
    Application as AiohttpApplication,
    View as AiohttpView,
    Request as AiohttpRequest,
)
from pyparsing import Optional


#from kts_backend import __appname__, __version__
from kts_backend.web.config import Config, setup_config
from kts_backend.web.logger import setup_logging
from .urls import register_urls


#__all__ = ("ApiApplication",)

from kts_backend.store import Store, setup_store, Database


class Application(AiohttpApplication):
    config: Config | None = None
    store: Store | None = None
    database: Database | None = None

class Request(AiohttpRequest):
    #admin: Optional[Admin] = None

    @property
    def app(self) -> Application:
        return super().app()


class View(AiohttpView):
    @property
    def request(self) -> Request:
        return super().request

    @property
    def database(self):
        return self.request.app.database

    @property
    def store(self) -> Store:
        return self.request.app.store

    @property
    def data(self) -> dict:
        return self.request.get("data", {})

app = Application()



def setup_app(config_path: str) -> Application:
    setup_logging(app)
    setup_config(app, config_path)
    setup_store(app)
    return app