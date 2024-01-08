import schedule
import threading
import time
from datetime import datetime

from api import API
from logger import logger
from config import token
from bot import Bot

bot = Bot(token)

@bot.bot.message_handler(commands=['start', 'top', 'settings', 'schedule', 'n'])
def message_handler(message):
    try:
        if message.text == '/start':
            bot.start(message)
        elif message.text.startswith('/top'):
            bot.top(message)
        elif message.text == '/settings':
            bot.settings(message)
        elif message.text.startswith('/schedule'):
            bot.edit_schedule(message)
        elif message.text.startswith('/n'):
            bot.ChangeTopCoinsNumber(message)
        else:
            logger.warning('No command handler; message={}'.format(message))
    except Exception as e:
        logger.exception(e)


@bot.bot.callback_query_handler(lambda call: True)
def callback_handler(call):
    try:
        if call.data.startswith('markup'):
            if call.data == 'markup_notify':
                bot.markup_notify(call)
        elif call.data == 'settings_coins':
            bot.goCoinsSettings(call)
        else:
            bot.helper(call)
    except Exception as e:
        logger.exception(e)


# waits until next round hour
def wait_until_next_hour():
    dt = datetime.fromtimestamp(time.time())
    dt = dt.replace(hour=dt.hour+1, minute=0, second=0, microsecond=0)
    t = datetime.timestamp(dt)
    while True:
        if time.time() >= t:
            break


# sends messages to all user whose schedule coincides with the current time
def run_schedule():
    try:
        wait_until_next_hour()
        bot.top_all()
        schedule.every(1).hour.do(bot.top_all)
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        logger.exception(e)


if __name__ == "__main__":
    t1 = threading.Thread(target=bot.bot.polling)
    t2 = threading.Thread(target=run_schedule)
    t1.start()
    t2.start()