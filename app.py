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


@app.route("/health")
def health():
    try:
        deliveries = get_sheet("Deliveries")
        return {
            "ok": True,
            "deliveries_rows": len(deliveries),
            "sheet_id": SHEET_ID,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
