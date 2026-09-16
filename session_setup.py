"""
اسکریپت ساخت SESSION_STRING — یک بار روی کامپیوتر خودت اجرا کن
pip install telethon
python session_setup.py
"""
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID   = int(input("API_ID: ").strip())
API_HASH = input("API_HASH: ").strip()

async def generate():
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        print("\n" + "=" * 60)
        print(client.session.save())
        print("=" * 60)

asyncio.run(generate())
