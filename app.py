from datetime import date
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import func

from config import APP_NAME, SECRET_KEY
from database import (
    init_db,
    get_session,
    upsert_contract,
    replace_payment_events,
    create_upload_batch,
    get_upload_batches,
    delete_upload_batch,
)
from models import Contract, ReminderLog, PaymentEvent
from utils import (
    preprocess_excel_dataframe,
    validate_required_fields,
    row_to_contract_payload,
    parse_payment_schedule_dates,
)
from reminder_engine import run_all_reminders

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

init_db()


def build_pie_data(labels, values, colors):
    total = sum(values)
    if total <= 0:
        total = 1

    segments = []
    current_deg = 0.0

    for label, value, color in zip(labels, values, colors):
        share = (value / total) * 360
        start_deg = current_deg
        end_deg = current_deg + share
        percent = round((value / total) * 100, 1)

        segments.append({
            "label": label,
            "value": value,
            "color": color,
            "percent": percent,
            "start_deg": round(start_deg, 2),
            "end_deg": round(end_deg, 2),
        })

        current_deg = end_deg

    gradient = ", ".join(
        f"{seg['color']} {seg['start_deg']}deg {seg['end_deg']}deg"
        for seg in segments
    )

    return {
        "segments": segments,
        "gradient": gradient if gradient else "#e5e7eb 0deg 360deg"
    }


def contracts_to_rows(session):
    contracts = session.query(Contract).order_by(Contract.vendor_name.asc()).all()
    rows = []

    for c in contracts:
        days_left = None
        if c.po_expiry_date:
            days_left = (c.po_expiry_date - date.today()).days

        rows.append({
            "id": c.id,
            "upload_batch_id": c.upload_batch_id,
            "vendor_name": c.vendor_name,
            "po_no": c.po_no,
            "service_type": c.service_type_sub or c.service_type_main,
            "location": c.location,
            "po_expiry_date": c.po_expiry_date,
            "days_left": days_left,
            "payment_schedule": c.payment_schedule,
            "payment_schedule_date_raw": c.payment_schedule_date_raw,
            "renewal_amount": c.renewal_amount,
            "total_amount": c.total_amount,
            "contact_person": c.contact_person,
            "phone_no": c.phone_no,
            "email_id": c.email_id,
            "status": c.status,
        })

    return rows


@app.route("/")
def dashboard():
    session = get_session()
    try:
        contracts = contracts_to_rows(session)

        overdue = [x for x in contracts if x["days_left"] is not None and x["days_left"] < 0]
        due_7 = [x for x in contracts if x["days_left"] is not None and 0 <= x["days_left"] <= 7]
        due_15 = [x for x in contracts if x["days_left"] is not None and 0 <= x["days_left"] <= 15]
        due_30 = [x for x in contracts if x["days_left"] is not None and 0 <= x["days_left"] <= 30]
        future = [x for x in contracts if x["days_left"] is not None and x["days_left"] > 30]

        total_logs = session.query(func.count(ReminderLog.id)).scalar() or 0
        total_payment_events = session.query(func.count(PaymentEvent.id)).scalar() or 0

        due_labels = ["Overdue", "Due in 7 Days", "Due in 15 Days", "Due in 30 Days", "Future"]
        due_values = [len(overdue), len(due_7), len(due_15), len(due_30), len(future)]
        due_colors = ["#dc3545", "#fd7e14", "#f59e0b", "#0d6efd", "#198754"]
        due_status_pie = build_pie_data(due_labels, due_values, due_colors)

        service_counts = {}
        for row in contracts:
            key = row["service_type"] or "Unknown"
            service_counts[key] = service_counts.get(key, 0) + 1

        service_labels = list(service_counts.keys())
        service_values = list(service_counts.values())
        service_colors = [
            "#2563eb", "#16a34a", "#f59e0b", "#9333ea", "#ef4444",
            "#0ea5e9", "#84cc16", "#f97316", "#14b8a6", "#8b5cf6"
        ]
        if len(service_labels) > len(service_colors):
            service_colors.extend(["#6b7280"] * (len(service_labels) - len(service_colors)))

        service_type_pie = build_pie_data(service_labels, service_values, service_colors[:len(service_labels)])

        location_counts = {}
        for row in contracts:
            key = row["location"] or "Unknown"
            location_counts[key] = location_counts.get(key, 0) + 1

        sorted_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)
        max_location_value = max([v for _, v in sorted_locations], default=1)

        location_bars = []
        for label, value in sorted_locations:
            width_percent = round((value / max_location_value) * 100, 2) if max_location_value else 0
            location_bars.append({
                "label": label,
                "value": value,
                "width_percent": width_percent
            })

        return render_template(
            "dashboard.html",
            app_name=APP_NAME,
            total_contracts=len(contracts),
            overdue_count=len(overdue),
            due_7_count=len(due_7),
            due_15_count=len(due_15),
            due_30_count=len(due_30),
            payment_event_count=total_payment_events,
            reminder_log_count=total_logs,
            overdue=overdue[:10],
            due_7=due_7[:10],
            due_status_pie=due_status_pie,
            service_type_pie=service_type_pie,
            location_bars=location_bars,
        )
    finally:
        session.close()


@app.route("/upload", methods=["GET", "POST"])
def upload():
    preview_rows = []
    validation_issues = []

    if request.method == "POST":
        file = request.files.get("file")

        if not file or file.filename == "":
            flash("Please choose an Excel file.", "danger")
            return render_template(
                "upload.html",
                app_name=APP_NAME,
                preview_rows=[],
                validation_issues=[],
            )

        try:
            df = pd.read_excel(file, header=0)
            df = df.dropna(how="all")

            cleaned_df = preprocess_excel_dataframe(df)
            validation_issues = validate_required_fields(cleaned_df)
            preview_rows = cleaned_df.head(20).fillna("").to_dict(orient="records")

            if "save_data" not in request.form:
                if validation_issues:
                    flash("Preview generated with validation issues.", "warning")
                else:
                    flash("Preview generated successfully.", "info")

                return render_template(
                    "upload.html",
                    app_name=APP_NAME,
                    preview_rows=preview_rows,
                    validation_issues=validation_issues,
                )

            if validation_issues:
                flash("Validation issues found. Please correct the file before saving.", "danger")
                return render_template(
                    "upload.html",
                    app_name=APP_NAME,
                    preview_rows=preview_rows,
                    validation_issues=validation_issues,
                )

            session = get_session()
            try:
                batch = create_upload_batch(session, file.filename, len(cleaned_df))

                inserted = 0
                updated = 0

                for _, row in cleaned_df.iterrows():
                    payload = row_to_contract_payload(row)
                    payload["upload_batch_id"] = batch.id

                    contract, action = upsert_contract(session, payload)

                    raw_payment_text = str(payload.get("payment_schedule_date_raw", "") or "")
                    payment_dates = parse_payment_schedule_dates(raw_payment_text)

                    replace_payment_events(
                        session=session,
                        contract_id=contract.id,
                        payment_dates=payment_dates,
                        source_text=raw_payment_text,
                    )

                    if action == "inserted":
                        inserted += 1
                    else:
                        updated += 1

                session.commit()
                flash(
                    f"Upload successful. Batch ID: {batch.id}, Inserted: {inserted}, Updated: {updated}",
                    "success"
                )
                return redirect(url_for("upload_history"))

            except Exception as db_error:
                session.rollback()
                flash(f"Database error while saving file: {db_error}", "danger")
            finally:
                session.close()

        except Exception as e:
            flash(f"Error processing file: {e}", "danger")

    return render_template(
        "upload.html",
        app_name=APP_NAME,
        preview_rows=preview_rows,
        validation_issues=validation_issues,
    )


@app.route("/upload-history")
def upload_history():
    session = get_session()
    try:
        batches = get_upload_batches(session)
        rows = []
        for b in batches:
            rows.append({
                "id": b.id,
                "file_name": b.file_name,
                "uploaded_at": b.uploaded_at,
                "total_rows": b.total_rows,
                "contract_count": len(b.contracts),
            })
        return render_template("upload_history.html", app_name=APP_NAME, rows=rows)
    finally:
        session.close()


@app.route("/delete-upload/<int:batch_id>", methods=["POST"])
def delete_uploaded_batch(batch_id):
    session = get_session()
    try:
        ok = delete_upload_batch(session, batch_id)
        if ok:
            session.commit()
            flash("Upload batch deleted successfully. Dashboard and charts have been updated.", "success")
        else:
            flash("Upload batch not found.", "warning")
    except Exception as e:
        session.rollback()
        flash(f"Failed to delete upload batch: {e}", "danger")
    finally:
        session.close()

    return redirect(url_for("upload_history"))


@app.route("/contracts")
def contracts():
    session = get_session()
    try:
        rows = contracts_to_rows(session)

        vendor = request.args.get("vendor", "").strip().lower()
        location = request.args.get("location", "").strip().lower()
        search = request.args.get("search", "").strip().lower()
        due_status = request.args.get("due_status", "").strip()

        if vendor:
            rows = [r for r in rows if vendor in (r["vendor_name"] or "").lower()]

        if location:
            rows = [r for r in rows if location in (r["location"] or "").lower()]

        if search:
            rows = [
                r for r in rows
                if search in (r["vendor_name"] or "").lower()
                or search in (r["po_no"] or "").lower()
                or search in (r["contact_person"] or "").lower()
                or search in (r["service_type"] or "").lower()
                or search in (r["payment_schedule_date_raw"] or "").lower()
            ]

        if due_status == "overdue":
            rows = [r for r in rows if r["days_left"] is not None and r["days_left"] < 0]
        elif due_status == "7":
            rows = [r for r in rows if r["days_left"] is not None and 0 <= r["days_left"] <= 7]
        elif due_status == "15":
            rows = [r for r in rows if r["days_left"] is not None and 0 <= r["days_left"] <= 15]
        elif due_status == "30":
            rows = [r for r in rows if r["days_left"] is not None and 0 <= r["days_left"] <= 30]

        return render_template("contracts.html", app_name=APP_NAME, rows=rows)
    finally:
        session.close()


@app.route("/payment-events")
def payment_events():
    session = get_session()
    try:
        events = session.query(PaymentEvent).order_by(PaymentEvent.payment_due_date.asc()).all()
        rows = []
        for e in events:
            contract = session.query(Contract).filter(Contract.id == e.contract_id).first()
            rows.append({
                "vendor_name": contract.vendor_name if contract else "",
                "po_no": contract.po_no if contract else "",
                "payment_due_date": e.payment_due_date,
                "source_text": e.source_text,
                "status": e.status,
            })
        return render_template("payment_events.html", app_name=APP_NAME, rows=rows)
    finally:
        session.close()


@app.route("/reminder-logs")
def reminder_logs():
    session = get_session()
    try:
        logs = session.query(ReminderLog).order_by(ReminderLog.created_at.desc()).all()
        rows = []
        for r in logs:
            contract = session.query(Contract).filter(Contract.id == r.contract_id).first()
            rows.append({
                "vendor_name": contract.vendor_name if contract else "",
                "po_no": contract.po_no if contract else "",
                "reminder_type": r.reminder_type,
                "target_date": r.target_date,
                "days_left": r.days_left,
                "recipient_email": r.recipient_email,
                "status": r.status,
                "sent_at": r.sent_at,
                "error_message": r.error_message,
                "created_at": r.created_at,
            })
        return render_template("reminder_logs.html", app_name=APP_NAME, rows=rows)
    finally:
        session.close()


@app.route("/run-reminders", methods=["POST"])
def run_reminders():
    session = get_session()
    try:
        result = run_all_reminders(session)
        flash(f"Reminder engine completed: {result}", "success")
    except Exception as e:
        flash(f"Reminder run failed: {e}", "danger")
    finally:
        session.close()

    return redirect(url_for("reminder_logs"))


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, host="127.0.0.1", port=5000)