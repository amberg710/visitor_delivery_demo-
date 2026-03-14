# Visitor & Delivery Hub

Modern **visitor management and reception operations dashboard** built with **Python Flask** and **Google Sheets API**.

This system allows reception teams to manage visitor check-ins, scheduled visits, badge allocation, package deliveries, and real-time analytics — all through a simple web interface.

Google Sheets is used as the backend database, making the system lightweight, easy to deploy, and simple to maintain.

---

# Overview

Visitor & Delivery Hub centralizes multiple reception workflows into one dashboard:

• Visitor check-in
• Scheduled visitor tracking
• Walk-in visitors
• Badge tracking
• Delivery management
• Operational analytics

The system provides **real-time operational insights** for reception staff and office administrators.

---

# Key Features

## Visitor Check-In

Reception staff can register visitors quickly by entering:

* Visitor name
* ID number
* Visit purpose
* Host
* Badge number

The system automatically:

* Validates badge availability
* Logs check-in time
* Detects **scheduled vs walk-in visitors**
* Stores all information in Google Sheets

---

## Expected Visitors

The system reads the **PrebookedVisitors sheet** and displays visitors expected today.

Each visitor appears with a **Pending status indicator**.

Reception can perform **one-click check-in** directly from the expected visitors list.

Once a visitor checks in, they automatically disappear from the pending list.

---

## Badge Dashboard

The badge dashboard shows a **live overview of badge usage**.

Each badge displays:

* Badge number
* Availability status
* Assigned visitor

Statuses include:

• Available
• In Use

### After-Hours Alerts

If badges are still checked out after **7:00 PM Monday–Friday**, the system displays an alert listing:

* Visitor name
* Badge number
* Host
* Check-in time

This helps reception ensure badges are returned before closing.

---

## Delivery Management

Reception can log incoming packages for employees.

Each delivery record includes:

* Parcel ID
* Item description
* Employee name
* Email
* Courier
* Storage location

Storage locations are assigned automatically.

When a package is collected, reception can mark it as **Collected**, and the system records the collection time.

---

## Analytics Dashboard

The analytics dashboard provides **operational insights into visitor activity**.

Metrics include:

* Visitors today
* Visitors currently inside
* Monthly visitor totals
* Badge utilization percentage
* Scheduled vs walk-in visitors
* Reception activity

### Charts Included

* Visitor trend analysis (daily / monthly / yearly)
* Purpose breakdown
* Scheduled vs walk-in comparison
* Receptionist activity

Charts are powered by **Chart.js**.

---

# Scheduled vs Walk-In Detection

When a visitor checks in, the system compares:

* Visitor name
* Host
* Visit date

with the **PrebookedVisitors sheet**.

If a match is found:

VisitType = Scheduled

Otherwise:

VisitType = Unscheduled

This enables accurate analytics on scheduled traffic vs walk-ins.

---

# Architecture

The application uses a simple architecture:

Browser
↓
Flask Web Application
↓
Google Sheets API
↓
Google Sheets (Database)

Using Google Sheets allows the system to operate **without a traditional database server**.

Benefits:

* Simple deployment
* Easy editing of data
* No database maintenance
* Accessible for non-technical staff

---

# Project Structure

```
project/
│
├── app.py
│
├── templates/
│   ├── home.html
│   ├── checkin.html
│   ├── visitors.html
│   ├── deliveries.html
│   ├── badges.html
│   └── analytics.html
│
├── static/
│   └── style.css
│
└── README.md
```

---

# Data Storage

The system uses three Google Sheets tabs.

## Visitors Sheet

Columns:

VisitorID
Name
IDNumber
Purpose
Host
BadgeNumber
Status
CheckInTime
CheckOutTime
Date
VisitType

---

## Deliveries Sheet

Columns:

ParcelID
Item
Employee
Email
Courier
Location
Status
ReceivedTime
CollectedTime

---

## PrebookedVisitors Sheet

Columns:

BookingID
Name
IDNumber
Purpose
Host
VisitDate
Notes

---

# Installation

## 1 Install dependencies

```
pip install flask google-api-python-client google-auth
```

---

## 2 Enable Google Sheets API

1. Go to Google Cloud Console
2. Create a project
3. Enable **Google Sheets API**
4. Create a **Service Account**
5. Download the service account JSON file

---

## 3 Configure environment variables

Example:

```
SHEET_ID=your_google_sheet_id
GOOGLE_SERVICE_ACCOUNT_JSON=your_service_account_json
```

---

## 4 Run the application

```
python app.py
```

The server will run on:

```
http://localhost:5000
```

---

# Deployment

This project can be deployed easily using:

* Render
* Railway
* Fly.io
* Heroku
* VPS servers

Because the system uses **Google Sheets instead of a database**, deployment is simple and requires minimal configuration.

---

# Security Considerations

The current version assumes usage within a **trusted internal network**.

Recommended improvements for production environments:

* User authentication
* Role-based permissions
* Audit logs
* HTTPS enforcement
* Visitor approval workflows

---

# Future Improvements

Potential future features include:

* QR code visitor check-in
* Visitor photo capture
* Email notifications for hosts
* Slack or Teams delivery alerts
* Badge expiration reminders
* Export analytics to CSV or PDF
* Multi-office support

---

# Use Cases

Visitor & Delivery Hub can be used for:

* Corporate offices
* Reception desks
* Co-working spaces
* Event venues
* University departments
* Security operations centers

---

# Technology Stack

Backend
Python
Flask

Frontend
HTML
CSS
JavaScript
Chart.js

Data Storage
Google Sheets API

---

# Author

This project demonstrates:

* Python backend development
* API integration
* operational dashboard design
* analytics visualization
* workflow automation

---

# License

MIT License
