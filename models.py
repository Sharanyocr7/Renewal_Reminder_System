from datetime import datetime
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
)

Base = declarative_base()


class UploadBatch(Base):
    __tablename__ = "upload_batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    total_rows = Column(Integer, default=0)

    contracts = relationship("Contract", back_populates="upload_batch", cascade="all, delete-orphan")


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, autoincrement=True)

    upload_batch_id = Column(Integer, ForeignKey("upload_batches.id"), nullable=True)

    sr_no = Column(String(50))
    service_type_main = Column(String(100))
    service_type_sub = Column(String(100))
    period = Column(String(255))
    location = Column(String(255))
    software_name = Column(Text)
    vendor_name = Column(String(255), nullable=False)
    vendor_code = Column(String(100))
    po_no = Column(String(100), nullable=False)
    po_expiry_date = Column(Date)
    payment_schedule = Column(String(255))
    payment_schedule_date_raw = Column(Text)
    renewal_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    comment = Column(Text)
    remarks = Column(Text)
    contact_person = Column(String(255))
    phone_no = Column(Text)
    email_id = Column(Text)
    status = Column(String(50), default="ACTIVE")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    upload_batch = relationship("UploadBatch", back_populates="contracts")
    reminders = relationship("ReminderLog", back_populates="contract", cascade="all, delete-orphan")
    payment_events = relationship("PaymentEvent", back_populates="contract", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("po_no", "vendor_name", name="uq_contract_po_vendor"),
    )


class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    payment_due_date = Column(Date, nullable=False)
    source_text = Column(Text)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)

    contract = relationship("Contract", back_populates="payment_events")

    __table_args__ = (
        UniqueConstraint("contract_id", "payment_due_date", name="uq_contract_payment_due_date"),
    )


class ReminderLog(Base):
    __tablename__ = "reminder_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)

    reminder_type = Column(String(100), nullable=False)
    target_date = Column(Date, nullable=False)
    days_left = Column(Integer)
    recipient_email = Column(Text)
    subject = Column(Text)
    body = Column(Text)
    status = Column(String(50), default="PENDING")
    error_message = Column(Text)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    contract = relationship("Contract", back_populates="reminders")

    __table_args__ = (
        UniqueConstraint("contract_id", "reminder_type", "target_date", name="uq_reminder_unique"),
    )