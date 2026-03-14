from flask import Flask, render_template, request, redirect
import requests
from datetime import datetime
import os

app = Flask(__name__)

# --- Google Sheets setup ---
API_KEY = os.environ.get("GOOGLE_API_KEY")
SPREADSHEET_ID = os.environ.get("SHEET_ID")

if not API_KEY or not SPREADSHEET_ID:
    raise ValueError("GOOGLE_API_KEY and SHEET_ID must be set!")

def sheet_url(sheet_name):
    return f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{sheet_name}"

# --- Visitors Functions ---
def get_visitors():
    url = sheet_url("Visitors") + f"?key={API_KEY}"
    res = requests.get(url).json()
    if "values" in res:
        headers = res["values"][0]
        rows = res["values"][1:]
        return [dict(zip(headers, r)) for r in rows]
    return []

def append_visitor(name, host, badge):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    url = sheet_url("Visitors") + f":append?valueInputOption=RAW&key={API_KEY}"
    body = {"values": [[name, host, badge, "Checked-in", now, ""]]}
    requests.post(url, json=body)

def checkout_visitor(row_index):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    url_status = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/Visitors!D{row_index+2}?valueInputOption=RAW&key={API_KEY}"
    url_time = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/Visitors!F{row_index+2}?valueInputOption=RAW&key={API_KEY}"
    requests.put(url_status, json={"values": [["Checked-out"]]})
    requests.put(url_time, json={"values": [[now]]})

# --- Deliveries Functions ---
def get_deliveries():
    url = sheet_url("Deliveries") + f"?key={API_KEY}"
    res = requests.get(url).json()
    if "values" in res:
        headers = res["values"][0]
        rows = res["values"][1:]
        return [dict(zip(headers, r)) for r in rows]
    return []

def next_free_location(deliveries):
    used = [int(d["Location"]) for d in deliveries if d["Status"]=="Stored"]
    for i in range(1,21):
        if i not in used:
            return i
    return None

def log_delivery(employee, email, courier):
    deliveries = get_deliveries()
    location = next_free_location(deliveries)
    if not location:
        raise Exception("All delivery locations full!")
    parcel_id = f"P{int(datetime.now().timestamp())}"
    received_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    url = sheet_url("Deliveries") + f":append?valueInputOption=RAW&key={API_KEY}"
    body = {"values": [[parcel_id, employee, email, courier, location, "Stored", received_time, ""]]}
    requests.post(url, json=body)
    return parcel_id, location

def collect_delivery(row_index):
    collected_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    url_status = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/Deliveries!F{row_index+2}?valueInputOption=RAW&key={API_KEY}"
    url_time = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/Deliveries!H{row_index+2}?valueInputOption=RAW&key={API_KEY}"
    requests.put(url_status, json={"values":[["Collected"]]})
    requests.put(url_time, json={"values":[[collected_time]]})

# --- Routes ---
@app.route("/")
def home():
    return render_template("home.html")

# --- Visitor Routes ---
@app.route("/visitors")
def visitors_page():
    visitors = get_visitors()
    return render_template("visitors.html", visitors=visitors)

@app.route("/checkin", methods=["POST"])
def checkin_route():
    name = request.form["name"]
    host = request.form["host"]
    badge = request.form["badge"]
    append_visitor(name, host, badge)
    return redirect("/visitors")

@app.route("/checkout", methods=["POST"])
def checkout_route():
    row_index = int(request.form["row_index"])
    checkout_visitor(row_index)
    return redirect("/visitors")

# --- Deliveries Routes ---
@app.route("/deliveries")
def deliveries_page():
    deliveries = get_deliveries()
    return render_template("deliveries.html", deliveries=deliveries)

@app.route("/log_delivery", methods=["POST"])
def log_delivery_route():
    employee = request.form["employee"]
    email = request.form["email"]
    courier = request.form["courier"]
    log_delivery(employee, email, courier)
    return redirect("/deliveries")

@app.route("/collect_delivery", methods=["POST"])
def collect_delivery_route():
    row_index = int(request.form["row_index"])
    collect_delivery(row_index)
    return redirect("/deliveries")

# --- Run server ---
if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=True)
