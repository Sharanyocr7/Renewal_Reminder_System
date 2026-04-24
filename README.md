# Gharda Renewal Reminder System

## Overview

The **Gharda Renewal Reminder System** is an internal web application designed to manage, track, and automate reminders for contract renewals, AMC services, subscriptions, and payment schedules.

The system enables users to upload Excel-based contract data, visualize upcoming renewals through dashboards, and ensure timely notifications to avoid missed deadlines.

This application is built with a focus on reliability, scalability, and usability for enterprise environments.

---

## Key Features

### 1. Excel-Based Data Ingestion

* Upload structured Excel files containing contract details
* Preview data before saving
* Validate required fields before insertion
* Supports large datasets (100+ records)

### 2. Upload Batch Management

* Each upload is tracked as a **separate batch**
* View upload history with metadata:

  * File name
  * Upload timestamp
  * Number of records
* Delete incorrect uploads safely

  * Automatically removes:

    * Contracts
    * Payment events
    * Reminder logs

### 3. Smart Dashboard

* Real-time metrics:

  * Total Contracts
  * Overdue Contracts
  * Due in 7 / 15 / 30 days
  * Payment Events
* Scroll-based analytics:

  * Due status distribution (Pie Chart)
  * Service type distribution (Pie Chart)
  * Location-wise contract distribution (Bar Chart)

### 4. Contract Management

* Centralized contract listing
* Search and filter:

  * Vendor
  * Location
  * Service type
  * Due status
* Displays days remaining for renewal

### 5. Payment Event Tracking

* Automatically parses payment schedule dates
* Generates structured payment events
* Tracks due dates for payments

### 6. Reminder Engine

* Automated reminder generation
* Avoids duplicate reminders
* Logs all reminders with status:

  * Sent
  * Failed
  * Pending

### 7. Clean UI / UX

* Background branding support (Gharda image)
* Glass-card UI design
* Responsive layout
* Enterprise-style dashboard

---

## Tech Stack

| Layer           | Technology                                   |
| --------------- | -------------------------------------------- |
| Backend         | Python (Flask)                               |
| Database        | SQLite (SQLAlchemy ORM)                      |
| Data Processing | Pandas, OpenPyXL                             |
| Scheduling      | APScheduler                                  |
| Frontend        | HTML, Bootstrap, Jinja2                      |
| Charts          | CSS-based rendering (no external dependency) |

---

## Project Structure

```
renewal_reminder_system/
│
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── database.py           # DB connection & operations
├── models.py             # ORM models
├── reminder_engine.py    # Reminder logic
├── utils.py              # Data processing utilities
├── scheduler_job.py      # Background scheduler
├── requirements.txt
│
├── data/
│   └── renewal_reminder.db
│
├── static/
│   └── images/
│       └── gharda_bg.jpg
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── upload.html
│   ├── upload_history.html
│   ├── contracts.html
│   ├── payment_events.html
│   └── reminder_logs.html
│
└── venv/
```

---

## Setup Instructions

### 1. Clone / Setup Project

```bash
git clone <repo-url>
cd renewal_reminder_system
```

### 2. Create Virtual Environment (Python 3.11 recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Application

```bash
python app.py
```

### 5. Access Application

```
http://127.0.0.1:5000
```

---

## Excel Upload Format

The system expects the following columns:

* Sr. No
* Service Type
* Period
* Location
* Software / Application / Hardware
* Vendor Name
* Vendor Code
* PO No
* PO Expiry Date
* Payment Schedule
* Payment Schedule Date
* Renewal Amount (without tax)
* Total Amount (with tax)
* Contact Person
* Phone No
* Email ID

---

## Upload Workflow

1. Upload Excel file
2. Preview data
3. Validate fields
4. Save as a batch
5. Data is inserted/updated
6. Dashboard updates automatically

---

## Delete Upload (Important Feature)

Users can delete a previously uploaded batch via **Upload History**.

### What happens on delete:

* All related contracts are removed
* Associated payment events are deleted
* Reminder logs are deleted
* Dashboard and charts update instantly

---

## Known Considerations

* SQLite is used for simplicity (can be replaced with PostgreSQL/MySQL for production)
* Date parsing depends on Excel format consistency
* Large files should be validated before upload

---

## Future Enhancements

* Email/SMS notification integration
* Role-based access control
* Audit logging
* Export reports (PDF/Excel)
* Cloud deployment (AWS/Azure)
* Advanced analytics dashboard

---

## Author

**Sharanyo Chatterjee**
Software Engineer
Gharda Chemicals Limited

---

## License

Internal Company Use Only
