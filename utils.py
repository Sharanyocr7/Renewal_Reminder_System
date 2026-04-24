import re
import calendar
from datetime import date
from dateutil.parser import parse
import pandas as pd


EXPECTED_COLUMNS = [
    "Sr. No",
    "Service Type",
    "Period",
    "Location",
    "Software / Application / Hardware",
    "Vendor Name",
    "Vendor  Code",
    "Po No",
    "PO Expiry Date",
    "Payment Schedule",
    "Payment Schedule Date",
    "Renewal amount without govt.Tax",
    "Total amount  with All Tax",
    "Comment",
    "Remarks",
    "Contact Person",
    "Phone no",
    "Email id",
]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().replace("\n", " ") for c in df.columns]
    return df


def apply_aliases(df: pd.DataFrame) -> pd.DataFrame:
    alias_map = {
        "Vendor Code": "Vendor  Code",
        "PO No": "Po No",
        "Phone No": "Phone no",
        "Email ID": "Email id",
    }
    for src, dst in alias_map.items():
        if src in df.columns and dst not in df.columns:
            df[dst] = df[src]
    return df


def ensure_all_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df


def safe_str(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def clean_currency(value) -> float:
    text = safe_str(value).replace(",", "")
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def clean_email_list(value: str) -> str:
    text = safe_str(value)
    if not text:
        return ""
    text = text.replace("\n", ",").replace(";", ",")
    emails = [e.strip() for e in text.split(",") if e.strip()]
    unique = []
    seen = set()
    for email in emails:
        lowered = email.lower()
        if lowered not in seen:
            unique.append(email)
            seen.add(lowered)
    return ",".join(unique)


def clean_phone_list(value: str) -> str:
    text = safe_str(value)
    if not text:
        return ""
    text = text.replace("\n", ",")
    phones = [p.strip() for p in text.split(",") if p.strip()]
    return ", ".join(phones)


def parse_date_safe(value):
    text = safe_str(value)
    if not text:
        return None

    try:
        dt = pd.to_datetime(text, errors="coerce", dayfirst=True)
        if not pd.isna(dt):
            return dt.date()
    except Exception:
        pass

    try:
        return parse(text, dayfirst=True, fuzzy=True).date()
    except Exception:
        return None


def month_name_to_number(name: str):
    mapping = {
        "jan": 1, "january": 1,
        "feb": 2, "february": 2,
        "mar": 3, "march": 3,
        "apr": 4, "april": 4,
        "may": 5,
        "jun": 6, "june": 6,
        "jul": 7, "july": 7,
        "aug": 8, "august": 8,
        "sep": 9, "sept": 9, "september": 9,
        "oct": 10, "october": 10,
        "nov": 11, "november": 11,
        "dec": 12, "december": 12,
    }
    return mapping.get(name.strip().lower())


def month_end_date(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def parse_payment_schedule_dates(raw_text: str):
    text = safe_str(raw_text)
    if not text:
        return []

    lowered = text.lower()
    if "as per defined in po" in lowered:
        return []

    single = parse_date_safe(text)
    if single:
        return [single]

    results = []

    pattern = re.match(r"^([A-Za-z]+)\s+(\d{4})(.*)$", text)
    if pattern:
        month_name = pattern.group(1)
        month_no = month_name_to_number(month_name)
        if month_no:
            years = re.findall(r"\d{4}", text)
            unique_years = []
            seen_years = set()
            for y in years:
                y_int = int(y)
                if y_int not in seen_years:
                    unique_years.append(y_int)
                    seen_years.add(y_int)
            for y in unique_years:
                results.append(month_end_date(y, month_no))
            return results

    parts = [p.strip() for p in re.split(r"[,\n]+", text) if p.strip()]
    for part in parts:
        dt = parse_date_safe(part)
        if dt:
            results.append(dt)

    unique_dates = []
    seen = set()
    for dt in results:
        if dt not in seen:
            unique_dates.append(dt)
            seen.add(dt)

    return unique_dates


def split_service_type(value: str):
    text = safe_str(value)
    if not text:
        return "Renewal", ""

    parts = [p.strip() for p in re.split(r"\s{2,}|\n+", text) if p.strip()]
    if len(parts) >= 2:
        return parts[0], parts[1]

    if text.lower() == "renewal":
        return "Renewal", ""

    return "Renewal", text


def preprocess_excel_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)
    df = apply_aliases(df)
    df = ensure_all_columns(df)

    main_types = []
    sub_types = []

    for val in df["Service Type"]:
        main_type, sub_type = split_service_type(val)
        main_types.append(main_type)
        sub_types.append(sub_type)

    df["service_type_main_clean"] = main_types
    df["service_type_sub_clean"] = sub_types
    df["po_expiry_date_clean"] = df["PO Expiry Date"].apply(parse_date_safe)
    df["email_clean"] = df["Email id"].apply(clean_email_list)
    df["phone_clean"] = df["Phone no"].apply(clean_phone_list)
    df["renewal_amount_clean"] = df["Renewal amount without govt.Tax"].apply(clean_currency)
    df["total_amount_clean"] = df["Total amount  with All Tax"].apply(clean_currency)

    return df


def validate_required_fields(df: pd.DataFrame):
    issues = []

    for idx, row in df.iterrows():
        excel_row = idx + 2

        if not safe_str(row.get("Vendor Name")):
            issues.append(f"Row {excel_row}: Vendor Name is missing.")
        if not safe_str(row.get("Po No")):
            issues.append(f"Row {excel_row}: Po No is missing.")
        if not row.get("po_expiry_date_clean"):
            issues.append(f"Row {excel_row}: PO Expiry Date is invalid or missing.")
        if not safe_str(row.get("Email id")):
            issues.append(f"Row {excel_row}: Email id is missing.")

    return issues


def row_to_contract_payload(row: pd.Series) -> dict:
    return {
        "sr_no": safe_str(row.get("Sr. No")),
        "service_type_main": safe_str(row.get("service_type_main_clean")) or "Renewal",
        "service_type_sub": safe_str(row.get("service_type_sub_clean")),
        "period": safe_str(row.get("Period")),
        "location": safe_str(row.get("Location")),
        "software_name": safe_str(row.get("Software / Application / Hardware")),
        "vendor_name": safe_str(row.get("Vendor Name")),
        "vendor_code": safe_str(row.get("Vendor  Code")),
        "po_no": safe_str(row.get("Po No")),
        "po_expiry_date": row.get("po_expiry_date_clean"),
        "payment_schedule": safe_str(row.get("Payment Schedule")),
        "payment_schedule_date_raw": safe_str(row.get("Payment Schedule Date")),
        "renewal_amount": float(row.get("renewal_amount_clean", 0.0)),
        "total_amount": float(row.get("total_amount_clean", 0.0)),
        "comment": safe_str(row.get("Comment")),
        "remarks": safe_str(row.get("Remarks")),
        "contact_person": safe_str(row.get("Contact Person")),
        "phone_no": safe_str(row.get("phone_clean")),
        "email_id": safe_str(row.get("email_clean")),
        "status": "ACTIVE",
    }