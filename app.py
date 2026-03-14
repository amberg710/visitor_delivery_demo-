from flask import Flask, render_template, request, redirect, url_for
import requests
from datetime import datetime
import os
import uuid

app = Flask(__name__, template_folder="templates")

API_KEY = os.environ.get("GOOGLE_API_KEY")
SHEET_ID = os.environ.get("SHEET_ID")

if not API_KEY or not SHEET_ID:
    raise ValueError("GOOGLE_API_KEY and SHEET_ID must be set in Render environment variables.")

MAX_LOCATIONS = 20


def values_url(sheet_name: str) -> str:
    return f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{sheet_name}"


def get_sheet(sheet_name: str):
    url = values_url(sheet_name) + f"?key={API_KEY}"
    res = requests.get(url, timeout=20)
    data = res.json()

    if "values" not in data:
        return []

    values = data["values"]
    if not values:
        return []

    headers = values[0]
    rows = values[1:]

    records = []
    for row in rows:
        padded = row + [""] * (len(headers) - len(row))
        records.append(dict(zip(headers, padded)))
    return records


def append_row(sheet_name: str, row_values: list):
    url = values_url(sheet_name) + f":append?valueInputOption=RAW&insertDataOption=INSERT_ROWS&key={API_KEY}"
    body = {"values": [row_values]}
    res = requests.post(url, json=body, timeout=20)
    res.raise_for_status()


def update_cell(sheet_name: str, row_index: int, col_index: int, value: str):
    cell = f"{chr(65 + col_index)}{row_index + 2}"
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{sheet_name}!{cell}?valueInputOption=RAW&key={API_KEY}"
    body = {"values": [[value]]}
    res = requests.put(url, json=body, timeout=20)
    res.raise_for_status()


def get_free_location(deliveries: list):
    used = set()

    for d in deliveries:
        status = d.get("Status", "").strip().lower()
        location = d.get("Location", "").strip()

        if status == "stored" and location.isdigit():
            used.add(int(location))

    for loc in range(1, MAX_LOCATIONS + 1):
        if loc not in used:
            return loc

    return None


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/deliveries")
def deliveries_page():
    deliveries = get_sheet("Deliveries")

    free_location = get_free_location(deliveries)

    used_locations = {
        int(d["Location"])
        for d in deliveries
        if d.get("Status", "").strip().lower() == "stored" and d.get("Location", "").isdigit()
    }

    available_locations = [i for i in range(1, MAX_LOCATIONS + 1) if i not in used_locations]

    return render_template(
        "deliveries.html",
        deliveries=deliveries,
        free_location=free_location,
        available_locations=available_locations
    )


@app.route("/receive_delivery", methods=["POST"])
def receive_delivery():
    item = request.form["item"].strip()
    employee = request.form["employee"].strip()
    email = request.form["email"].strip()
    courier = request.form["courier"].strip()

    deliveries = get_sheet("Deliveries")
    location = get_free_location(deliveries)

    if location is None:
        return "No free storage locations available.", 400

    parcel_id = str(uuid.uuid4())[:8].upper()
    received_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    append_row("Deliveries", [
        parcel_id,
        item,
        employee,
        email,
        courier,
        str(location),
        "Stored",
        received_time,
        ""
    ])

    return redirect(url_for("deliveries_page"))


@app.route("/collect_delivery", methods=["POST"])
def collect_delivery():
    row_index = int(request.form["row_index"])
    deliveries = get_sheet("Deliveries")

    if row_index < 0 or row_index >= len(deliveries):
        return redirect(url_for("deliveries_page"))

    collected_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # G = Status, I = CollectedTime
    update_cell("Deliveries", row_index, 6, "Collected")
    update_cell("Deliveries", row_index, 8, collected_time)

    return redirect(url_for("deliveries_page"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
