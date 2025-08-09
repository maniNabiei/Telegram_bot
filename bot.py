import telebot
from telebot import types
from db import (create_db, register_user, login_user, logout_user, is_logged_in, decrement_token, get_tokens,
                add_tokens, get_email)
from config import send_verification_email
from rembg import remove
from PIL import Image
from io import BytesIO

bot = telebot.TeleBot('7733327431:AAHcRA-tnV0cqvtgVnyK8DR4etY3qQrC3O4')
user_states = {}

create_db()


@bot.message_handler(commands=['start'])
def handle_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('📝 ثبت‌نام', '🔐 ورود')
    markup.row('🚪 خروج', 'خرید توکن', 'نمایش توکن‌ها')
    bot.send_message(message.chat.id, "به ربات خوش آمدید.\n\n.ابتدا ثبت نام کنید تا به صورت رایگان ده توکن دریافت کنید\n\n.هر عکسی که برای حذف شدن بکگراند ارسال میکنید یک توکن از شما کم میکند\n\n.درصورت تمام شدن توکن ها باید توکن خریداری کنید تا بتوانید از ربات استفاده کنید",
                     reply_markup=markup)


@bot.message_handler(func=lambda m: m.text == "📝 ثبت‌نام")
def start_register(message):
    user_states[message.chat.id] = {'step': 'first_name'}
    bot.send_message(message.chat.id, "نام خود را وارد کنید:")


@bot.message_handler(func=lambda m: m.chat.id in user_states and user_states[m.chat.id]['step'] in [
    'first_name', 'last_name', 'email', 'password', 'verify'
])
def register_flow(message):
    state = user_states[message.chat.id]
    if state['step'] == 'first_name':
        state['first_name'] = message.text
        state['step'] = 'last_name'
        bot.send_message(message.chat.id, "نام خانوادگی را وارد کنید:")

    elif state['step'] == 'last_name':
        state['last_name'] = message.text
        state['step'] = 'email'
        bot.send_message(message.chat.id, "ایمیل خود را وارد کنید:")

    elif state['step'] == 'email':
        state['email'] = message.text

        gt_email = get_email(message.chat.id)
        if gt_email:
            bot.send_message(message.chat.id, 'شما با یک اکانت دیگر قبلا ثبت نام کرده اید و اجازه ثبت نام مجدد را ندارید')
            user_states.pop(message.chat.id)
            return
        state['step'] = 'password'
        bot.send_message(message.chat.id, "رمز عبور دلخواه خود را وارد کنید:")

    elif state['step'] == 'password':
        state['password'] = message.text
        code = send_verification_email(state['email'])
        state['verify_code'] = code
        state['step'] = 'verify'
        bot.send_message(message.chat.id, "کد تایید ارسال‌شده به ایمیل را وارد کنید:")

    elif state['step'] == 'verify':
        if message.text.strip() == state['verify_code']:
            register_user(
                message.chat.id,
                state['first_name'],
                state['last_name'],
                state['email'],
                state['password']
            )
            bot.send_message(message.chat.id, "ثبت‌نام موفق بود ✅")
            user_states.pop(message.chat.id)
        else:
            bot.send_message(message.chat.id, "کد نادرست است. دوباره تلاش کنید:")


@bot.message_handler(func=lambda m: m.text == "🔐 ورود")
def login_start(message):
    user_states[message.chat.id] = {'step': 'login_email'}
    bot.send_message(message.chat.id, "ایمیل خود را وارد کنید:")


@bot.message_handler(func=lambda m: m.chat.id in user_states and user_states[m.chat.id]['step'] in [
    'login_email', 'login_password'
])
def login_flow(message):
    state = user_states[message.chat.id]

    if state['step'] == 'login_email':
        state['email'] = message.text
        state['step'] = 'login_password'
        bot.send_message(message.chat.id, "رمز عبور را وارد کنید:")

    elif state['step'] == 'login_password':
        success = login_user(state['email'], message.text, message.chat.id)
        if success:
            bot.send_message(message.chat.id, "✅ ورود با موفقیت انجام شد.")
        else:
            bot.send_message(message.chat.id, "❌ ایمیل یا رمز اشتباه است.")
        user_states.pop(message.chat.id)


@bot.message_handler(func=lambda m: m.text == "🚪 خروج")
def logout(message):
    if is_logged_in(message.chat.id):
        logout_user(message.chat.id)
        bot.send_message(message.chat.id, "با موفقیت از حساب خارج شدید.")
    else:
        bot.send_message(message.chat.id, "شما وارد نشده‌اید.")


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id

    if not is_logged_in(chat_id):
        bot.send_message(chat_id, "لطفاً ابتدا وارد حساب خود شوید.")
        return

    tokens = get_tokens(chat_id)
    if tokens <= 0:
        bot.send_message(chat_id, "❌ توکن شما تمام شده است. برای ادامه، توکن خریداری کنید.")
        return

    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    input_image = Image.open(BytesIO(downloaded_file)).convert("RGBA")
    output_image = remove(input_image)

    output_bytes = BytesIO()
    output_image.save(output_bytes, format='PNG')
    output_bytes.seek(0)

    bot.send_document(chat_id, output_bytes, visible_file_name="no-bg.png")

    decrement_token(chat_id)
    bot.send_message(chat_id, f"✅ بک‌گراند حذف شد. توکن باقی‌مانده: {get_tokens(chat_id)}")


@bot.message_handler(commands=['tokens'])
def show_tokens(message):
    chat_id = message.chat.id
    if not is_logged_in(chat_id):
        bot.send_message(chat_id, "ابتدا باید وارد حساب کاربری خود شوید.")
        return
    tokens = get_tokens(chat_id)
    bot.send_message(chat_id, f"شما {tokens} توکن برای حذف بک‌گراند دارید.")


@bot.message_handler(commands=['buy_tokens'])
def buy_tokens(message):
    chat_id = message.chat.id
    if not is_logged_in(chat_id):
        bot.send_message(chat_id, "ابتدا باید وارد حساب کاربری خود شوید.")
        return
    bot.send_message(chat_id, "برای خرید توکن لطفا تعداد توکن مورد نظر را به صورت عدد ارسال کنید:")

    user_states[chat_id] = {'step': 'buy_tokens'}


@bot.message_handler(func=lambda m: m.chat.id in user_states and user_states[m.chat.id].get('step') == 'buy_tokens')
def handle_buy_tokens(message):
    chat_id = message.chat.id
    count = message.text
    if not count.isdigit() or int(count) <= 0:
        bot.send_message(chat_id, "لطفا یک عدد معتبر وارد کنید.")
        return
    add_tokens(chat_id, int(count))
    bot.send_message(chat_id, f"{count} توکن به حساب شما اضافه شد.")
    user_states.pop(chat_id)


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.text == 'ثبت‌نام':
        bot.send_message(message.chat.id, "فرایند ثبت‌نام شروع شد...")
    elif message.text == 'ورود':
        bot.send_message(message.chat.id, "فرایند ورود شروع شد...")
    elif message.text == 'خرید توکن':
        bot.send_message(message.chat.id, "برای خرید توکن به ...")
    elif message.text == 'نمایش توکن‌ها':
        count_token = get_tokens(message.chat.id)
        bot.send_message(message.chat.id, f"شما {count_token} توکن دارید")
    else:
        bot.send_message(message.chat.id, "لطفا از دکمه‌های موجود استفاده کنید.")


@bot.message_handler(commands=['menu'])
def menu(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('باز کردن سایت', url='https://example.com')
    btn2 = types.InlineKeyboardButton('دکمه کلیک', callback_data='button_clicked')
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "منو:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'button_clicked':
        bot.answer_callback_query(call.id, "دکمه کلیک شد!")
        bot.send_message(call.message.chat.id, "شما دکمه کلیک را زدید.")


bot.infinity_polling()
