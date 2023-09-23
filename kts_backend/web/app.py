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


__all__ = ("ApiApplication",)

from kts_backend.store import Store, setup_store


class Application(AiohttpApplication):
    config: Sequence[Config] = None
    store: Sequence[Store] = None

app = Application()




def setup_app(config_path: str) -> Application:
    setup_logging(app)
    setup_config(app, config_path)
    setup_store(app)
    return app