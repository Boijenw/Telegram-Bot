import os

# Бот
BOT_TOKEN = "8978660580:AAGH9665OkD_7PHmdn4bXrmwdRFksMuvdpk"
ADMIN_USERNAMES = ["Senko_live"]
MAIN_ADMIN = "@Senko_live"

# API Telegram (получить на my.telegram.org)
API_ID = 35577943
API_HASH = "89272d75cfd5b0c490be821ddad3aa06"

# Аккаунты для рассылки
ACCOUNTS = [
    {
        "phone": "+79936989427",
        "session_name": "main_account",
        "username": "@seqrp"
    },
    {
        "phone": "+79939245508",
        "session_name": "backup_account",
        "username": "@Question088"
    }
]

# Реквизиты для оплаты
BANK_CARD = "2200701793366904"
CRYPTO_WALLET = "UQDRAZiYpNEzRSf-dwiwQVbxpEb_a-Aw50Iv5igfzQ1Hk82Z"

# Цены (в рублях и звездах)
PRICES = {
    10000: {"rub": 50, "stars": 25},
    20000: {"rub": 100, "stars": 50},
    50000: {"rub": 250, "stars": 100},
    100000: {"rub": 500, "stars": 125}
}