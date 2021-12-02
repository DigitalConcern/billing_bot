from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from config import TOKEN, API_KEY, version, SECRET_PIN, db_exec
from forex_python.bitcoin import BtcConverter
from block_io import BlockIo
import qrcode

block_io = BlockIo(API_KEY, SECRET_PIN, version)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
b = BtcConverter()


# Команда start
@dp.message_handler(commands=["start"])
async def start(m, res=False):
    # Добавляем две кнопки
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Москва")
    item2 = types.KeyboardButton("Питер")
    markup.add(item1)
    markup.add(item2)
    await bot.send_message(m.chat.id, "Выбери свой город!", reply_markup=markup)


# Получение сообщений от юзера
@dp.message_handler(content_types=["text"])
async def handle_text(message: types.Message):
    markup_inline = types.InlineKeyboardMarkup()

    if message.text.strip() == 'Москва':
        rows = await db_exec("SELECT id, product, cost FROM public.products WHERE city = 'Moscow';")

        for row in rows:
            img = open('data/' + ''.join(row[1]) + '.png', 'rb')
            item_buy = types.InlineKeyboardButton(text='Купить', callback_data=f'{row[0]}')
            markup_inline.inline_keyboard.clear()
            markup_inline.add(item_buy)
            await bot.send_photo(message.chat.id, img, f'Цена: {row[2]} RUB ≈ {round(b.convert_to_btc((row[2]), "RUB"), 7)} ₿',\
                                 reply_markup=markup_inline)
    elif message.text.strip() == 'Питер':
        rows = await db_exec("SELECT id, product, cost FROM public.products WHERE city = 'Piter';")
        for row in rows:
            img = open('data/' + ''.join(row[1]) + '.png', 'rb')
            item_buy = types.InlineKeyboardButton(text='Купить', callback_data=f'{row[0]}')
            markup_inline.inline_keyboard.clear()
            markup_inline.add(item_buy)
            await bot.send_photo(message.chat.id, img, f'Цена: {row[2]} RUB ≈ {round(b.convert_to_btc((row[2]), "RUB"), 7)} ₿',\
                                 reply_markup=markup_inline)
    else:
        await bot.send_message(message.chat.id, "К сожалению, вашего города еще нет в нашем списке 😔")


@dp.callback_query_handler(lambda c: c.data)
async def callback_inline(callback_query: types.CallbackQuery):
    if callback_query.data == '1':
        addr = block_io.get_new_address()['data']['address']
        row = await db_exec("SELECT cost FROM public.products WHERE id = 1;")
        msg = "<b>Вы выбрали Машинку для покупки в Москве</b> \n\n" \
              "Вам будет необходимо перевести по адресу ниже необходимую" \
              " сумму ≈" + f'<b>{round(b.convert_to_btc(row[0][0], "RUB"), 7)} ₿</b>' +\
              " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n" + f'<code>{addr}</code>'
        await bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
        img = qrcode.make(addr)
        img.save('qr.png')
        await bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))
    if callback_query.data == '2':
        addr = block_io.get_new_address()['data']['address']
        row = await db_exec("SELECT cost FROM public.products WHERE id = 2;")
        msg = "<b>Вы выбрали Кораблик для покупки в Москве</b> \n\n" \
              "Вам будет необходимо перевести по адресу ниже необходимую" \
              " сумму ≈" + f'<b>{round(b.convert_to_btc(row[0][0], "RUB"), 7)} ₿</b>' +\
              " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n" + f'<code>{addr}</code>'
        await bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
        img = qrcode.make(addr)
        img.save('qr.png')
        await bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))
    if callback_query.data == '3':
        addr = block_io.get_new_address()['data']['address']
        row = await db_exec("SELECT cost FROM public.products WHERE id = 3;")
        msg = "<b>Вы выбрали Вертолетик для покупки в Москве</b> \n\n" \
              "Вам будет необходимо перевести по адресу ниже необходимую" \
              " сумму ≈" + f'<b>{round(b.convert_to_btc(row[0][0], "RUB"), 7)} ₿</b>' +\
              " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n" + f'<code>{addr}</code>'
        await bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
        img = qrcode.make(addr)
        img.save('qr.png')
        await bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))
    if callback_query.data == '4':
        addr = block_io.get_new_address()['data']['address']
        row = await db_exec("SELECT cost FROM public.products WHERE id = 4;")
        msg = "<b>Вы выбрали Машинку для покупки в Питере</b> \n\n" \
              "Вам будет необходимо перевести по адресу ниже необходимую" \
              " сумму ≈" + f'<b>{round(b.convert_to_btc(row[0][0], "RUB"), 7)} ₿</b>' +\
              " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n" + f'<code>{addr}</code>'
        await bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
        img = qrcode.make(addr)
        img.save('qr.png')
        await bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))
    if callback_query.data == '5':
        addr = block_io.get_new_address()['data']['address']
        row = await db_exec("SELECT cost FROM public.products WHERE id = 5;")
        msg = "<b>Вы выбрали Кораблик для покупки в Питере</b> \n\n" \
              "Вам будет необходимо перевести по адресу ниже необходимую" \
              " сумму ≈" + f'<b>{round(b.convert_to_btc(row[0][0], "RUB"), 7)} ₿</b>' +\
              " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n" + f'<code>{addr}</code>'
        await bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
        img = qrcode.make(addr)
        img.save('qr.png')
        await bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))
    if callback_query.data == '6':
        addr = block_io.get_new_address()['data']['address']
        row = await db_exec("SELECT cost FROM public.products WHERE id = 6;")
        msg = "<b>Вы выбрали Вертолетик для покупки в Питере</b> \n\n" \
              "Вам будет необходимо перевести по адресу ниже необходимую" \
              " сумму ≈" + f'<b>{round(b.convert_to_btc(row[0][0], "RUB"), 7)} ₿</b>' +\
              " \n\n <i>Адрес кошелька Bitcoin для перевода</i>: \n" + f'<code>{addr}</code>'
        await bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
        img = qrcode.make(addr)
        img.save('qr.png')
        await bot.send_photo(callback_query.from_user.id, open('qr.png', 'rb'))


# Запускаем бота
if __name__ == '__main__':
    executor.start_polling(dp)
