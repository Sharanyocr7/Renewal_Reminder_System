import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Gharda Renewal Reminder System")
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret")

DB_PATH = os.getenv("DB_PATH", "data/renewal_reminder.db")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", APP_NAME)

INTERNAL_ALERT_EMAIL = os.getenv("INTERNAL_ALERT_EMAIL", "")

DEFAULT_REMINDER_DAYS = sorted(
    {
        int(x.strip())
        for x in os.getenv("DEFAULT_REMINDER_DAYS", "90,60,30,15,7,3,1,0").split(",")
        if x.strip()
    },
    reverse=True
)