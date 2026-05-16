import asyncio
import logging
import random
import string
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, LabeledPrice, PreCheckoutQuery
from aiogram.filters import Command
from config import *
from database import *
from account_manager import account_manager

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========== КЛАВИАТУРЫ ==========
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance"),
         InlineKeyboardButton(text="💳 Купить", callback_data="buy_menu")],
        [InlineKeyboardButton(text="📨 Рассылка", callback_data="send_menu"),
         InlineKeyboardButton(text="🎫 Промокод", callback_data="promo_menu")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])
    return keyboard

def get_payment_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Т-Банк (карта)", callback_data="pay_card")],
        [InlineKeyboardButton(text="🪙 USDT (TRC20)", callback_data="pay_crypto")],
        [InlineKeyboardButton(text="⭐ Telegram Stars", callback_data="pay_stars")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    return keyboard

def get_amount_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="10 000 сообщ. (50₽/⭐)", callback_data="buy_10000")],
        [InlineKeyboardButton(text="20 000 сообщ. (100₽/⭐)", callback_data="buy_20000")],
        [InlineKeyboardButton(text="50 000 сообщ. (250₽/⭐)", callback_data="buy_50000")],
        [InlineKeyboardButton(text="100 000 сообщ. (500₽/⭐)", callback_data="buy_100000")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    return keyboard

def get_admin_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Выдать баланс", callback_data="admin_add_balance")],
        [InlineKeyboardButton(text="🔨 Бан/Разбан", callback_data="admin_ban_menu")],
        [InlineKeyboardButton(text="🔇 Мут/Размут", callback_data="admin_mute_menu")],
        [InlineKeyboardButton(text="🎫 Создать промокод", callback_data="admin_create_promo")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👑 Список админов", callback_data="admin_list")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    return keyboard

def is_admin(user_id, username):
    return username in ADMIN_USERNAMES

# ========== КОМАНДЫ ==========
@dp.message(Command('start'))
async def start_cmd(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or str(user_id)
    register_user(user_id, username)
    
    if is_banned(user_id):
        await message.answer("❌ Вы забанены в боте!")
        return
    
    await message.answer(
        f"🤖 **Рассыльщик Telegram**\n\n"
        f"👋 Привет, {username}!\n"
        f"💰 Баланс: `{get_balance(user_id)}` сообщений\n\n"
        f"📌 Управляй ботом через кнопки ниже:",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(lambda c: c.data == "balance")
async def show_balance(callback: CallbackQuery):
    user_id = callback.from_user.id
    bal = get_balance(user_id)
    await callback.message.edit_text(
        f"💰 **Ваш баланс:** `{bal}` сообщений\n\n"
        f"💵 1 сообщение = 0.005₽\n"
        f"🎫 Есть промокод? Введи `/promo КОД`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ])
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "buy_menu")
async def buy_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        f"💳 **Выберите способ оплаты:**\n\n"
        f"⭐ Telegram Stars — моментально\n"
        f"💳 Т-Банк — перевод на карту\n"
        f"🪙 USDT — криптовалюта",
        parse_mode="Markdown",
        reply_markup=get_payment_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "pay_card")
async def pay_card(callback: CallbackQuery):
    await callback.message.edit_text(
        f"💳 **Оплата банковской картой**\n\n"
        f"Переведите нужную сумму на карту:\n"
        f"`{BANK_CARD}`\n\n"
        f"🏦 **Т-Банк**\n\n"
        f"После оплаты отправьте чек @Senko_live\n"
        f"Баланс пополнится вручную.\n\n"
        f"💰 Цены:\n"
        f"• 50₽ → 10 000 сообщ.\n"
        f"• 100₽ → 20 000 сообщ.\n"
        f"• 250₽ → 50 000 сообщ.\n"
        f"• 500₽ → 100 000 сообщ.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="buy_menu")]
        ])
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "pay_crypto")
async def pay_crypto(callback: CallbackQuery):
    await callback.message.edit_text(
        f"🪙 **Оплата USDT (TRC20)**\n\n"
        f"Кошелек для перевода:\n"
        f"`{CRYPTO_WALLET}`\n\n"
        f"💰 **Цены:**\n"
        f"• 50₽ (~0.5 USDT) → 10 000 сообщ.\n"
        f"• 100₽ (~1 USDT) → 20 000 сообщ.\n"
        f"• 250₽ (~2.5 USDT) → 50 000 сообщ.\n"
        f"• 500₽ (~5 USDT) → 100 000 сообщ.\n\n"
        f"📤 После оплаты отправьте скриншот @Senko_live",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="buy_menu")]
        ])
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "pay_stars")
async def pay_stars(callback: CallbackQuery):
    await callback.message.edit_text(
        f"⭐ **Оплата Telegram Stars**\n\n"
        f"Выберите количество сообщений:",
        parse_mode="Markdown",
        reply_markup=get_amount_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("buy_"))
async def process_stars_payment(callback: CallbackQuery):
    amount = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    prices = {
        10000: 50,
        20000: 100,
        50000: 250,
        100000: 500
    }
    
    stars_amount = prices.get(amount, 50)
    
    await bot.send_invoice(
        chat_id=user_id,
        title=f"⭐ {amount} сообщений",
        description=f"Пополнение баланса на {amount} сообщений для рассылки",
        payload=f"stars_{amount}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=f"{amount} сообщений", amount=stars_amount)],
        start_parameter="mailing_bot"
    )
    await callback.answer()

@dp.pre_checkout_query(lambda q: True)
async def pre_checkout_handler(pre_checkout: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout.id, ok=True)

@dp.message(lambda m: m.successful_payment)
async def successful_payment(message: Message):
    user_id = message.from_user.id
    payload = message.successful_payment.invoice_payload
    amount_messages = int(payload.split("_")[1])
    
    add_balance(user_id, amount_messages)
    await message.answer(
        f"✅ **Оплата прошла успешно!**\n\n"
        f"💰 Начислено: `{amount_messages}` сообщений\n"
        f"📊 Новый баланс: `{get_balance(user_id)}` сообщений",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(lambda c: c.data == "send_menu")
async def send_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        f"📨 **Рассылка сообщений**\n\n"
        f"Используйте команду:\n"
        f"`/send @чат_юзернейм Текст сообщения`\n\n"
        f"Пример:\n"
        f"`/send @durov Привет, подписчики!`\n\n"
        f"⚠️ 1 сообщение = 1 с баланса",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ])
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "promo_menu")
async def promo_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        f"🎫 **Активация промокода**\n\n"
        f"Введите команду:\n"
        f"`/promo КОД`\n\n"
        f"Пример: `/promo ABC123`\n\n"
        f"Промокоды дают бесплатные сообщения!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ])
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "help")
async def help_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        f"❓ **Помощь**\n\n"
        f"📌 **Команды:**\n"
        f"• `/start` - главное меню\n"
        f"• `/balance` - баланс\n"
        f"• `/send @чат Текст` - рассылка\n"
        f"• `/promo КОД` - активировать промокод\n\n"
        f"💳 **Оплата:**\n"
        f"• Telegram Stars (моментально)\n"
        f"• Банковская карта (вручную)\n"
        f"• USDT (вручную)\n\n"
        f"👑 **Поддержка:** @Senko_live",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ])
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.edit_text(
        f"🤖 **Рассыльщик Telegram**\n\n"
        f"💰 Баланс: `{get_balance(user_id)}` сообщений\n\n"
        f"📌 Выберите действие:",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

# ========== РАССЫЛКА ==========
@dp.message(Command('send'))
async def send_cmd(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    
    if is_banned(user_id):
        await message.answer("❌ Вы забанены в боте!")
        return
    
    if is_muted(user_id):
        await message.answer("🔇 Вы в муте! Нельзя делать рассылки.")
        return
    
    bal = get_balance(user_id)
    if bal < 1:
        await message.answer("❌ Недостаточно средств! Купите сообщения в меню `/buy`", parse_mode="Markdown")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Использование: `/send @чат_юзернейм Текст сообщения`", parse_mode="Markdown")
        return
    
    parts = args[1].split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Укажите чат и текст!\nПример: `/send @durov Привет!`", parse_mode="Markdown")
        return
    
    target_chat = parts[0]
    msg_text = parts[1]
    
    status_msg = await message.answer("🚀 Отправляю...")
    
    success, error = await account_manager.send_message(target_chat, msg_text)
    
    if success:
        if deduct_balance(user_id, 1):
            add_to_sent(user_id)
            await status_msg.edit_text(f"✅ Отправлено в {target_chat}!\n💰 Остаток: {get_balance(user_id)}")
        else:
            await status_msg.edit_text("❌ Ошибка списания баланса")
    else:
        await status_msg.edit_text(f"❌ {error}")

@dp.message(Command('promo'))
async def promo_cmd(message: Message):
    user_id = message.from_user.id
    if is_banned(user_id):
        await message.answer("❌ Вы забанены!")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Использование: `/promo КОД`", parse_mode="Markdown")
        return
    
    code = args[1].upper()
    success, result = use_promocode(user_id, code)
    
    if success:
        await message.answer(f"✅ {result}!\n💰 Новый баланс: {get_balance(user_id)}")
    else:
        await message.answer(f"❌ {result}")

@dp.message(Command('balance'))
async def balance_cmd(message: Message):
    user_id = message.from_user.id
    if is_banned(user_id):
        await message.answer("❌ Вы забанены!")
        return
    bal = get_balance(user_id)
    await message.answer(f"💰 Ваш баланс: `{bal}` сообщений", parse_mode="Markdown")

# ========== АДМИН-ПАНЕЛЬ ==========
@dp.message(Command('admin'))
async def admin_panel(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    
    if not is_admin(user_id, username):
        await message.answer("⛔ У вас нет прав администратора!")
        return
    
    await message.answer(
        f"👑 **Панель администратора**\n\n"
        f"Добро пожаловать, @{username}!\n\n"
        f"📌 Управляйте ботом через кнопки:",
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard()
    )

@dp.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats_callback(callback: CallbackQuery):
    username = callback.from_user.username or ""
    if not is_admin(callback.from_user.id, username):
        await callback.answer("Нет прав!", show_alert=True)
        return
    
    total_users, total_balance, total_sent, banned_count = get_stats()
    
    await callback.message.edit_text(
        f"📊 **Статистика бота**\n\n"
        f"👥 Пользователей: `{total_users}`\n"
        f"💰 В обороте: `{total_balance}` сообщ.\n"
        f"📨 Отправлено всего: `{total_sent}` сообщ.\n"
        f"🔨 Забанено: `{banned_count}`\n"
        f"🎫 Промокодов: `{cursor.execute('SELECT COUNT(*) FROM promocodes').fetchone()[0]}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="back_to_admin")]
        ])
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_list")
async def admin_list_callback(callback: CallbackQuery):
    username = callback.from_user.username or ""
    if not is_admin(callback.from_user.id, username):
        await callback.answer("Нет прав!", show_alert=True)
        return
    
    admins_list = "\n".join([f"👑 @{admin}" for admin in ADMIN_USERNAMES])
    
    await callback.message.edit_text(
        f"👥 **Список администраторов**\n\n{admins_list}\n\n⭐ Главный: {MAIN_ADMIN}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="back_to_admin")]
        ])
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_create_promo")
async def admin_create_promo_callback(callback: CallbackQuery):
    username = callback.from_user.username or ""
    if not is_admin(callback.from_user.id, username):
        await callback.answer("Нет прав!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"🎫 **Создание промокода**\n\n"
        f"Используйте команду:\n"
        f"`/create_promo количество_сообщений сколько_раз`\n\n"
        f"Пример:\n"
        f"`/create_promo 5000 10`\n\n"
        f"Создаст промокод на 5000 сообщений, который можно использовать 10 раз.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="back_to_admin")]
        ])
    )
    await callback.answer()

@dp.message(Command('create_promo'))
async def create_promo_cmd(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    
    if not is_admin(user_id, username):
        await message.answer("⛔ Нет прав!")
        return
    
    args = message.text.split()
    if len(args) != 3:
        await message.answer("❌ Использование: `/create_promo количество использований`", parse_mode="Markdown")
        return
    
    amount = int(args[1])
    max_uses = int(args[2])
    
    code = create_promocode(amount, max_uses, user_id)
    await message.answer(
        f"✅ **Промокод создан!**\n\n"
        f"🎫 Код: `{code}`\n"
        f"💰 Сумма: `{amount}` сообщений\n"
        f"📊 Макс. использований: `{max_uses}`\n\n"
        f"Пользователи активируют: `/promo {code}`",
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data == "admin_add_balance")
async def admin_add_balance_menu(callback: CallbackQuery):
    username = callback.from_user.username or ""
    if not is_admin(callback.from_user.id, username):
        await callback.answer("Нет прав!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"➕ **Выдача баланса**\n\n"
        f"Используйте команду:\n"
        f"`/add_balance @username количество`\n\n"
        f"Пример:\n"
        f"`/add_balance @Senko_live 10000`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="back_to_admin")]
        ])
    )
    await callback.answer()

@dp.message(Command('add_balance'))
async def add_balance_cmd(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    
    if not is_admin(user_id, username):
        await message.answer("⛔ Нет прав!")
        return
    
    args = message.text.split()
    if len(args) != 3:
        await message.answer("❌ Использование: `/add_balance @username количество`", parse_mode="Markdown")
        return
    
    target = args[1].replace('@', '')
    amount = int(args[2])
    
    cursor.execute("SELECT user_id FROM users WHERE username LIKE ?", (f"%{target}%",))
    user = cursor.fetchone()
    
    if not user:
        await message.answer(f"❌ Пользователь @{target} не найден")
        return
    
    add_balance(user[0], amount)
    await message.answer(f"✅ Выдано {amount} сообщений @{target}")

@dp.callback_query(lambda c: c.data == "admin_ban_menu")
async def admin_ban_menu(callback: CallbackQuery):
    username = callback.from_user.username or ""
    if not is_admin(callback.from_user.id, username):
        await callback.answer("Нет прав!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"🔨 **Бан пользователя**\n\n"
        f"Команды:\n"
        f"`/ban @username [причина]` - забанить\n"
        f"`/unban @username` - разбанить\n\n"
        f"Пример:\n"
        f"`/ban @Senko_live Спам`\n"
        f"`/unban @Senko_live`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="back_to_admin")]
        ])
    )
    await callback.answer()

@dp.message(Command('ban'))
async def ban_cmd(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    
    if not is_admin(user_id, username):
        await message.answer("⛔ Нет прав!")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: `/ban @username [причина]`", parse_mode="Markdown")
        return
    
    target = args[1].replace('@', '')
    reason = " ".join(args[2:]) if len(args) > 2 else "Не указана"
    
    cursor.execute("SELECT user_id FROM users WHERE username LIKE ?", (f"%{target}%",))
    user = cursor.fetchone()
    
    if not user:
        await message.answer(f"❌ Пользователь @{target} не найден")
        return
    
    ban_user(user[0])
    await message.answer(f"✅ Пользователь @{target} забанен\n📝 Причина: {reason}")

@dp.message(Command('unban'))
async def unban_cmd(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    
    if not is_admin(user_id, username):
        await message.answer("⛔ Нет прав!")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: `/unban @username`", parse_mode="Markdown")
        return
    
    target = args[1].replace('@', '')
    
    cursor.execute("SELECT user_id FROM users WHERE username LIKE ?", (f"%{target}%",))
    user = cursor.fetchone()
    
    if not user:
        await message.answer(f"❌ Пользователь @{target} не найден")
        return
    
    unban_user(user[0])
    await message.answer(f"✅ Пользователь @{target} разбанен")

@dp.callback_query(lambda c: c.data == "admin_mute_menu")
async def admin_mute_menu(callback: CallbackQuery):
    username = callback.from_user.username or ""
    if not is_admin(callback.from_user.id, username):
        await callback.answer("Нет прав!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"🔇 **Мут пользователя**\n\n"
        f"Команды:\n"
        f"`/mute @username минуты [причина]` - замутить\n"
        f"`/unmute @username` - размутить\n\n"
        f"Пример:\n"
        f"`/mute @Senko_live 60 Спам`\n"
        f"`/unmute @Senko_live`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="back_to_admin")]
        ])
    )
    await callback.answer()

@dp.message(Command('mute'))
async def mute_cmd(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    
    if not is_admin(user_id, username):
        await message.answer("⛔ Нет прав!")
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.answer("❌ Использование: `/mute @username минуты [причина]`", parse_mode="Markdown")
        return
    
    target = args[1].replace('@', '')
    minutes = int(args[2])
    reason = " ".join(args[3:]) if len(args) > 3 else "Не указана"
    
    cursor.execute("SELECT user_id FROM users WHERE username LIKE ?", (f"%{target}%",))
    user = cursor.fetchone()
    
    if not user:
        await message.answer(f"❌ Пользователь @{target} не найден")
        return
    
    mute_user(user[0], user_id, minutes, reason)
    await message.answer(f"🔇 Пользователь @{target} замучен на {minutes} мин.\n📝 Причина: {reason}")

@dp.message(Command('unmute'))
async def unmute_cmd(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    
    if not is_admin(user_id, username):
        await message.answer("⛔ Нет прав!")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: `/unmute @username`", parse_mode="Markdown")
        return
    
    target = args[1].replace('@', '')
    
    cursor.execute("SELECT user_id FROM users WHERE username LIKE ?", (f"%{target}%",))
    user = cursor.fetchone()
    
    if not user:
        await message.answer(f"❌ Пользователь @{target} не найден")
        return
    
    unmute_user(user[0])
    await message.answer(f"🔊 Пользователь @{target} размучен")

@dp.callback_query(lambda c: c.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery):
    await callback.message.edit_text(
        f"👑 **Панель администратора**\n\n"
        f"📌 Управляйте ботом через кнопки:",
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()

# ========== ЗАПУСК ==========
async def main():
    print("🚀 Запуск бота на Railway...")
    print("📱 Авторизация аккаунтов для рассылки...")
    await account_manager.init()
    print("✅ Аккаунты готовы!")
    print("🤖 Бот запущен!")
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("="*50)
    print("🤖 TELEGRAM РАССЫЛЬЩИК")
    print("👑 Админ: @Senko_live")
    print("📱 Аккаунты: @seqrp, @Question088")
    print("="*50)
    asyncio.run(main())