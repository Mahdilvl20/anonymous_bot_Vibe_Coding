import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ماژول‌های پروژه
from config import BOT_TOKEN, GROUP_ID, SALT_KEY
from utils.encryption import get_anonymous_id
from utils.anti_spam import is_spaming
from utils.moderation import is_banned, ban_user, unban_user
from utils.states import Form
from utils.keyboards import (
    get_main_keyboard, 
    get_welcome_inline_keyboard,
    get_cancel_reply_keyboard
)

# --- تنظیمات لاگ ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# وضعیت فعلی ربات (پیش‌فرض روشن)
IS_BOT_ACTIVE = True

# --- Middleware مدیریت وضعیت و ضد اسپم ---
class BotControlMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, types.Message):
            return await handler(event, data)

        # اجازه عبور به دستورات مدیریتی گروه حتی در زمان خاموش بودن
        if event.chat.type in ["group", "supergroup"] and event.text in ["/on", "/off"]:
            return await handler(event, data)

        # بررسی وضعیت خاموش/روشن بودن برای کاربران در پی‌وی
        if not IS_BOT_ACTIVE and event.chat.type == "private":
            await event.answer("⚠️ ربات در حال حاضر توسط ادمین خاموش شده است.")
            return

        # بررسی سیستم ضد اسپم
        if is_spaming(event.from_user.id, limit=2.0):
            return

        return await handler(event, data)

# --- Initialization ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.message.middleware(BotControlMiddleware())

# --- هندلرهای مدیریت وضعیت (فقط در گروه) ---

@dp.message(Command("off"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_bot_off(message: types.Message):
    global IS_BOT_ACTIVE
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ["administrator", "creator"]:
        return

    IS_BOT_ACTIVE = False
    logger.info(f"Bot disabled in group {message.chat.id}")
    await message.reply("🔴 ربات خاموش شد. کاربران دیگر نمی‌توانند پیام بفرستند.")

@dp.message(Command("on"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_bot_on(message: types.Message):
    global IS_BOT_ACTIVE
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ["administrator", "creator"]:
        return

    IS_BOT_ACTIVE = True
    logger.info(f"Bot enabled in group {message.chat.id}")
    await message.reply("🟢 ربات روشن شد. آماده دریافت پیام‌های ناشناس.")

# --- بقیه هندلرهای پروژه ---

@dp.message(Command("start"), F.chat.type == "private")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    welcome_text = "سلام! برای ارسال پیام ناشناس به عرفان از دکمه زیر استفاده کنید: 😊"
    await message.answer(text=welcome_text, reply_markup=get_welcome_inline_keyboard())
    await message.answer("منوی پایین فعال شد:", reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "cancel_action")
@dp.message(F.text == "🔙 بازگشت")
async def cancel_handler(event, state: FSMContext):
    await state.clear()
    text = "عملیات لغو شد. به منوی اصلی برگشتیم."
    if isinstance(event, types.CallbackQuery):
        await event.answer("لغو شد")
        await event.message.answer(text, reply_markup=get_main_keyboard())
    else:
        await event.answer(text, reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "start_anon_msg")
@dp.message(F.text == "💌 پیام ناشناس به عرفان")
async def start_messaging(event, state: FSMContext):
    user_id = event.from_user.id
    anon_id = get_anonymous_id(user_id, SALT_KEY)
    
    if is_banned(anon_id):
        if isinstance(event, types.CallbackQuery):
            return await event.answer("🚫 شما مسدود هستید.", show_alert=True)
        return await event.answer("🚫 مسدود هستید.")

    prompt_text = "حرفتون رو بزنید تا برای عرفان فرستاده بشه:"
    if isinstance(event, types.CallbackQuery):
        await event.answer()
        await event.message.answer(prompt_text, reply_markup=get_cancel_reply_keyboard())
    else:
        await event.answer(prompt_text, reply_markup=get_cancel_reply_keyboard())
    
    await state.set_state(Form.waiting_for_message)

@dp.message(Form.waiting_for_message, F.chat.type == "private")
async def collect_anonymous_message(message: types.Message, state: FSMContext):
    if message.text == "🔙 بازگشت": return

    anon_id = get_anonymous_id(message.from_user.id, SALT_KEY)
    prefix = f"👤 **کاربر ناشناس ({anon_id}):**\n\n"

    try:
        if message.text:
            await bot.send_message(GROUP_ID, f"{prefix}{message.text}", parse_mode="Markdown")
        else:
            await message.copy_to(GROUP_ID, caption=f"{prefix}{message.caption or ''}", parse_mode="Markdown")
        
        await message.reply("برای عرفان فرستاده شد. ✅", reply_markup=get_main_keyboard())
        await state.clear()
    except Exception as e:
        logger.error(f"Error: {e}")
        await message.reply("❌ خطا در ارسال.")

# --- مدیریت ادمین در گروه (Ban/Unban) ---

@dp.message(F.chat.type.in_({"group", "supergroup"}), F.text == "/ban")
async def handle_admin_ban(message: types.Message):
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ["administrator", "creator"]: return
    if not message.reply_to_message: return

    try:
        content = message.reply_to_message.text or message.reply_to_message.caption
        target_anon_id = content.split("(")[1].split(")")[0]
        ban_user(target_anon_id)
        await message.reply(f"✅ کاربر {target_anon_id} مسدود شد.")
    except:
        await message.reply("❌ خطا در شناسایی آیدی.")

@dp.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/unban"))
async def handle_admin_unban(message: types.Message):
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ["administrator", "creator"]: return
    
    target_anon_id = message.text.split()[1] if len(message.text.split()) > 1 else None
    if target_anon_id:
        unban_user(target_anon_id)
        await message.reply(f"✅ کاربر {target_anon_id} آزاد شد.")

async def main():
    logger.info("Bot is running...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())