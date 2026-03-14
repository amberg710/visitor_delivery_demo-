from flask import Flask, request, redirect, render_template
import requests
from datetime import datetime
import os

app = Flask(__name__)

# --- Google Sheets API setup (from environment variables) ---
API_KEY = os.environ.get("GOOGLE_API_KEY")
SPREADSHEET_ID = os.environ.get("SHEET_ID")

if not API_KEY or not SPREADSHEET_ID:
    raise ValueError("GOOGLE_API_KEY and SHEET_ID must be set as environment variables!")

def sheet_url(sheet_name):
    return f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{sheet_name}"

# --- Read visitors ---
def get_visitors():
    url = sheet_url("Visitors") + f"?key={API_KEY}"
    res = requests.get(url).json()
    if "values" in res:
        headers = res["values"][0]
        rows = res["values"][1:]
        return [dict(zip(headers, r)) for r in rows]
    return []

# --- Append visitor ---
def append_visitor(name, host, badge):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    url = sheet_url("Visitors") + f":append?valueInputOption=RAW&key={API_KEY}"
    body = {"values": [[name, host, badge, "Checked-in", now, ""]]}
    requests.post(url, json=body)

# --- Check-out visitor ---
def checkout_visitor(row_index):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/Visitors!F{row_index+2}?valueInputOption=RAW&key={API_KEY}"
    body = {"values": [[now]]}
    requests.put(url, json=body)

# --- Append delivery ---
def append_delivery(item, employee, courier, location):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    url = sheet_url("Deliveries") + f":append?valueInputOption=RAW&key={API_KEY}"
    body = {"values": [[item, employee, courier, location, "Received", now, ""]]}
    requests.post(url, json=body)

# --- Mark delivery pickup ---
def pickup_delivery(row_index):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/Deliveries!G{row_index+2}?valueInputOption=RAW&key={API_KEY}"
    body = {"values": [[now]]}
    requests.put(url, json=body)

# --- Routes ---
@app.route("/")
def index():
    visitors = get_visitors()
    return render_template("index.html", visitors=visitors)

@app.route("/checkin", methods=["POST"])
def checkin():
    name = request.form["name"]
    host = request.form["host"]
    badge = request.form["badge"]
    append_visitor(name, host, badge)
    return redirect("/")

@app.route("/checkout", methods=["POST"])
def checkout():
    row_index = int(request.form["row_index"])
    checkout_visitor(row_index)
    return redirect("/")

@app.route("/deliver", methods=["POST"])
def deliver():
    item = request.form["item"]
    employee = request.form["employee"]
    courier = request.form["courier"]
    location = request.form["location"]
    append_delivery(item, employee, courier, location)
    return redirect("/")

@app.route("/pickup", methods=["POST"])
def pickup():
    row_index = int(request.form["row_index"])
    pickup_delivery(row_index)
    return redirect("/")

# --- Production-ready server for Render ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
