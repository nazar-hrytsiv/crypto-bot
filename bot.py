from telebot import TeleBot, types

from logger import logger
from config import cmc_key
from api import API
from db_worker import DB


class Bot():

    def __init__(self, token):
        '''
        Telegram bot for monitoring cryptocurrency prices

        :param token - bot's API key
        '''
        self.bot = TeleBot(token=token, exception_handler=logger)
        self.set_default_commands()
        self.api = API(name='CoinMarketCap', key=cmc_key)
        self.db = DB('data.db')
        logger.info('Bot started')
    

    def set_default_commands(self):
        '''
        Sets default commands for every private chat

        :return:
        '''
        default_commands = [
            types.BotCommand('start', '1'),
            types.BotCommand('settings', '1'),
            types.BotCommand('top', '1')
        ]
        # idk why but it works only when set_my_commands and get_my_commands have same params
        self.bot.set_my_commands(
            commands = default_commands,
            scope = types.BotCommandScopeAllPrivateChats(),
            language_code = 'en'
        )
        self.bot.get_my_commands(
            scope = types.BotCommandScopeAllPrivateChats(),
            language_code = 'en'
        )

    
    def start(self, message):
        '''
        Starts bot

        :param message - telegram message
        :return:
        '''
        logger.info('tg_id={}'.format(message.from_user.id))
        try:
            # add user in DB if not yet
            self.db.add_user(message.from_user.id)
            # greetings
            self.bot.send_message(
                chat_id = message.from_user.id,
                text = 'Hello, ' + message.from_user.first_name + ' 😊'
            )
        except Exception as e:
            logger.exception('message={}'.format(message))


    def top(self, message):
        '''
        Sends TOP of coins to the user

        :param message - telegram message
        :return:
        '''
        logger.info('tg_id={}'.format(message.from_user.id))
        try:
            # check for command argument - number
            try:
                coins_n = message.text.split()[1]
                # number [1-100]
                if coins_n.isdigit() and (int(coins_n)>=1 and int(coins_n)<=100):
                    coins_n = int(coins_n)
                # sends user tip about how to use command
                else:
                    error_message = '⚠️<b>warning;</b> The command you sent is incorrect. Command should have only 1 argument (number [1-100]) or None'
                    self.bot.send_message(
                        chat_id=message.from_user.id,
                        text=error_message,
                        parse_mode="HTML"
                    )
                    return
            # no argument - get from user settings
            except IndexError:
                coins_n = self.db.get_top_coins_number(message.from_user.id)
            response = self.api.latest_listings(limit=coins_n)
            # api error
            if response['status'] == 0:
                self.bot.send_message(
                    chat_id=message.from_user.id,
                    text='<b>⚠️error; Please, contact developer</b>',
                    parse_mode="HTML"
                )
            else:
                text_header = "<b>Coin</b> - <b>Price</b>"
                format_text = text_header + ('').join(response['coins'])
                self.bot.send_message(
                    chat_id=message.from_user.id,
                    text=format_text,
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.exception('message={}'.format(message))


    def top_all(self):
        '''
        Sends TOP coins to users who scheduled current time
        :return:
        '''
        logger.info('')
        try:
            response = self.api.latest_listings()
            # api error
            if response['status'] == 0:
                for user in self.db.get_recipients():
                    self.bot.send_message(
                        chat_id=user[0],
                        text='<b>⚠️error; Please, contact developer</b>',
                        parse_mode="HTML"
                    )
            else:
                text_header = "<b>Coin</b> - <b>Price</b>"
                for user in self.db.get_recipients():
                    try:
                        text = '*\n' + text_header + ('').join(response['coins'][:user[1]])
                        self.bot.send_message(
                            chat_id=user[0],
                            text=text,
                            parse_mode="HTML"
                        )
                    except Exception:
                        logger.exception('tg_id={}'.format(user[0]))
        except Exception as e:
            logger.exception(e)


    def settings(self, message):
        '''
        Interface for interacting with user's settings

        :param message - telegram message
        :return:
        '''
        logger.info('tg_id={}'.format(message.from_user.id))
        try:
            markup = types.InlineKeyboardMarkup()
            item1 = types.InlineKeyboardButton(text='Notifications', callback_data='markup_notify')
            item2 = types.InlineKeyboardButton(text='Coins', callback_data='settings_coins')
            markup.add(item1, item2)

            self.bot.send_message(
                chat_id=message.from_user.id,
                text='<b>Settings</b>',
                parse_mode='HTML',
                reply_markup=markup
            )
        except Exception as e:
            logger.exception('message={}'.format(message))

        
    def markup_notify(self, call):
        '''
        Interface for Interacting with user's notifications settings

        :param call - user's callback
        :return:
        '''
        logger.info('tg_id={}'.format(call.from_user.id))
        try:
            tg_id = call.from_user.id

            scheduler_notify = self.db.get_schedule(tg_id)
            text_scheduler = ''
            for hour in scheduler_notify:
                text_scheduler += '\n' + str(hour) + ':00'
            text = '⏰ <b>Notifications schedule</b>{}'.format(text_scheduler)

            markup = types.InlineKeyboardMarkup()
            item1 = types.InlineKeyboardButton(text='Edit Schedule', callback_data='edit_schedule')
            markup.add(item1)

            self.bot.edit_message_text(
                chat_id=tg_id, 
                message_id=call.message.id, 
                text=text,  
                parse_mode='HTML',
                reply_markup=markup
            )
        except Exception as e:
            logger.exception('call={}'.format(call))
            try:
                self.bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text='⚠️error⚠️\nPlease, contact developer')
            except Exception as e:
                logger.exception(e)


    def goCoinsSettings(self, call):
        '''
        User's coins settings

        :param call - user's callback
        :return:
        '''
        logger.info('tg_id={}'.format(call.from_user.id))
        try:
            tg_id = call.from_user.id
            coins_number = self.db.get_top_coins_number(tg_id) # number of TOP coins
            textHint = '\n\n<i>(click on command to copy)</i>\nChange: <code>/n n[1-100]</code>\nExample: <code>/n 99</code>'
            text = f'\n<b>TOP coins:</b> {coins_number}' + textHint

            self.bot.edit_message_text(
                chat_id=tg_id, 
                message_id=call.message.id, 
                text=text,  
                parse_mode='HTML',
                reply_markup=None
            )
        except Exception as e:
            logger.exception('call={}'.format(call))
            try:
                self.bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text='⚠️error; Please, contact developer')
            except Exception as e:
                logger.exception(e)


    def ChangeTopCoinsNumber(self, message):
        '''
        Changes number of top coins in user's settings

        :param message - telegram message
        '''
        try:
            args = message.text.split()
            if len(args) == 2:
                if args[1].isdigit():
                    n = int(args[1])
                    if n >= 1 and n <= 100:
                        if self.db.save_settings(tg_id=message.from_user.id, field="coins_number", val=n):
                            self.bot.send_message(
                                chat_id=message.from_user.id,
                                text='✅success'
                            )
                            return
            self.bot.send_message(
                chat_id=message.from_user.id,
                text='❌failure'
            )
        except Exception:
            logger.exception('message={}'.format(message))


    def edit_schedule(self, message):
        '''
        Edits notification schedule

        :param message - telegram message
        :return:
        '''
        logger.info('tg_id={}'.format(message.from_user.id))
        try:
            cmd_args = message.text.split()
            length = len(cmd_args)
            text_error = '❌<b>Please, check you are using command correcly:</b>\nmax 24 numbers;\nonly numbers;\nnumbers between 0 and 23 including them;'
            if length == 1 or length > 25:
                self.bot.send_message(
                    chat_id = message.from_user.id,
                    text = text_error,
                    parse_mode='HTML'
                )
            else:
                args = []
                for n in cmd_args[1:]:
                    if n.isdigit():
                        n = int(n)
                        if n>=0 and n<=23:
                            args.append(n)
                args = set(args) # get rid of same numbers
                status = ''
                if len(args):
                    status = '✅success' if self.db.edit_schedule(message.from_user.id, args) else text_error
                else:
                    status = text_error
                self.bot.send_message(
                    chat_id = message.from_user.id,
                    text = status,
                    parse_mode='HTML'
                )
        except Exception:
            logger.exception('message={}'.format(message))


    def helper(self, call):
        '''
        Helps user with some difficulties when interacting with interface

        :param call - user's callback
        :return:
        '''
        logger.info('tg_id={}'.format(call.from_user.id))
        try:
            tg_id = call.from_user.id

            if call.data == 'edit_schedule':
                text = '⚠️The notification schedule will be cleared. <b>List the hours (max 24 numbers)</b> at which you want to receive notifications.\n\n<b>Usage:</b> <code>/schedule hours</code>\ne.g. <code>/schedule 0 8 12 18</code> is schedule for 00:00, 8:00, 12:00 and 18:00'

                self.bot.edit_message_text(
                    chat_id=tg_id, 
                    message_id=call.message.id, 
                    text=text,  
                    parse_mode='HTML',
                    reply_markup=None
                )
        except:
            pass