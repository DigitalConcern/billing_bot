from aiogram import *
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import Throttled
from aiogram.dispatcher.filters import Text
from config import *
from forex_python.bitcoin import BtcConverter
from coinbase.wallet.client import Client
import os
import datetime
import asyncio
import logging
import requests
import psycopg2 as pg
import qrcode

client = Client(API_KEY, SECRET_API_KEY, api_version='2021-12-01')
account = client.get_account('BTC')

connection = pg.connect(DB_URI, sslmode='require')
cur = connection.cursor()

storage = MemoryStorage()
bot = Bot(TOKEN)
dp = Dispatcher(bot, storage=storage)

logging.basicConfig(level=logging.DEBUG)

b = BtcConverter()


class Form(StatesGroup):
    city = State()
    category = State()
    amount = State()
    id = 0
    acceptation = State()


@dp.message_handler(commands=["start"])
async def start(m, res=False):
    try:
        # Execute throttling manager with rate-limit equal to 2 seconds for key "start"
        await dp.throttle('start', rate=6)
    except Throttled:
        # If request is throttled, the `Throttled` exception will be raised
        await m.reply('От вас слишком много запросов!\nПодозрительно...')
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cur.execute('SELECT DISTINCT city FROM products;')
        rows = cur.fetchall()
        for row in rows:
            item = types.KeyboardButton(''.join(row[0]))
            markup.add(item)
        await bot.send_message(m.chat.id, "Выбери город, в котором планируешь сделать заказ!", reply_markup=markup)
        await Form.city.set()


# @dp.message_handler(state='*', commands='отмена')
# @dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
# async def cancel_handler(message: types.Message, state: FSMContext):
#     """
#     Allow user to cancel any action
#     """
#     current_state = await state.get_state()
#     if current_state is None:
#         return
#
#     logging.info('Cancelling state %r', current_state)
#     # Cancel state and inform user about it
#     await state.finish()
#     # And remove keyboard (just in case)
#     await message.reply('Отменено.', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Form.city)
async def process_city(message: types.Message, state: FSMContext):
    if not message.text.startswith('/'):
        async with state.proxy() as data:
            data['city'] = message.text

        await Form.next()

        markup_inline = types.InlineKeyboardMarkup()
        cur.execute(f"SELECT DISTINCT category FROM products WHERE city = '{message.text.strip()}';")
        rows = cur.fetchall()
        if not rows:
            await bot.send_message(message.chat.id, "К сожалению, вашего города еще нет в нашем списке 😔 \n"
                                                    "Выбери из предложенных в меню!")
            await Form.city.set()
        else:
            for row in rows:
                item = types.InlineKeyboardButton(text=''.join(row[0]),
                                                  callback_data=''.join(row[0])) #city_{"".join(row[0])}_
                markup_inline.add(item)
            await bot.send_message(message.chat.id, "Выбери категорию, которая тебя интересует!",
                                   reply_markup=markup_inline)


@dp.callback_query_handler(lambda call: call.data, state=Form.category)
async def process_category(callback_query: types.CallbackQuery, state: FSMContext):
    # Update state and data
    await state.update_data(category=callback_query.data.strip())
    await Form.next()

    async with state.proxy() as data:
        markup_inline = types.InlineKeyboardMarkup()
        cur.execute(f"SELECT name, price, id FROM products WHERE category = '{data['category']}' AND city = '{data['city']}';")
        rows = cur.fetchall()
        for row in rows:
            markup_inline.inline_keyboard.clear()
            img = open('data/' + ''.join(row[0]) + '.png', 'rb')
            item_buy1 = types.InlineKeyboardButton(text='1', callback_data=f'{row[2]}' + '_1')
            item_buy3 = types.InlineKeyboardButton(text='3', callback_data=f'{row[2]}' + '_3')
            item_buy5 = types.InlineKeyboardButton(text='5', callback_data=f'{row[2]}' + '_5')
            item_buy10 = types.InlineKeyboardButton(text='10', callback_data=f'{row[2]}' + '_10')
            markup_inline.row(item_buy1, item_buy3, item_buy5, item_buy10)
            await bot.send_photo(callback_query.from_user.id, img,
                                 f'{row[0]}\nЦена за одну штуку: {row[1]} RUB ≈ {round(b.convert_to_btc((row[1]), "RUB"), 7)} ₿\n'
                                 f'Выберите сколько товара Вы хотите купить',
                                 reply_markup=markup_inline)


@dp.callback_query_handler(lambda call: call.data, state=Form.amount)
async def process_amount(callback_query: types.CallbackQuery, state: FSMContext):
    markup_inline = types.InlineKeyboardMarkup()
    yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
    no = types.InlineKeyboardButton(text='Нет', callback_data='no')
    markup_inline.row(yes, no)

    await Form.next()
    # await Form.next()

    async with state.proxy() as data:
        data['amount'] = int(callback_query.data.split('_')[1])
        Form.id = int(callback_query.data.split('_')[0])

        await bot.send_message(callback_query.from_user.id, "Вы действительно хотите приобрести товар?",
                               reply_markup=markup_inline)


@dp.callback_query_handler(lambda call: call.data, state=Form.acceptation)
async def process_acceptation(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == 'yes':
        async with state.proxy() as data:
            user_id = callback_query.from_user.id

            cur.execute(f"INSERT INTO users(id, trans, date) VALUES ({user_id}, false,"
                        f" '{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}');")
            connection.commit()

            addr = account.create_address()['address']
            cur.execute(f"SELECT price, name, city FROM products WHERE id = {Form.id};")
            row = cur.fetchone()
            value = round(b.convert_to_btc(row[0], "RUB"), 7) * int(data['amount'])
            msg = f"<b>Вы выбрали {row[1]} в количестве {data['amount']} штук(а) для покупки в {row[2]}</b> \n\n" \
                  "Вам нужно в течение 15 минут перевести по адресу ниже необходимую" \
                  " сумму ≈" + f'<b>{value} ₿</b>' + \
                  " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n"
            await bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
            await bot.send_message(callback_query.from_user.id, f'<code>{addr}</code>', parse_mode="HTML")
            img = qrcode.make(addr)
            img.save('qr.png')
            await bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))
            await bot.send_message(callback_query.from_user.id, '<b>После успешной покупки в течение 15 минут вам придет'
                                                                ' уведомление об успешной оплате</b>', parse_mode="HTML")

            markup = types.ReplyKeyboardRemove()
            await bot.send_message(callback_query.from_user.id,'<b>Если хотите оформить еще один заказ или оформить заказ повторно,'
                                                               ' введите</b>\n<a>/start</a>', parse_mode="HTML", reply_markup=markup)

            await state.finish()
            asyncio.create_task(accept(addr, value, user_id))
    else:
        await state.finish()
        markup = types.ReplyKeyboardRemove()
        await bot.send_message(callback_query.from_user.id, '<b>Если хотите оформить еще один заказ или оформить заказ повторно,'
                                                            ' введите</b>\n<a>/start</a>', parse_mode="HTML", reply_markup=markup)

# @dp.message_handler(commands=["start"])
# async def start(m, res=False):
#     markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#     cur.execute('SELECT DISTINCT city FROM products;')
#     rows = cur.fetchall()
#     for row in rows:
#         item = types.KeyboardButton(''.join(row[0]))
#         markup.add(item)
#     await bot.send_message(m.chat.id, "Выбери город, в котором планируешь сделать заказ!", reply_markup=markup)
#
#
# @dp.message_handler(content_types=["text"])
# async def handle_city(message: types.Message):
#     markup_inline = types.InlineKeyboardMarkup()
#     cur.execute(f"SELECT DISTINCT category FROM products WHERE city = '{message.text.strip()}';")
#     rows = cur.fetchall()
#     if not rows:
#         await bot.send_message(message.chat.id, "К сожалению, вашего города еще нет в нашем списке 😔 \n"
#                                                 "Выбери из предложенных в меню!")
#     else:
#         for row in rows:
#             item = types.InlineKeyboardButton(text=''.join(row[0]),
#                                               callback_data=f'city_{"".join(row[0])}_{message.text.strip()}')
#             markup_inline.add(item)
#         await bot.send_message(message.chat.id, "Выбери категорию, которая тебя интересует!",
#                                reply_markup=markup_inline)
#
#
# # Получение сообщений от юзера
# @dp.callback_query_handler(lambda c: c.data)
# async def callback_inline_category(callback_query: types.CallbackQuery):
#     if callback_query.data.split('_')[0] == 'city':
#         city = callback_query.data.split('_')[2]
#         category = callback_query.data.split('_')[1]
#         markup_inline = types.InlineKeyboardMarkup()
#         cur.execute(f"SELECT name, price, id FROM products WHERE category = '{category}' AND city = '{city}';")
#         rows = cur.fetchall()
#         for row in rows:
#             markup_inline.inline_keyboard.clear()
#             img = open('data/' + ''.join(row[0]) + '.png', 'rb')
#             item_buy1 = types.InlineKeyboardButton(text='1', callback_data=f'id_{row[2]}' + '_1')
#             item_buy3 = types.InlineKeyboardButton(text='3', callback_data=f'id_{row[2]}' + '_3')
#             item_buy5 = types.InlineKeyboardButton(text='5', callback_data=f'id_{row[2]}' + '_5')
#             item_buy10 = types.InlineKeyboardButton(text='10', callback_data=f'id_{row[2]}' + '_10')
#             markup_inline.row(item_buy1, item_buy3, item_buy5, item_buy10)
#             await bot.send_photo(callback_query.from_user.id, img,
#                                  f'{row[0]}\nЦена за одну штуку: {row[1]} RUB ≈ {round(b.convert_to_btc((row[1]), "RUB"), 7)} ₿\n'
#                                  f'Выберите сколько товара Вы хотите купить',
#                                  reply_markup=markup_inline)
#
#     if callback_query.data.split('_')[0] == 'id':
#         user_id = callback_query.from_user.id
#
#         cur.execute(f"INSERT INTO users(id, trans, date) VALUES ({user_id}, false,"
#                     f" '{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}');")
#         connection.commit()
#
#         amount = callback_query.data.split('_')[2]
#         id = callback_query.data.split('_')[1]
#         addr = account.create_address()['address']
#         cur.execute(f"SELECT price, name, city FROM products WHERE id = {id};")
#         row = cur.fetchone()
#         value = round(b.convert_to_btc(row[0], "RUB"), 7) * int(amount)
#         msg = f"<b>Вы выбрали {row[1]} в количестве {amount} штук(а) для покупки в {row[2]}</b> \n\n" \
#               "Вам нужно в течение 15 минут перевести по адресу ниже необходимую" \
#               " сумму ≈" + f'<b>{value} ₿</b>' + \
#               " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n"
#         await bot.send_message(user_id, msg, parse_mode="HTML")
#         await bot.send_message(user_id, f'<code>{addr}</code>', parse_mode="HTML")
#         img = qrcode.make(addr)
#         img.save('qr.png')
#         await bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))
#         await bot.send_message(user_id, '<b>После успешной покупки в течение 15 минут вам придет'
#                                         ' уведомление об успешной оплате</b>', parse_mode="HTML")
#
#         asyncio.create_task(accept(addr, value, user_id))
#
#
async def accept(address, sum, user):
    ctr = 0
    conf = requests.get(f"https://chain.so/api/v2/get_address_balance/BTC/{address}/500")
    ans = conf.json()
    while ctr != 50 and float(ans['data']['confirmed_balance']) != sum:
        conf = requests.get(f"https://chain.so/api/v2/get_address_balance/BTC/{address}/500")
        ans = conf.json()
        await asyncio.sleep(10)
        ctr += 10
    if float(ans['data']['confirmed_balance']) == sum:
        cur.execute(f"INSERT INTO users(id, trans, date) VALUES ({user}, true,"
                    f" '{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}');")
        connection.commit()
        await bot.send_message(user, "Покупка подтверждена!")
        return
    else:
        cur.execute(f"INSERT INTO users(id, trans, date) VALUES ({user}, false,"
                    f" '{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}');")
        connection.commit()
        await bot.send_message(user, "Покупка не подтверждена!\nПопробуйте оформить заказ заново!")
        return


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
        port=int(os.environ.get("PORT", 5000))
    )

    # bot.remove_webhook()
    # bot.set_webhook(url=APP_URL)
    # server.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
