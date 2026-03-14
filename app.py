from flask import Flask, render_template, request, redirect, url_for
import requests
from datetime import datetime
import os
import uuid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)

API_KEY = os.environ.get("GOOGLE_API_KEY")
SHEET_ID = os.environ.get("SHEET_ID")
MAX_LOCATIONS = 20

if not API_KEY or not SHEET_ID:
    raise RuntimeError("Missing GOOGLE_API_KEY or SHEET_ID environment variables.")


def sheet_url(sheet_name: str) -> str:
    return f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{sheet_name}"


def get_sheet(sheet_name: str) -> list[dict]:
    url = sheet_url(sheet_name) + f"?key={API_KEY}"
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    data = response.json()

    if "values" not in data or not data["values"]:
        return []

    headers = data["values"][0]
    rows = data["values"][1:]

    out = []
    for row in rows:
        padded = row + [""] * (len(headers) - len(row))
        out.append(dict(zip(headers, padded)))

    return out


def append_row(sheet_name: str, values: list[str]) -> None:
    url = sheet_url(sheet_name) + f":append?valueInputOption=RAW&key={API_KEY}"
    response = requests.post(url, json={"values": [values]}, timeout=20)
    response.raise_for_status()


def update_cell(sheet_name: str, row_index: int, col_index: int, value: str) -> None:
    cell = f"{chr(65 + col_index)}{row_index + 2}"
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/"
        f"{SHEET_ID}/values/{sheet_name}!{cell}?valueInputOption=RAW&key={API_KEY}"
    )
    response = requests.put(url, json={"values": [[value]]}, timeout=20)
    response.raise_for_status()


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

        # G column = Status
        update_cell("Deliveries", row_index, 6, "Collected")

        # I column = CollectedTime
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
