from http import HTTPStatus
import logging
from fastapi import Request, Response
from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from .routers import public, admin, web
from pathlib import Path
from .repository import employee, weekend

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Updater
from .bot import bot
BASE_DIR = Path(__file__).resolve().parent
logger = logging.getLogger(__name__)

app = FastAPI(title="Escalas NOC API")
app.include_router(public.router)
app.include_router(admin.router)
app.include_router(web.router)
app.mount("/static", StaticFiles(directory=str(Path(BASE_DIR, './frontend/static'))), name="static")

@app.get("/status")
async def status():
    await bot.send_folgas_by_day()
    return Response(content="OK", status_code=HTTPStatus.OK)

@app.get("/domingo/{id}")
async def status(id : int):
    await bot.send_week(id)
    return Response(content="OK", status_code=HTTPStatus.OK)

@app.on_event("startup")
async def startup_event():
    try:
        await bot.app.initialize()
        await bot.app.start()
        await bot.app.updater.start_polling()
    except Exception as exc:
        logger.warning("Telegram bot não inicializado no startup: %s", exc)
