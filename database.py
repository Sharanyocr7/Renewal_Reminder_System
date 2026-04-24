import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_PATH
from models import Base, Contract, PaymentEvent, ReminderLog, UploadBatch

db_dir = os.path.dirname(DB_PATH)
if db_dir:
    os.makedirs(db_dir, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()


def create_upload_batch(session, file_name: str, total_rows: int):
    batch = UploadBatch(file_name=file_name, total_rows=total_rows)
    session.add(batch)
    session.flush()
    return batch


def get_upload_batches(session):
    return session.query(UploadBatch).order_by(UploadBatch.uploaded_at.desc()).all()


def get_upload_batch_by_id(session, batch_id: int):
    return session.query(UploadBatch).filter(UploadBatch.id == batch_id).first()


def delete_upload_batch(session, batch_id: int):
    batch = get_upload_batch_by_id(session, batch_id)
    if not batch:
        return False
    session.delete(batch)
    session.flush()
    return True


def upsert_contract(session, payload: dict):
    existing = (
        session.query(Contract)
        .filter(Contract.po_no == payload["po_no"], Contract.vendor_name == payload["vendor_name"])
        .first()
    )

    if existing:
        for key, value in payload.items():
            setattr(existing, key, value)
        existing.updated_at = datetime.utcnow()
        session.flush()
        return existing, "updated"

    contract = Contract(**payload)
    session.add(contract)
    session.flush()
    return contract, "inserted"


def replace_payment_events(session, contract_id: int, payment_dates, source_text: str):
    session.query(PaymentEvent).filter(PaymentEvent.contract_id == contract_id).delete()
    for dt in payment_dates:
        session.add(
            PaymentEvent(
                contract_id=contract_id,
                payment_due_date=dt,
                source_text=source_text,
                status="ACTIVE"
            )
        )
    session.flush()


def reminder_exists(session, contract_id: int, reminder_type: str, target_date):
    return (
        session.query(ReminderLog)
        .filter(
            ReminderLog.contract_id == contract_id,
            ReminderLog.reminder_type == reminder_type,
            ReminderLog.target_date == target_date,
        )
        .first()
        is not None
    )


def create_reminder_log(
    session,
    contract_id,
    reminder_type,
    target_date,
    days_left,
    recipient_email,
    subject,
    body,
    status,
    error_message=None,
    sent_at=None,
):
    log = ReminderLog(
        contract_id=contract_id,
        reminder_type=reminder_type,
        target_date=target_date,
        days_left=days_left,
        recipient_email=recipient_email,
        subject=subject,
        body=body,
        status=status,
        error_message=error_message,
        sent_at=sent_at,
    )
    session.add(log)
    session.flush()
    return log