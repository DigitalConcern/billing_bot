from aiogram import *
from telebot import types
from config import *
from forex_python.bitcoin import BtcConverter
from coinbase.wallet.client import Client
from flask import Flask, request
import os
import logging
import psycopg2 as pg
import qrcode

client = Client(API_KEY, SECRET_API_KEY, api_version='2021-12-01')
account = client.get_account('BTC')

connection = pg.connect(DB_URI, sslmode='require')
cur = connection.cursor()

bot = Bot(TOKEN)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.DEBUG)

b = BtcConverter()
user_id = 0


# Команда start
@dp.message_handler(commands=["start"])
async def start(m, res=False):
    # Добавляем две кнопки
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    cur.execute('SELECT DISTINCT city FROM products;')
    rows = cur.fetchall()
    for row in rows:
        item = types.KeyboardButton(''.join(row[0]))
        markup.add(item)
        await bot.send_message(m.chat.id, ''.join(row[0]))
    # cur.execute(f'INSERT INTO users(id, last_trans) VALUES ({m.chat.id}, false);')
    # connection.commit()
    await bot.send_message(m.chat.id, "Выбери город, в котором планируешь сделать заказ!")


@dp.message_handler(content_types=["text"])
async def handle_city(message: types.Message):
    markup_inline = types.InlineKeyboardMarkup()
    cur.execute(f"SELECT DISTINCT category FROM products WHERE city = '{message.text.strip()}';")
    rows = cur.fetchall()
    if not rows:
        await bot.send_message(message.chat.id, "К сожалению, вашего города еще нет в нашем списке 😔 \n"
                                                "Выбери из предложенных в меню!")
    else:
        for row in rows:
            item = types.InlineKeyboardButton(text=''.join(row[0]),
                                              callback_data=f'city_{"".join(row[0])}_{message.text.strip()}')
            markup_inline.add(item)
        await bot.send_message(message.chat.id, "Выбери категорию, которая тебя интересует!",
                               reply_markup=markup_inline)


# Получение сообщений от юзера
@dp.callback_query_handler(lambda c: c.data)
async def callback_inline_category(callback_query: types.CallbackQuery):
    if callback_query.data.split('_')[0] == 'city':
        city = callback_query.data.split('_')[2]
        category = callback_query.data.split('_')[1]
        markup_inline = types.InlineKeyboardMarkup()
        cur.execute(f"SELECT name, price, id FROM products WHERE category = '{category}' AND city = '{city}';")
        rows = cur.fetchall()
        for row in rows:
            markup_inline.keyboard.clear()
            img = open('data/' + ''.join(row[0]) + '.png', 'rb')
            item_buy1 = types.InlineKeyboardButton(text='1', callback_data=f'id_{row[2]}' + '_1')
            item_buy3 = types.InlineKeyboardButton(text='3', callback_data=f'id_{row[2]}' + '_3')
            item_buy5 = types.InlineKeyboardButton(text='5', callback_data=f'id_{row[2]}' + '_5')
            item_buy10 = types.InlineKeyboardButton(text='10', callback_data=f'id_{row[2]}' + '_10')
            markup_inline.row(item_buy1, item_buy3, item_buy5, item_buy10)
            await bot.send_photo(callback_query.from_user.id, img,
                                 f'{row[0]}\nЦена за одну штуку: {row[1]} RUB ≈ {round(b.convert_to_btc((row[1]), "RUB"), 7)} ₿\n'
                                 f'Выберите сколько товара Вы хотите купить',
                                 reply_markup=markup_inline)
        callback_query.data = ''

    if callback_query.data.split('_')[0] == 'id':
        amount = callback_query.data.split('_')[2]
        id = callback_query.data.split('_')[1]
        addr = account.create_address()['address']
        cur.execute(f"SELECT price, name, city FROM products WHERE id = {id};")
        row = cur.fetchone()
        value = round(b.convert_to_btc(row[0], "RUB"), 7) * int(amount)
        msg = f"<b>Вы выбрали {row[1]} в количестве {amount} штук(а) для покупки в {row[2]}</b> \n\n" \
              "Вам нужно в течение 15 минут перевести по адресу ниже необходимую" \
              " сумму ≈" + f'<b>{value} ₿</b>' + \
              " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n"
        await bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
        await bot.send_message(callback_query.from_user.id, f'<code>{addr}</code>', parse_mode="HTML")
        img = qrcode.make(addr)
        img.save('qr.png')
        await bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))

        # ioloop = asyncio.get_event_loop()
        # task = ioloop.create_task(accept(addr, value, callback_query.from_user.id))
        # ioloop.run_until_complete(asyncio.wait(task))
        # ioloop.close()

        callback_query.data = ''

    #     markup_inline = types.InlineKeyboardMarkup()
    #     item_yes = types.InlineKeyboardButton(text='Да', callback_data='ans_yes')
    #     item_no = types.InlineKeyboardButton(text='Нет', callback_data='ans_no')
    #     markup_inline.row(item_yes, item_no)
    #     bot.send_message(callback_query.from_user.id, 'Подтвердить покупку?', reply_markup=markup_inline, parse_mode="HTML")
    #
    # if callback_query.data.split('_')[0] == 'ans':
    #     if callback_query.data.split('_')[1] == 'yes':

    #     if callback_query.data.split('_')[1] == 'no':
    #         bot.send_message(callback_query.from_user.id, str(len(last_msgs)))
    #         for msg in last_msgs:
    #             bot.delete_message(callback_query.from_user.id, msg)


# @server.route(f'/{TOKEN}', methods=['POST'])
# def redirect_message():
#     json_string = request.get_data().decode('utf-8')
#     update = telebot.types.Update.de_json(json_string)
#     bot.process_new_updates([update])
#     return '!', 200


# async def accept(address, sum, user):
#     ctr = 0
#     conf = {}
#     while ctr != 900 or conf["data"]["confirmed_balance"] != sum:
#         conf = requests.get(f"https://chain.so/api/v2/get_address_balance/BTC/{address}/500")
#         await asyncio.sleep(0.1)
#     if conf["data"]["confirmed_balance"] == sum:
#         cur.execute(f'INSERT INTO users(id, trans) VALUES ({user}, true);')
#         connection.commit()


# Run after startup
async def on_startup(dp):
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL)


# Run before shutdown
async def on_shutdown(dp):
    logging.warning('Bye! Shutting down webhook connection')


# Запускаем бота
if __name__ == '__main__':
    executor.start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=int(os.environ.get("PORT", 5000)))

    # bot.remove_webhook()
    # bot.set_webhook(url=APP_URL)
    # server.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
