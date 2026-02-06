import os
from dotenv import load_dotenv

# لود کردن متغیرها از فایل .env
load_dotenv()

# استخراج مقادیر
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
SALT_KEY = os.getenv("SALT_KEY")

# چک کردن برای اطمینان از اینکه مقادیر خالی نباشند
if not all([BOT_TOKEN, GROUP_ID, SALT_KEY]):
    raise ValueError("Missing essential environment variables in .env file!")