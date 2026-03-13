from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = "demo-secret-key"

EXCEL_FILE = "visitors.xlsx"
BADGES = list(range(1,31))  # Badge pool 1-30

# Load today's sheet or create if not exists
try:
    visitors_df = pd.read_excel(EXCEL_FILE, sheet_name="Today")
except:
    visitors_df = pd.DataFrame(columns=[
        'Name','Host','Email','Expected','Type',
        'Badge','Status','CheckIn','CheckOut','Desk'
    ])
    visitors_df.to_excel(EXCEL_FILE, sheet_name="Today", index=False)

# ------------------ Helper Functions ------------------

def get_available_badges():
    used = visitors_df.loc[visitors_df['Status']=='Checked In','Badge'].dropna().tolist()
    return [b for b in BADGES if b not in used]

def send_email(host_email, visitor_name, subject="Visitor Checked In"):
    msg = MIMEText(f"{visitor_name} has checked in at reception.")
    msg['Subject'] = subject
    msg['From'] = "reception@fiserv.com"
    msg['To'] = host_email
    try:
        with smtplib.SMTP("smtp.example.com", 587) as server:
            server.starttls()
            server.login("your_email","password")
            server.send_message(msg)
    except:
        print(f"Demo mode: email not sent to {host_email}")

# ------------------ Routes ------------------

@app.route("/")
def index():
    available_badges = get_available_badges()
    checked_in = visitors_df[visitors_df['Status']=='Checked In']
    not_checked_in = visitors_df[visitors_df['Status']!='Checked In']['Name'].tolist()
    return render_template("index.html", visitors=not_checked_in,
                           badges=available_badges, checked_in=checked_in)

@app.route("/checkin", methods=['POST'])
def checkin():
    global visitors_df
    visitor_name = request.form['visitor_name']
    badge = int(request.form['badge'])
    desk = request.form.get('desk','A')
    idx = visitors_df[visitors_df['Name']==visitor_name].index
    if len(idx)==0:
        flash("Visitor not found!", "danger")
    else:
        i = idx[0]
        visitors_df.at[i,'Badge'] = badge
        visitors_df.at[i,'Status'] = "Checked In"
        visitors_df.at[i,'CheckIn'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        visitors_df.at[i,'Desk'] = desk
        send_email(visitors_df.at[i,'Email'], visitor_name)
        visitors_df.to_excel(EXCEL_FILE, sheet_name="Today", index=False)
        flash(f"{visitor_name} checked in with badge {badge}", "success")
    return redirect(url_for('index'))

@app.route("/checkout/<visitor_name>")
def checkout(visitor_name):
    global visitors_df
    idx = visitors_df[visitors_df['Name']==visitor_name].index
    if len(idx)==0:
        flash("Visitor not found!", "danger")
    else:
        i = idx[0]
        visitors_df.at[i,'Status'] = "Checked Out"
        visitors_df.at[i,'CheckOut'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        visitors_df.to_excel(EXCEL_FILE, sheet_name="Today", index=False)
        flash(f"{visitor_name} checked out. Badge {visitors_df.at[i,'Badge']} now free.", "success")
    return redirect(url_for('index'))

# Individual visitor add
@app.route("/add_visitor", methods=['GET','POST'])
def add_visitor():
    global visitors_df
    if request.method=='POST':
        name = request.form['name']
        host = request.form['host']
        email = request.form['email']
        expected = request.form['expected']
        type_ = request.form['type']
        new_row = pd.DataFrame([{
            'Name': name, 'Host': host, 'Email': email, 'Expected': expected,
            'Type': type_, 'Badge': None, 'Status': 'Not Checked In',
            'CheckIn': None, 'CheckOut': None, 'Desk': None
        }])
        visitors_df = pd.concat([visitors_df, new_row], ignore_index=True)
        visitors_df.to_excel(EXCEL_FILE, sheet_name="Today", index=False)
        flash(f"{name} added successfully!", "success")
        return redirect(url_for('add_visitor'))
    return render_template("add_visitor.html")

# Bulk visitor upload
@app.route("/bulk_upload", methods=['GET','POST'])
def bulk_upload():
    global visitors_df
    if request.method=='POST':
        file = request.files['file']
        new_visitors = pd.read_excel(file)
        new_visitors['Badge'] = None
        new_visitors['Status'] = 'Not Checked In'
        new_visitors['CheckIn'] = None
        new_visitors['CheckOut'] = None
        new_visitors['Desk'] = None
        visitors_df = pd.concat([visitors_df, new_visitors], ignore_index=True)
        visitors_df.to_excel(EXCEL_FILE, sheet_name="Today", index=False)
        flash("Bulk visitors uploaded successfully!", "success")
        return redirect(url_for('bulk_upload'))
    return render_template("bulk_upload.html")

# Deliveries module
@app.route("/deliveries", methods=['GET','POST'])
def deliveries():
    global visitors_df
    if request.method=='POST':
        employee = request.form['employee']
        email = request.form['email']
        courier = request.form['courier']
        parcel_id = request.form['parcel_id']
        location = request.form['location']
        new_delivery = pd.DataFrame([{
            'Employee': employee, 'Email': email, 'Courier': courier,
            'ParcelID': parcel_id, 'Location': location,
            'Status': 'Received', 'Received': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'PickedUp': None, 'Desk': 'A'
        }])
        try:
            deliveries_df = pd.read_excel(EXCEL_FILE, sheet_name="Deliveries")
        except:
            deliveries_df = pd.DataFrame(columns=new_delivery.columns)
        deliveries_df = pd.concat([deliveries_df, new_delivery], ignore_index=True)
        deliveries_df.to_excel(EXCEL_FILE, sheet_name="Deliveries", index=False)
        send_email(email, f"Parcel {parcel_id} received for {employee}", subject="Delivery Arrival")
        flash(f"Delivery for {employee} logged successfully!", "success")
        return redirect(url_for('deliveries'))
    return render_template("deliveries.html")

if __name__=="__main__":
    app.run(debug=True)
