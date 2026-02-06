import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from config import BOT_TOKEN, GROUP_ID, SALT_KEY
from utils.encryption import get_anonymous_id

# تنظیمات لاگ برای دیدن خطاهای احتمالی در کنسول
logging.basicConfig(level=logging.INFO)

# راه اندازی بات و دیسپچر
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(F.chat.type == "private")
async def handle_anonymous_messages(message: types.Message):
    """
    دریافت پیام از پی‌وی و ارسال به گروه به صورت ناشناس
    """
    # ۱. تولید آیدی مجازی (مثلاً a1b2c3d4)
    anon_id = get_anonymous_id(message.from_user.id, SALT_KEY)
    
    # ۲. آماده‌سازی کپشن برای رسانه‌ها یا متن پیام
    prefix = f"👤 **کاربر ناشناس ({anon_id}):**\n\n"

    try:
        # ۳. بررسی نوع پیام و ارسال کپی آن به گروه
        if message.text:
            # ارسال پیام متنی
            await bot.send_message(
                chat_id=GROUP_ID, 
                text=f"{prefix}{message.text}", 
                parse_mode="Markdown"
            )
        else:
            # کپی کردن هر نوع رسانه (عکس، فیلم، ویس، فایل) با کپشن جدید
            # متد copy_to باعث می‌شود پیام بدون نام فرستنده اصلی ارسال شود
            new_caption = f"{prefix}{message.caption or ''}"
            await message.copy_to(
                chat_id=GROUP_ID, 
                caption=new_caption, 
                parse_mode="Markdown"
            )
        
        # ۴. تایید ارسال به کاربر
        await message.reply("✅ پیام شما با موفقیت و به صورت کاملاً ناشناس در گروه منتشر شد.")
    
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        await message.reply("❌ متاسفانه در ارسال پیام مشکلی پیش آمد. مطمئن شوید ربات در گروه عضو و ادمین است.")

async def main():
    print("🚀 ربات ناشناس با موفقیت روشن شد...")
    # حذف آپدیت‌های قدیمی که وقتی ربات خاموش بوده ارسال شده‌اند
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🤖 ربات خاموش شد.")