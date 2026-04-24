from datetime import date, datetime
from config import DEFAULT_REMINDER_DAYS, INTERNAL_ALERT_EMAIL
from database import reminder_exists, create_reminder_log
from email_service import send_email
from models import Contract, PaymentEvent


def build_expiry_subject(contract: Contract, days_left: int):
    if days_left < 0:
        return f"OVERDUE Renewal Alert | {contract.vendor_name} | PO {contract.po_no}"
    if days_left == 0:
        return f"Renewal Due Today | {contract.vendor_name} | PO {contract.po_no}"
    return f"Renewal Reminder ({days_left} day(s) left) | {contract.vendor_name} | PO {contract.po_no}"


def build_expiry_body(contract: Contract, days_left: int):
    return f"""
Dear {contract.contact_person or "Team"},

This is an automated renewal reminder from Gharda Chemicals Limited.

Contract Details
----------------
Vendor Name      : {contract.vendor_name}
Service Type     : {contract.service_type_sub or contract.service_type_main}
Location         : {contract.location}
Software/Service : {contract.software_name}
Vendor Code      : {contract.vendor_code}
PO Number        : {contract.po_no}
PO Expiry Date   : {contract.po_expiry_date}
Payment Schedule : {contract.payment_schedule}
Payment Dates    : {contract.payment_schedule_date_raw}
Renewal Amount   : {contract.renewal_amount}
Total Amount     : {contract.total_amount}
Remarks          : {contract.remarks}

Days Left: {days_left}

Please review and initiate the renewal process as required.

Regards,
Gharda Renewal Reminder System
""".strip()


def build_payment_subject(contract: Contract, due_date, days_left: int):
    if days_left < 0:
        return f"OVERDUE Payment Alert | {contract.vendor_name} | PO {contract.po_no}"
    if days_left == 0:
        return f"Payment Due Today | {contract.vendor_name} | PO {contract.po_no}"
    return f"Payment Reminder ({days_left} day(s) left) | {contract.vendor_name} | PO {contract.po_no}"


def build_payment_body(contract: Contract, due_date, days_left: int):
    return f"""
Dear {contract.contact_person or "Team"},

This is an automated payment reminder from Gharda Chemicals Limited.

Contract Details
----------------
Vendor Name      : {contract.vendor_name}
Service Type     : {contract.service_type_sub or contract.service_type_main}
Location         : {contract.location}
Software/Service : {contract.software_name}
Vendor Code      : {contract.vendor_code}
PO Number        : {contract.po_no}
Payment Due Date : {due_date}
Payment Schedule : {contract.payment_schedule}
Payment Dates    : {contract.payment_schedule_date_raw}
Renewal Amount   : {contract.renewal_amount}
Total Amount     : {contract.total_amount}
Remarks          : {contract.remarks}

Days Left: {days_left}

Please review and take the necessary action.

Regards,
Gharda Renewal Reminder System
""".strip()


def run_expiry_reminders(session):
    today = date.today()
    stats = {"processed": 0, "sent": 0, "failed": 0, "skipped": 0}

    contracts = session.query(Contract).filter(Contract.status == "ACTIVE").all()

    for contract in contracts:
        if not contract.po_expiry_date:
            stats["skipped"] += 1
            continue

        days_left = (contract.po_expiry_date - today).days
        should_send = (days_left in DEFAULT_REMINDER_DAYS) or (days_left < 0)

        if not should_send:
            stats["skipped"] += 1
            continue

        reminder_type = "EXPIRY_REMINDER"
        target_date = contract.po_expiry_date

        if reminder_exists(session, contract.id, reminder_type, target_date):
            stats["skipped"] += 1
            continue

        recipients = contract.email_id or INTERNAL_ALERT_EMAIL
        subject = build_expiry_subject(contract, days_left)
        body = build_expiry_body(contract, days_left)

        ok, error = send_email(recipients, subject, body)

        create_reminder_log(
            session=session,
            contract_id=contract.id,
            reminder_type=reminder_type,
            target_date=target_date,
            days_left=days_left,
            recipient_email=recipients,
            subject=subject,
            body=body,
            status="SENT" if ok else "FAILED",
            error_message=error,
            sent_at=datetime.utcnow() if ok else None,
        )

        stats["processed"] += 1
        if ok:
            stats["sent"] += 1
        else:
            stats["failed"] += 1

    session.commit()
    return stats


def run_payment_reminders(session):
    today = date.today()
    stats = {"processed": 0, "sent": 0, "failed": 0, "skipped": 0}

    events = session.query(PaymentEvent).filter(PaymentEvent.status == "ACTIVE").all()

    for event in events:
        contract = session.query(Contract).filter(Contract.id == event.contract_id).first()
        if not contract or contract.status != "ACTIVE":
            stats["skipped"] += 1
            continue

        days_left = (event.payment_due_date - today).days
        should_send = (days_left in DEFAULT_REMINDER_DAYS) or (days_left < 0)

        if not should_send:
            stats["skipped"] += 1
            continue

        reminder_type = "PAYMENT_REMINDER"
        target_date = event.payment_due_date

        if reminder_exists(session, contract.id, reminder_type, target_date):
            stats["skipped"] += 1
            continue

        recipients = contract.email_id or INTERNAL_ALERT_EMAIL
        subject = build_payment_subject(contract, event.payment_due_date, days_left)
        body = build_payment_body(contract, event.payment_due_date, days_left)

        ok, error = send_email(recipients, subject, body)

        create_reminder_log(
            session=session,
            contract_id=contract.id,
            reminder_type=reminder_type,
            target_date=target_date,
            days_left=days_left,
            recipient_email=recipients,
            subject=subject,
            body=body,
            status="SENT" if ok else "FAILED",
            error_message=error,
            sent_at=datetime.utcnow() if ok else None,
        )

        stats["processed"] += 1
        if ok:
            stats["sent"] += 1
        else:
            stats["failed"] += 1

    session.commit()
    return stats


def run_all_reminders(session):
    return {
        "expiry": run_expiry_reminders(session),
        "payment": run_payment_reminders(session),
    }