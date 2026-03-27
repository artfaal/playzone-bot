import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.bot_token: str = os.environ["TELEGRAM_BOT_TOKEN"]
        self.database_path: str = os.environ.get("DATABASE_PATH", "/data/playzone.db")
        admin_ids_raw = os.environ.get("ADMIN_IDS", "")
        self.admin_ids: set[int] = {
            int(uid.strip())
            for uid in admin_ids_raw.split(",")
            if uid.strip().isdigit()
        }
        self.group_chat_id: int = int(os.environ["GROUP_CHAT_ID"])
        topic_id_raw = os.environ.get("TOPIC_THREAD_ID", "")
        self.topic_thread_id: int | None = int(topic_id_raw) if topic_id_raw.strip() else None


config = Config()
