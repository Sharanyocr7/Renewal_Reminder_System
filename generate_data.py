import pandas as pd
import random
from datetime import datetime, timedelta

# -------------------------------
# CONFIG
# -------------------------------
TOTAL_ROWS = 150
today = datetime.today()

# -------------------------------
# BASE DATA FROM YOUR SAMPLE
# -------------------------------
base_rows = [
    {
        "Sr. No": 1,
        "Service Type": "Renewal",
        "Category": "AMC",
        "Period": "April 2026 - March 2029",
        "Location": "Bandra",
        "Software / Application / Hardware": "IRAJE PIM Solution | 10 user pack - Subscription based license",
        "Vendor Name": "Unitcore Pvt Ltd",
        "Vendor Code": 1013973,
        "Po No": 3100000035,
        "PO Expiry Date": "31-Mar-29",
        "Payment Schedule": "Annually",
        "Payment Schedule Date": "April 2026, 2027, 2028",
        "Renewal amount without govt.Tax": 405000,
        "Total amount with All Tax": 477900,
        "Comment": "",
        "Remarks": "10 user pack - Subscription based license (per Quarter)",
        "Contact Person": "Imran Khan",
        "Phone no": "9324913901",
        "Email id": "renewal@unitcore.in / imran.khan@unitcore.in"
    },
    {
        "Sr. No": 2,
        "Service Type": "Renewal",
        "Category": "AMC",
        "Period": "April 26 to April 27",
        "Location": "Bandra",
        "Software / Application / Hardware": "Export software",
        "Vendor Name": "Immortal computers P Ltd",
        "Vendor Code": 1006718,
        "Po No": 3100000045,
        "PO Expiry Date": "21-Jan-27",
        "Payment Schedule": "Annually Advance",
        "Payment Schedule Date": "Apr-26",
        "Renewal amount without govt.Tax": 13123,
        "Total amount with All Tax": 15485.14,
        "Comment": "",
        "Remarks": "EMSS Software AMC",
        "Contact Person": "Sales Dept",
        "Phone no": "9969630299",
        "Email id": "icl-acts@eximon.com"
    },
    {
        "Sr. No": 3,
        "Service Type": "Renewal",
        "Category": "Subscription",
        "Period": "Jan 2026 - Jan 2029",
        "Location": "Lote",
        "Software / Application / Hardware": "Autocad 3 Year - 3 Users License Renewal for Lote Users",
        "Vendor Name": "ARKANCE IN PRIVATE LIMITED",
        "Vendor Code": 1008974,
        "Po No": 3100000077,
        "PO Expiry Date": "21-Jan-29",
        "Payment Schedule": "One Time Advance",
        "Payment Schedule Date": "Apr-26",
        "Renewal amount without govt.Tax": 244500,
        "Total amount with All Tax": 288510,
        "Comment": "",
        "Remarks": "Contract No - 110002949874 | Serial No - 777-14448192",
        "Contact Person": "Komal Desai",
        "Phone no": "9319276166 / 8169306536",
        "Email id": "komal.desai@arkance.world"
    },
    {
        "Sr. No": 4,
        "Service Type": "Renewal",
        "Category": "Service",
        "Period": "April 2026 - Oct 2027",
        "Location": "All Locations",
        "Software / Application / Hardware": "ISO Consulting & Recertification",
        "Vendor Name": "Abattis Consulting Pvt Ltd",
        "Vendor Code": 1013338,
        "Po No": 3100000113,
        "PO Expiry Date": "Oct-27",
        "Payment Schedule": "As per defined in PO",
        "Payment Schedule Date": "",
        "Renewal amount without govt.Tax": 1700000,
        "Total amount with All Tax": 2006000,
        "Comment": "",
        "Remarks": "",
        "Contact Person": "Ajay Kumar",
        "Phone no": "9711996836",
        "Email id": "ajay.kumar@abattisconsulting.com"
    },
]

# -------------------------------
# MASTER CHOICES
# -------------------------------
software_options = [
    ("IRAJE PIM Solution | 10 user pack - Subscription based license", "Unitcore Pvt Ltd", "Imran Khan", "9324913901", "renewal@unitcore.in / imran.khan@unitcore.in", "AMC", "Bandra", "Annually", "April 2026, 2027, 2028", 405000, 477900, "10 user pack - Subscription based license (per Quarter)"),
    ("Export software", "Immortal computers P Ltd", "Sales Dept", "9969630299", "icl-acts@eximon.com", "AMC", "Bandra", "Annually Advance", "Apr-26", 13123, 15485.14, "EMSS Software AMC"),
    ("Autocad 3 Year - 3 Users License Renewal for Lote Users", "ARKANCE IN PRIVATE LIMITED", "Komal Desai", "9319276166 / 8169306536", "komal.desai@arkance.world", "Subscription", "Lote", "One Time Advance", "Apr-26", 244500, 288510, "Contract No - 110002949874 | Serial No - 777-14448192"),
    ("ISO Consulting & Recertification", "Abattis Consulting Pvt Ltd", "Ajay Kumar", "9711996836", "ajay.kumar@abattisconsulting.com", "Service", "All Locations", "As per defined in PO", "", 1700000, 2006000, ""),
    ("SAP License Renewal", "TechNova Systems Pvt Ltd", "Rohan Mehta", "9820012345", "rohan.mehta@technova.com", "Subscription", "Mumbai HO", "Annually", "May-26", 350000, 413000, "Enterprise license support"),
    ("Firewall Annual Support", "SecureNet Solutions", "Neha Verma", "9876543210", "neha@securenet.com", "AMC", "Plant 1", "Annually Advance", "Jun-26", 95000, 112100, "Cybersecurity support contract"),
    ("Microsoft 365 Business Renewal", "CloudEdge Pvt Ltd", "Amit Sinha", "9811122233", "amit.sinha@cloudedge.com", "Subscription", "All Locations", "Annually", "Jul-26", 180000, 212400, "50 user annual subscription"),
    ("CCTV Maintenance Contract", "VisionTrack Services", "Pooja Nair", "9898989898", "pooja.nair@visiontrack.com", "Service", "Warehouse", "Quarterly", "Apr-26, Jul-26, Oct-26", 76000, 89680, "Includes 24/7 support"),
]

period_options = [
    "April 2026 - March 2029",
    "Jan 2026 - Jan 2029",
    "April 2026 - Oct 2027",
    "May 2026 - April 2027",
    "June 2026 - May 2028"
]

# -------------------------------
# STATUS DATE LOGIC
# -------------------------------
status_buckets = [
    ("Overdue", -random.randint(1, 60)),
    ("7 Days Left", 7),
    ("15 Days Left", 15),
    ("30 Days Left", 30)
]

def format_date(dt):
    return dt.strftime("%d-%b-%y")

def create_mock_row(sr_no, status_name, days_offset):
    item = random.choice(software_options)
    software, vendor, contact, phone, email, category, location, payment_schedule, payment_schedule_date, amt_wo_tax, amt_with_tax, remarks = item

    expiry_date = today + timedelta(days=days_offset)

    # add some variation
    vendor_code = random.randint(1000000, 1999999)
    po_no = random.randint(3100000000, 3199999999)

    amount_factor = random.uniform(0.9, 1.15)
    renewal_amt = round(amt_wo_tax * amount_factor, 2)
    total_amt = round(amt_with_tax * amount_factor, 2)

    comment = status_name

    return {
        "Sr. No": sr_no,
        "Service Type": "Renewal",
        "Category": category,
        "Period": random.choice(period_options),
        "Location": location,
        "Software / Application / Hardware": software,
        "Vendor Name": vendor,
        "Vendor Code": vendor_code,
        "Po No": po_no,
        "PO Expiry Date": format_date(expiry_date),
        "Payment Schedule": payment_schedule,
        "Payment Schedule Date": payment_schedule_date,
        "Renewal amount without govt.Tax": renewal_amt,
        "Total amount with All Tax": total_amt,
        "Comment": comment,
        "Remarks": remarks,
        "Contact Person": contact,
        "Phone no": phone,
        "Email id": email
    }

# -------------------------------
# BUILD FINAL DATA
# -------------------------------
all_rows = []

# first keep your original-style rows
for row in base_rows:
    all_rows.append(row)

remaining = TOTAL_ROWS - len(base_rows)

# make balanced status mix
status_plan = (
    [("Overdue", -random.randint(1, 60)) for _ in range(remaining // 4)] +
    [("7 Days Left", 7) for _ in range(remaining // 4)] +
    [("15 Days Left", 15) for _ in range(remaining // 4)] +
    [("30 Days Left", 30) for _ in range(remaining - 3 * (remaining // 4))]
)

random.shuffle(status_plan)

sr_no = len(all_rows) + 1
for status_name, days_offset in status_plan:
    all_rows.append(create_mock_row(sr_no, status_name, days_offset))
    sr_no += 1

# -------------------------------
# CREATE DATAFRAME
# -------------------------------
df = pd.DataFrame(all_rows)

# -------------------------------
# SAVE TO EXCEL
# -------------------------------
output_file = "renewal_mock_150_rows.xlsx"
df.to_excel(output_file, index=False)
print(f"Excel file created successfully: {output_file}")
print("Saved at current folder")