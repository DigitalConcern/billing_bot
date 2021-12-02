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

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
logger = telebot.logger
logger.setLevel(logging.DEBUG)
b = BtcConverter()


# Команда start
@bot.message_handler(commands=["start"])
async def start(m, res=False):
    # Добавляем две кнопки
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Москва")
    item2 = types.KeyboardButton("Питер")
    markup.add(item1)
    markup.add(item2)
    bot.send_message(m.chat.id, "Выбери свой город!", reply_markup=markup)


# Получение сообщений от юзера
@bot.message_handler(content_types=["text"])
async def handle_text(message: types.Message):
    markup_inline = types.InlineKeyboardMarkup()

    if message.text.strip() == 'Москва':
        rows =  db_exec("SELECT id, product, cost FROM public.products WHERE city = 'Moscow';")

        for row in rows:
            img = open('data/' + ''.join(row[1]) + '.png', 'rb')
            item_buy = types.InlineKeyboardButton(text='Купить', callback_data=f'{row[0]}')
            markup_inline.inline_keyboard.clear()
            markup_inline.add(item_buy)
            bot.send_photo(message.chat.id, img, f'Цена: {row[2]} RUB ≈ {round(b.convert_to_btc((row[2]), "RUB"), 7)} ₿',\
                                 reply_markup=markup_inline)
    elif message.text.strip() == 'Питер':
        rows =  db_exec("SELECT id, product, cost FROM public.products WHERE city = 'Piter';")
        for row in rows:
            img = open('data/' + ''.join(row[1]) + '.png', 'rb')
            item_buy = types.InlineKeyboardButton(text='Купить', callback_data=f'{row[0]}')
            markup_inline.inline_keyboard.clear()
            markup_inline.add(item_buy)
            bot.send_photo(message.chat.id, img, f'Цена: {row[2]} RUB ≈ {round(b.convert_to_btc((row[2]), "RUB"), 7)} ₿',\
                                 reply_markup=markup_inline)
    else:
        bot.send_message(message.chat.id, "К сожалению, вашего города еще нет в нашем списке 😔")


@bot.callback_query_handler(lambda c: c.data)
async def callback_inline(callback_query: types.CallbackQuery):
    if callback_query.data == '1':
        addr = primary_account.create_address()['address']
        row =  db_exec("SELECT cost FROM public.products WHERE id = 1;")
        msg = "<b>Вы выбрали Машинку для покупки в Москве</b> \n\n" \
              "Вам будет необходимо перевести по адресу ниже необходимую" \
              " сумму ≈" + f'<b>{round(b.convert_to_btc(row[0][0], "RUB"), 7)} ₿</b>' +\
              " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n" + f'<code>{addr}</code>'
        bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
        img = qrcode.make(addr)
        img.save('qr.png')
        bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))
    if callback_query.data == '2':
        addr = primary_account.create_address()['address']
        row =  db_exec("SELECT cost FROM public.products WHERE id = 2;")
        msg = "<b>Вы выбрали Кораблик для покупки в Москве</b> \n\n" \
              "Вам будет необходимо перевести по адресу ниже необходимую" \
              " сумму ≈" + f'<b>{round(b.convert_to_btc(row[0][0], "RUB"), 7)} ₿</b>' +\
              " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n" + f'<code>{addr}</code>'
        bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
        img = qrcode.make(addr)
        img.save('qr.png')
        bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))
    if callback_query.data == '3':
        addr = primary_account.create_address()['address']
        row =  db_exec("SELECT cost FROM public.products WHERE id = 3;")
        msg = "<b>Вы выбрали Вертолетик для покупки в Москве</b> \n\n" \
              "Вам будет необходимо перевести по адресу ниже необходимую" \
              " сумму ≈" + f'<b>{round(b.convert_to_btc(row[0][0], "RUB"), 7)} ₿</b>' +\
              " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n" + f'<code>{addr}</code>'
        bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
        img = qrcode.make(addr)
        img.save('qr.png')
        bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))
    if callback_query.data == '4':
        addr = primary_account.create_address()['address']
        row =  db_exec("SELECT cost FROM public.products WHERE id = 4;")
        msg = "<b>Вы выбрали Машинку для покупки в Питере</b> \n\n" \
              "Вам будет необходимо перевести по адресу ниже необходимую" \
              " сумму ≈" + f'<b>{round(b.convert_to_btc(row[0][0], "RUB"), 7)} ₿</b>' +\
              " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n" + f'<code>{addr}</code>'
        bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
        img = qrcode.make(addr)
        img.save('qr.png')
        bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))
    if callback_query.data == '5':
        addr = primary_account.create_address()['address']
        row =  db_exec("SELECT cost FROM public.products WHERE id = 5;")
        msg = "<b>Вы выбрали Кораблик для покупки в Питере</b> \n\n" \
              "Вам будет необходимо перевести по адресу ниже необходимую" \
              " сумму ≈" + f'<b>{round(b.convert_to_btc(row[0][0], "RUB"), 7)} ₿</b>' +\
              " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n" + f'<code>{addr}</code>'
        bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
        img = qrcode.make(addr)
        img.save('qr.png')
        bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))
    if callback_query.data == '6':
        addr = primary_account.create_address()['address']
        row =  db_exec("SELECT cost FROM public.products WHERE id = 6;")
        msg = "<b>Вы выбрали Вертолетик для покупки в Питере</b> \n\n" \
              "Вам будет необходимо перевести по адресу ниже необходимую" \
              " сумму ≈" + f'<b>{round(b.convert_to_btc(row[0][0], "RUB"), 7)} ₿</b>' +\
              " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n" + f'<code>{addr}</code>'
        bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
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
