import logging
from aiohttp import web
from aiogram import Bot,Dispatcher,types

from config import TOKEN,WEBHOOK_URL,WEBHOOK_PATH,PORT
from database import connect

from handlers import start,games,quests,admin

logging.basicConfig(level=logging.INFO)

bot=Bot(token=TOKEN)
dp=Dispatcher()

dp.include_router(start.router)
dp.include_router(games.router)
dp.include_router(quests.router)
dp.include_router(admin.router)

async def handle(request):

    update=types.Update(**await request.json())

    await dp.feed_update(bot,update)

    return web.Response()

async def startup(app):

    await connect()

    await bot.set_webhook(WEBHOOK_URL+WEBHOOK_PATH)

async def shutdown(app):

    await bot.session.close()

app=web.Application()

app.router.add_post(WEBHOOK_PATH,handle)

app.on_startup.append(startup)
app.on_shutdown.append(shutdown)

if __name__=="__main__":

    web.run_app(app,host="0.0.0.0",port=PORT)