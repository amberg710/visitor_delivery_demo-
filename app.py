from flask import Flask, render_template, request, redirect
from datetime import datetime

app = Flask(__name__)

deliveries = []

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/deliveries")
def deliveries_page():
    return render_template("deliveries.html", deliveries=deliveries)

@app.route("/log_delivery", methods=["POST"])
def log_delivery():
    item = request.form["item"]
    employee = request.form["employee"]
    courier = request.form["courier"]
    location = request.form["location"]

    deliveries.append({
        "Item": item,
        "Employee": employee,
        "Courier": courier,
        "Location": location,
        "Status": "Received",
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    return redirect("/deliveries")

if __name__ == "__main__":
    app.run()
