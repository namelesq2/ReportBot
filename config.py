import os
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("TOKEN")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))
TIMEZONE_OFFSET = -3