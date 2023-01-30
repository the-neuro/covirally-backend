import sentry_sdk

from fastapi import FastAPI

from app.config import settings, AppEnvTypes
from app.events import create_start_app_handler, create_stop_app_handler


if settings.app_env not in (AppEnvTypes.DEV, AppEnvTypes.TEST):
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,
    )


def get_application() -> FastAPI:
    application = FastAPI(version="1.0.0")

    application.add_event_handler(
        "startup",
        create_start_app_handler(),
    )
    application.add_event_handler(
        "shutdown",
        create_stop_app_handler(),
    )

    return application


app = get_application()
