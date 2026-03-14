from flask import Flask, request, redirect, render_template
import requests
from datetime import datetime, date
import os

app = Flask(__name__)

# --- Google Sheets API setup ---
API_KEY = os.environ.get("GOOGLE_API_KEY")
SPREADSHEET_ID = os.environ.get("SHEET_ID")

if not API_KEY or not SPREADSHEET_ID:
    raise ValueError("GOOGLE_API_KEY and SHEET_ID must be set as environment variables!")

def sheet_url(sheet_name):
    return f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{sheet_name}"

def get_sheet_data(sheet_name):
    url = f"{sheet_url(sheet_name)}?key={API_KEY}"
    res = requests.get(url).json()
    if "values" not in res or len(res["values"]) < 2:
        return []
    headers = res["values"][0]
    rows = res["values"][1:]
    return [dict(zip(headers, r)) for r in rows]

def update_sheet(sheet_name, col_letter, row_index, value):
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{sheet_name}!{col_letter}{row_index+2}?valueInputOption=RAW&key={API_KEY}"
    body = {"values": [[value]]}
    requests.put(url, json=body)

# --- Visitor functions ---
def get_today_visitors():
    visitors = get_sheet_data("VisitorsSchedule")
    today_str = date.today().strftime("%Y-%m-%d")
    return [v for v in visitors if v["ScheduledDate"] == today_str]

# --- Routes ---
@app.route("/")
def home():
    return render_template("home.html")

# Visitor check-in
@app.route("/checkin")
def checkin_page():
    today_visitors = get_today_visitors()
    badges = get_sheet_data("Badges")
    return render_template("checkin.html", today_visitors=today_visitors, badges=badges)

@app.route("/assign_badge", methods=["POST"])
def assign_badge():
    row_index = int(request.form["row_index"])
    badge_number = request.form["badge"]

    today_visitors = get_today_visitors()
    visitor_name = today_visitors[row_index]["Name"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    update_sheet("VisitorsSchedule", "F", row_index, badge_number)  # BadgeAssigned
    update_sheet("VisitorsSchedule", "D", row_index, now)           # CheckedIn
    update_sheet("VisitorsSchedule", "G", row_index, "Checked-in")  # Status

    badges = get_sheet_data("Badges")
    badge_row = next((i for i, b in enumerate(badges) if b["BadgeNumber"] == badge_number), None)
    if badge_row is not None:
        update_sheet("Badges", "B", badge_row, "Assigned")
        update_sheet("Badges", "C", badge_row, visitor_name)

    return redirect("/checkin")

@app.route("/checkout", methods=["POST"])
def checkout():
    row_index = int(request.form["row_index"])
    today_visitors = get_today_visitors()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    update_sheet("VisitorsSchedule", "E", row_index, now)           # CheckedOut
    update_sheet("VisitorsSchedule", "G", row_index, "Checked-out") # Status

    badge_number = today_visitors[row_index]["BadgeAssigned"]
    badges = get_sheet_data("Badges")
    badge_row = next((i for i, b in enumerate(badges) if b["BadgeNumber"] == badge_number), None)
    if badge_row is not None:
        update_sheet("Badges", "B", badge_row, "Available")
        update_sheet("Badges", "C", badge_row, "")

    return redirect("/checkin")

# Delivery logging
@app.route("/deliveries")
def deliveries_page():
    deliveries = get_sheet_data("Deliveries")
    return render_template("deliveries.html", deliveries=deliveries)

@app.route("/log_delivery", methods=["POST"])
def log_delivery():
    item = request.form["item"]
    employee = request.form["employee"]
    courier = request.form["courier"]
    location = request.form["location"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    url = f"{sheet_url('Deliveries')}:append?valueInputOption=RAW&key={API_KEY}"
    body = {"values": [[item, employee, courier, location, "Received", now, ""]]}
    requests.post(url, json=body)

    return redirect("/deliveries")

# --- Production-ready for Render ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
