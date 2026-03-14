from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import uuid
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)

SHEET_ID = os.environ.get("SHEET_ID")
SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
MAX_LOCATIONS = 20
MAX_BADGES = 30

if not SHEET_ID or not SERVICE_ACCOUNT_JSON:
    raise RuntimeError("Missing SHEET_ID or GOOGLE_SERVICE_ACCOUNT_JSON environment variables.")


def get_sheets_service():
    creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
    credentials = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


def get_sheet(sheet_name: str) -> list[dict]:
    service = get_sheets_service()
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=SHEET_ID, range=sheet_name)
        .execute()
    )

    values = result.get("values", [])
    if not values:
        return []

    headers = values[0]
    rows = values[1:]

    out = []
    for row in rows:
        padded = row + [""] * (len(headers) - len(row))
        out.append(dict(zip(headers, padded)))

    return out


def append_row(sheet_name: str, values: list[str]) -> None:
    service = get_sheets_service()
    (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=SHEET_ID,
            range=sheet_name,
            valueInputOption="RAW",
            body={"values": [values]},
        )
        .execute()
    )


def update_cell(sheet_name: str, row_index: int, col_index: int, value: str) -> None:
    service = get_sheets_service()
    cell = f"{chr(65 + col_index)}{row_index + 2}"
    (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=SHEET_ID,
            range=f"{sheet_name}!{cell}",
            valueInputOption="RAW",
            body={"values": [[value]]},
        )
        .execute()
    )


def get_free_location(deliveries: list[dict]) -> int | None:
    used = set()

    for d in deliveries:
        status = d.get("Status", "").strip().lower()
        location = d.get("Location", "").strip()

        if status == "stored" and location.isdigit():
            used.add(int(location))

    for i in range(1, MAX_LOCATIONS + 1):
        if i not in used:
            return i

    return None


def get_used_badges(visitors: list[dict]) -> set[int]:
    used = set()
    for v in visitors:
        status = v.get("Status", "").strip().lower()
        badge = v.get("BadgeNumber", "").strip()
        if status == "in" and badge.isdigit():
            used.add(int(badge))
    return used


def get_available_badges(visitors: list[dict]) -> list[int]:
    used = get_used_badges(visitors)
    return [i for i in range(1, MAX_BADGES + 1) if i not in used]


def count_visitors_today(visitors: list[dict], today_str: str) -> int:
    return sum(1 for v in visitors if v.get("Date", "").strip() == today_str)


def count_visitors_inside(visitors: list[dict]) -> int:
    return sum(1 for v in visitors if v.get("Status", "").strip().lower() == "in")


def monthly_counts(visitors: list[dict]) -> dict[str, int]:
    counts = {}
    for v in visitors:
        date_str = v.get("Date", "").strip()
        if len(date_str) >= 7:
            key = date_str[:7]
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), reverse=True))


def yearly_counts(visitors: list[dict]) -> dict[str, int]:
    counts = {}
    for v in visitors:
        date_str = v.get("Date", "").strip()
        if len(date_str) >= 4:
            key = date_str[:4]
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), reverse=True))


def get_today_prebooked(prebooked: list[dict], today_str: str) -> list[dict]:
    return [
        p for p in prebooked
        if p.get("VisitDate", "").strip() == today_str
    ]


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/deliveries")
def deliveries_page():
    try:
        deliveries = get_sheet("Deliveries")
        free_location = get_free_location(deliveries)

        used = {
            int(d["Location"])
            for d in deliveries
            if d.get("Status", "").strip().lower() == "stored"
            and d.get("Location", "").isdigit()
        }

        available_locations = [i for i in range(1, MAX_LOCATIONS + 1) if i not in used]

        return render_template(
            "deliveries.html",
            deliveries=deliveries,
            free_location=free_location,
            available_locations=available_locations,
        )
    except Exception as e:
        return f"/deliveries failed: {str(e)}", 500


@app.route("/log_delivery", methods=["POST"])
def log_delivery():
    try:
        item = request.form.get("item", "").strip()
        employee = request.form.get("employee", "").strip()
        email = request.form.get("email", "").strip()
        courier = request.form.get("courier", "").strip()

        if not item or not employee or not email or not courier:
            return "Missing required fields.", 400

        deliveries = get_sheet("Deliveries")
        location = get_free_location(deliveries)

        if location is None:
            return "No free storage locations available.", 400

        parcel_id = str(uuid.uuid4())[:8].upper()
        received_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        append_row(
            "Deliveries",
            [
                parcel_id,
                item,
                employee,
                email,
                courier,
                str(location),
                "Stored",
                received_time,
                "",
            ],
        )

        return redirect(url_for("deliveries_page"))
    except Exception as e:
        return f"log_delivery failed: {str(e)}", 500


@app.route("/collect_delivery", methods=["POST"])
def collect_delivery():
    try:
        row_index_raw = request.form.get("row_index", "").strip()

        if not row_index_raw.isdigit():
            return "Invalid row index.", 400

        row_index = int(row_index_raw)
        deliveries = get_sheet("Deliveries")

        if row_index < 0 or row_index >= len(deliveries):
            return "Row index out of range.", 400

        collected_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        update_cell("Deliveries", row_index, 6, "Collected")
        update_cell("Deliveries", row_index, 8, collected_time)

        return redirect(url_for("deliveries_page"))
    except Exception as e:
        return f"collect_delivery failed: {str(e)}", 500


@app.route("/checkin")
def checkin_page():
    try:
        visitors = get_sheet("Visitors")
        available_badges = get_available_badges(visitors)
        return render_template("checkin.html", available_badges=available_badges)
    except Exception as e:
        return f"/checkin failed: {str(e)}", 500


@app.route("/log_visitor", methods=["POST"])
def log_visitor():
    try:
        name = request.form.get("name", "").strip()
        id_number = request.form.get("id_number", "").strip()
        purpose = request.form.get("purpose", "").strip()
        other_purpose = request.form.get("other_purpose", "").strip()
        host = request.form.get("host", "").strip()
        badge_number = request.form.get("badge_number", "").strip()

        if purpose == "Other" and other_purpose:
            purpose = other_purpose

        if not name or not purpose or not host or not badge_number:
            return "Missing required fields.", 400

        if not badge_number.isdigit():
            return "Invalid badge number.", 400

        badge_number_int = int(badge_number)

        if badge_number_int < 1 or badge_number_int > MAX_BADGES:
            return "Badge number out of range.", 400

        visitors = get_sheet("Visitors")
        available_badges = get_available_badges(visitors)

        if badge_number_int not in available_badges:
            return "Selected badge is no longer available.", 400

        if any(
            v.get("Status", "").strip().lower() == "in"
            and v.get("BadgeNumber", "").strip() == str(badge_number_int)
            for v in visitors
        ):
            return "Badge is already assigned to another visitor.", 400

        visitor_id = str(uuid.uuid4())[:8].upper()
        now = datetime.now()
        checkin_time = now.strftime("%Y-%m-%d %H:%M:%S")
        date_only = now.strftime("%Y-%m-%d")

        append_row(
            "Visitors",
            [
                visitor_id,
                name,
                id_number,
                purpose,
                host,
                str(badge_number_int),
                "In",
                checkin_time,
                "",
                date_only,
            ],
        )

        return redirect(url_for("visitors_page"))
    except Exception as e:
        return f"log_visitor failed: {str(e)}", 500


@app.route("/visitors")
def visitors_page():
    try:
        visitors = get_sheet("Visitors")
        prebooked = get_sheet("PrebookedVisitors")
        today_str = datetime.now().strftime("%Y-%m-%d")

        active_visitors = [
            v for v in visitors if v.get("Status", "").strip().lower() == "in"
        ]

        todays_prebooked = get_today_prebooked(prebooked, today_str)

        return render_template(
            "visitors.html",
            visitors=visitors,
            active_visitors=active_visitors,
            todays_prebooked=todays_prebooked,
        )
    except Exception as e:
        return f"/visitors failed: {str(e)}", 500


@app.route("/checkout_visitor", methods=["POST"])
def checkout_visitor():
    try:
        row_index_raw = request.form.get("row_index", "").strip()

        if not row_index_raw.isdigit():
            return "Invalid row index.", 400

        row_index = int(row_index_raw)
        visitors = get_sheet("Visitors")

        if row_index < 0 or row_index >= len(visitors):
            return "Row index out of range.", 400

        current_status = visitors[row_index].get("Status", "").strip().lower()
        if current_status != "in":
            return "Visitor is not currently checked in.", 400

        checkout_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        update_cell("Visitors", row_index, 6, "Out")
        update_cell("Visitors", row_index, 8, checkout_time)

        return redirect(url_for("visitors_page"))
    except Exception as e:
        return f"checkout_visitor failed: {str(e)}", 500


@app.route("/badges")
def badges_page():
    try:
        visitors = get_sheet("Visitors")
        used_badges = get_used_badges(visitors)

        active_by_badge = {}
        for v in visitors:
            if v.get("Status", "").strip().lower() == "in":
                badge = v.get("BadgeNumber", "").strip()
                if badge.isdigit():
                    active_by_badge[int(badge)] = v.get("Name", "").strip()

        badges = []
        for i in range(1, MAX_BADGES + 1):
            badges.append(
                {
                    "number": i,
                    "available": i not in used_badges,
                    "name": active_by_badge.get(i, ""),
                }
            )

        return render_template("badges.html", badges=badges)
    except Exception as e:
        return f"/badges failed: {str(e)}", 500


@app.route("/analytics")
def analytics_page():
    try:
        visitors = get_sheet("Visitors")
        today_str = datetime.now().strftime("%Y-%m-%d")

        used_badges = get_used_badges(visitors)

        stats = {
            "visitors_today": count_visitors_today(visitors, today_str),
            "visitors_inside": count_visitors_inside(visitors),
            "badges_in_use": len(used_badges),
            "badges_available": MAX_BADGES - len(used_badges),
            "monthly_counts": monthly_counts(visitors),
            "yearly_counts": yearly_counts(visitors),
        }

        return render_template("analytics.html", stats=stats)
    except Exception as e:
        return f"/analytics failed: {str(e)}", 500


@app.route("/health")
def health():
    try:
        visitors = get_sheet("Visitors")
        deliveries = get_sheet("Deliveries")
        return {
            "ok": True,
            "visitors_rows": len(visitors),
            "deliveries_rows": len(deliveries),
            "sheet_id": SHEET_ID,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
