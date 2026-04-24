from database import init_db, get_session
from reminder_engine import run_all_reminders


def main():
    init_db()
    session = get_session()
    try:
        result = run_all_reminders(session)
        print("Reminder run completed.")
        print(result)
    finally:
        session.close()


if __name__ == "__main__":
    main()