from telethon import TelegramClient
from config import API_ID, API_HASH, ACCOUNTS
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

class AccountManager:
    def __init__(self):
        self.current_index = 0
        self.client = None
        
    async def init(self):
        await self.switch_to_account(0)
    
    async def switch_to_account(self, index):
        if index >= len(ACCOUNTS):
            return False
        if self.client:
            await self.client.disconnect()
        acc = ACCOUNTS[index]
        self.client = TelegramClient(acc['session_name'], API_ID, API_HASH)
        await self.client.start(phone=acc['phone'])
        if await self.client.is_user_authorized():
            self.current_index = index
            logging.info(f"✅ {acc['username']} авторизован")
            return True
        return False
    
    async def send_message(self, chat_id, text):
        try:
            await self.client.send_message(chat_id, text)
            return True, None
        except Exception as e:
            error = str(e)
            if "403" in error or "FLOOD" in error or "USER_IS_BLOCKED" in error:
                if self.current_index + 1 < len(ACCOUNTS):
                    await self.switch_to_account(self.current_index + 1)
                    return False, "Аккаунт забанен, переключен на резервный"
            return False, f"Ошибка: {error}"

account_manager = AccountManager()