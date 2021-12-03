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
    cur.execute(f'SELECT category FROM products WHERE city = "{message.text.strip()}" ')
    rows = cur.fetchall()
    for row in rows:
        item = types.KeyboardButton(row)
        markup_inline.add(item)
    bot.send_message(message.chat.id, "Выбери категорию, которая тебя интересует!", reply_markup=markup_inline)


# # Получение сообщений от юзера
# @bot.message_handler(content_types=["text"])
# def handle_category(message: types.Message):
#     markup_inline = types.InlineKeyboardMarkup()
#
#     if message.text.strip() == 'category 1':
#         rows = cur.execute("SELECT product, price FROM products WHERE category = 'category 1';").fetchall()
#         for row in rows:
#             img = open('data/' + ''.join(row[1]) + '.png', 'rb')
#             item_buy = types.InlineKeyboardButton(text='Купить', callback_data=f'{row[0]}')
#             markup_inline.keyboard.clear()
#             markup_inline.add(item_buy)
#             bot.send_photo(message.chat.id, img,
#                            f'Цена: {row[2]} RUB ≈ {round(b.convert_to_btc((row[2]), "RUB"), 7)} ₿',
#                            reply_markup=markup_inline)
#     elif message.text.strip() == 'Питер':
#         rows = cur.execute("SELECT id, product, cost FROM public.products WHERE city = 'Piter';").fetchall()
#         for row in rows:
#             img = open('data/' + ''.join(row[1]) + '.png', 'rb')
#             item_buy = types.InlineKeyboardButton(text='Купить', callback_data=f'{row[0]}')
#             markup_inline.keyboard.clear()
#             markup_inline.add(item_buy)
#             bot.send_photo(message.chat.id, img,
#                            f'Цена: {row[2]} RUB ≈ {round(b.convert_to_btc((row[2]), "RUB"), 7)} ₿',
#                            reply_markup=markup_inline)
#     else:
#         bot.send_message(message.chat.id, "К сожалению, вашего города еще нет в нашем списке 😔")
#
#
# @bot.callback_query_handler(lambda c: c.data)
# def callback_inline(callback_query: types.CallbackQuery):
#     if callback_query.data == '1':
#         addr = primary_account.create_address()['address']
#         row = cur.execute("SELECT cost FROM public.products WHERE id = 1;").fetchall()
#         msg = "<b>Вы выбрали Машинку для покупки в Москве</b> \n\n" \
#               "Вам будет необходимо перевести по адресу ниже необходимую" \
#               " сумму ≈" + f'<b>{round(b.convert_to_btc(row[0][0], "RUB"), 7)} ₿</b>' + \
#               " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n" + f'<code>{addr}</code>'
#         bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
#         img = qrcode.make(addr)
#         img.save('qr.png')
#         bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))
#     if callback_query.data == '2':
#         addr = primary_account.create_address()['address']
#         row = cur.execute("SELECT cost FROM public.products WHERE id = 2;")
#         msg = "<b>Вы выбрали Кораблик для покупки в Москве</b> \n\n" \
#               "Вам будет необходимо перевести по адресу ниже необходимую" \
#               " сумму ≈" + f'<b>{round(b.convert_to_btc(row[0][0], "RUB"), 7)} ₿</b>' + \
#               " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n" + f'<code>{addr}</code>'
#         bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
#         img = qrcode.make(addr)
#         img.save('qr.png')
#         bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))
#     if callback_query.data == '3':
#         addr = primary_account.create_address()['address']
#         row = cur.execute("SELECT cost FROM public.products WHERE id = 3;").fetchall()
#         msg = "<b>Вы выбрали Вертолетик для покупки в Москве</b> \n\n" \
#               "Вам будет необходимо перевести по адресу ниже необходимую" \
#               " сумму ≈" + f'<b>{round(b.convert_to_btc(row[0][0], "RUB"), 7)} ₿</b>' + \
#               " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n" + f'<code>{addr}</code>'
#         bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
#         img = qrcode.make(addr)
#         img.save('qr.png')
#         bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))
#     if callback_query.data == '4':
#         addr = primary_account.create_address()['address']
#         row = cur.execute("SELECT cost FROM public.products WHERE id = 4;").fetchall()
#         msg = "<b>Вы выбрали Машинку для покупки в Питере</b> \n\n" \
#               "Вам будет необходимо перевести по адресу ниже необходимую" \
#               " сумму ≈" + f'<b>{round(b.convert_to_btc(row[0][0], "RUB"), 7)} ₿</b>' + \
#               " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n" + f'<code>{addr}</code>'
#         bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
#         img = qrcode.make(addr)
#         img.save('qr.png')
#         bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))
#     if callback_query.data == '5':
#         addr = primary_account.create_address()['address']
#         row = cur.execute("SELECT cost FROM public.products WHERE id = 5;").fetchall()
#         msg = "<b>Вы выбрали Кораблик для покупки в Питере</b> \n\n" \
#               "Вам будет необходимо перевести по адресу ниже необходимую" \
#               " сумму ≈" + f'<b>{round(b.convert_to_btc(row[0][0], "RUB"), 7)} ₿</b>' + \
#               " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n" + f'<code>{addr}</code>'
#         bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
#         img = qrcode.make(addr)
#         img.save('qr.png')
#         bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))
#     if callback_query.data == '6':
#         addr = primary_account.create_address()['address']
#         row = cur.execute("SELECT cost FROM public.products WHERE id = 6;").fetchall()
#         msg = "<b>Вы выбрали Вертолетик для покупки в Питере</b> \n\n" \
#               "Вам будет необходимо перевести по адресу ниже необходимую" \
#               " сумму ≈" + f'<b>{round(b.convert_to_btc(row[0][0], "RUB"), 7)} ₿</b>' + \
#               " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n" + f'<code>{addr}</code>'
#         bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
#         img = qrcode.make(addr)
#         img.save('qr.png')
#         bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))


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
