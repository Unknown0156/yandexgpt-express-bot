import logging
from functools import partial
from typing import Any
from http import HTTPStatus
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from pybotx import Bot, BotAccountWithSecret, IncomingMessage, build_command_accepted_response
from pybotx_fsm import FSMMiddleware
from elasticapm.contrib.starlette import make_apm_client, ElasticAPM

import settings
from collector import AIStates, collector, fsm
from redis import RedisRepo


#фильтрация логов uvicorn
class EndpointFilter(logging.Filter):
    def __init__(
        self,
        path: str,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._path = path

    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find(self._path) == -1

#фильтруем access логи
uvicorn_logger = logging.getLogger("uvicorn.access")
uvicorn_logger.addFilter(EndpointFilter(path="/health"))

#обработка ошибок бота
async def internal_error_handler(
    message: IncomingMessage,
    bot: Bot,
    e: Exception,
) -> None:
    logging.error(f"Bot internal error: {e}")
    await bot.answer_message(
        f"Bot internal error: {e} Please contact your system administrator",
        silent_response=False,
    )
    await message.state.fsm.drop_state()

#запуск бота
async def startup(bot: Bot) -> None:
    #запуск бота
    await bot.startup()
    #подключение редиса
    bot.state.redis_repo = await RedisRepo.init(
        dsn=settings.redis_dsn, prefix="yandexgpt-express-bot"
    )

#остановка бота
async def shutdown(bot: Bot) -> None:
    #остановка бота
    await bot.shutdown()
    #отключение редиса
    await bot.state.redis_repo.close()

#бот
bot = Bot(
    collectors=[collector],
    bot_accounts=[
        BotAccountWithSecret(
            host=settings.express_url,
            id=UUID(settings.express_bot_id),
            secret_key=settings.express_bot_key,
        ),
    ],
    exception_handlers={Exception: internal_error_handler},
    middlewares=[
        FSMMiddleware(
            [fsm], state_repo_key="redis_repo"
        ),
    ],
)

#приложение fastapi
express_bot = FastAPI()
#подключение elastic apm
if (settings.apm == "on"):
    #конфигурация elasticapm агента
    apm = make_apm_client({
        'SERVER_URL': settings.apm_server,
        'SERVICE_NAME': settings.apm_name,
        'TRANSACTIONS_IGNORE_PATTERNS': ['^GET /health'],
        'DEBUG': True,
    })
    express_bot.add_middleware(ElasticAPM, client=apm)
#подключение бота
express_bot.state.bot = bot
express_bot.add_event_handler("startup", partial(startup, bot))
express_bot.add_event_handler("shutdown", partial(shutdown, bot))

# На этот эндпоинт приходят команды BotX
# (сообщения и системные события).
@express_bot.post("/command")
async def command_handler(request: Request) -> JSONResponse:
    bot.async_execute_raw_bot_command(await request.json())
    return JSONResponse(
        build_command_accepted_response(),
        status_code=HTTPStatus.ACCEPTED,
    )

# К этому эндпоинту BotX обращается, чтобы узнать
# доступность бота и его список команд.
@express_bot.get("/status")
async def status_handler(request: Request) -> JSONResponse:
    status = await bot.raw_get_status(dict(request.query_params))
    return JSONResponse(status)

# На этот эндпоинт приходят коллбэки с результатами
# выполнения асинхронных методов в BotX.
@express_bot.post("/notification/callback")
async def callback_handler(request: Request) -> JSONResponse:
    await bot.set_raw_botx_method_result(await request.json())
    return JSONResponse(
        build_command_accepted_response(),
        status_code=HTTPStatus.ACCEPTED,
    )

#healthcheck
@express_bot.get("/health", status_code=200)
def healthcheck():
    return {"status": "ok"}