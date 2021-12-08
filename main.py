import telebot
from telebot import types
from config import *
from forex_python.bitcoin import BtcConverter
from coinbase.wallet.client import Client
from flask import Flask, request
import aiogram
import os
import logging
import psycopg2 as pg
import qrcode

client = Client(API_KEY, SECRET_API_KEY, api_version='2021-12-01')
primary_account = client.get_primary_account()

connection = pg.connect(DB_URI, sslmode='require')
cur = connection.cursor()

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
logger = telebot.logger
logger.setLevel(logging.DEBUG)
b = BtcConverter()


# Команда start
@bot.message_handler(commands=["start"])
def start(m, res=False):
    # Добавляем две кнопки
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    cur.execute('SELECT DISTINCT city FROM public.products;')
    rows = cur.fetchall()
    for row in rows:
        item = types.KeyboardButton(''.join(row[0]))
        markup.add(item)
    # cur.execute(f'INSERT INTO users(id, last_trans) VALUES ({m.chat.id}, false);')
    # connection.commit()
    bot.send_message(m.chat.id, "Выбери город, в котором планируешь сделать заказ!", reply_markup=markup)


@bot.message_handler(content_types=["text"])
def handle_city(message: types.Message):
    markup_inline = types.InlineKeyboardMarkup()
    cur.execute(f"SELECT DISTINCT category FROM products WHERE city = '{message.text.strip()}';")
    rows = cur.fetchall()
    if not rows:
        bot.send_message(message.chat.id, "К сожалению, вашего города еще нет в нашем списке 😔 \n"
                                          "Выбери из предложенных в меню!")
    else:
        for row in rows:
            item = types.InlineKeyboardButton(text=''.join(row[0]),
                                              callback_data=f'city_{"".join(row[0])}_{message.text.strip()}')
            markup_inline.add(item)
        bot.send_message(message.chat.id, "Выбери категорию, которая тебя интересует!", reply_markup=markup_inline)


# Получение сообщений от юзера
@bot.callback_query_handler(lambda c: True)
def callback_inline_category(callback_query: types.CallbackQuery):
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
            bot.send_photo(callback_query.from_user.id, img,
                           f'{row[0]}\nЦена за одну штуку: {row[1]} RUB ≈ {round(b.convert_to_btc((row[1]), "RUB"), 7)} ₿\n'
                           f'Выберите сколько товара Вы хотите купить',
                           reply_markup=markup_inline)
    if callback_query.data.split('_')[0] == 'id':
        amount = callback_query.data.split('_')[2]
        id = callback_query.data.split('_')[1]
        addr = primary_account.create_address()['address']
        cur.execute(f"SELECT price, name FROM products WHERE id = {id};")
        row = cur.fetchone()
        msg = f"<b>Вы выбрали {row[1]} для покупки в Москве</b> \n\n" \
              "Вам будет необходимо перевести по адресу ниже необходимую" \
              " сумму ≈" + f'<b>{round(b.convert_to_btc(row[0][0], "RUB"), 7) * int(amount)} ₿</b>' + \
              " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n"
        bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
        bot.send_message(callback_query.from_user.id, f'<code>{addr}</code>', parse_mode="HTML")
        img = qrcode.make(addr)
        img.save('qr.png')
        bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))


@server.route(f'/{TOKEN}', methods=['POST'])
def redirect_message():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '!', 200


# Запускаем бота
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    server.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
