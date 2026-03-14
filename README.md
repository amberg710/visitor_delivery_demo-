Visitor & Delivery Hub

A modern visitor management and reception operations dashboard built with Python Flask and Google Sheets API.

This system allows reception teams to manage:

Visitor check-ins

Scheduled visits

Walk-in visitors

Badge allocation

Package deliveries

Live visitor analytics

The platform uses Google Sheets as a backend database, making it simple to deploy and operate without maintaining a full database server.

Overview

Visitor & Delivery Hub was designed as a lightweight front desk management system.

It centralizes multiple reception workflows into a single interface:

Visitor check-in

Expected visitor tracking

Badge management

Package deliveries

Operational analytics

The dashboard provides real-time insights into visitor activity and reception performance.

Key Features
Visitor Check-In

Reception staff can quickly register visitors by entering:

Name

ID number

Visit purpose

Host

Badge number

The system automatically:

Validates badge availability

Logs check-in time

Marks visitor as Scheduled or Unscheduled

Stores data in Google Sheets

Expected Visitors

The system checks the PrebookedVisitors sheet and shows:

Visitors expected today

Booking details

Host

Visit purpose

Visitors appear with a Pending status indicator.

Reception can perform one-click check-in from this list.

Once the visitor checks in, they automatically disappear from the pending list.

Badge Dashboard

Badge management includes:

Live badge availability

Badge assigned visitor name

Visual badge grid

Each badge shows:

Available

In Use

Assigned visitor

After-hours alerts

If badges remain checked out after 7 PM Monday–Friday, the system displays an alert showing:

Visitor name

Badge number

Host

Check-in time

This helps ensure badges are returned before the end of the day.

Delivery Management

Reception can log packages delivered to employees.

Delivery logging includes:

Parcel ID

Item description

Employee name

Email

Courier

Storage location

Packages are assigned to storage slots automatically.

Reception can mark deliveries as Collected, and the system logs the collection time.

Analytics Dashboard

The analytics page provides a business-style operational dashboard.

Key metrics

Visitors today

Visitors currently inside

Monthly visitor totals

Badge utilization percentage

Scheduled vs walk-in visitors

Reception activity trends

Data visualization

The system includes charts for:

Visitor trends (daily / monthly / yearly)

Purpose breakdown

Scheduled vs walk-in visitors

Receptionist activity

Charts are rendered using Chart.js.

Scheduled vs Walk-In Detection

When a visitor checks in, the system compares:

Visitor name

Host

Visit date

against the PrebookedVisitors sheet.

If a match exists for today:

VisitType = Scheduled

Otherwise:

VisitType = Unscheduled

This allows the analytics dashboard to track:

Expected visitors

Walk-in traffic

Architecture

The application follows a simple web architecture.

Browser
   |
   | HTTP
   v
Flask Application
   |
   | Google Sheets API
   v
Google Sheets Database

The system avoids a traditional database and instead uses Google Sheets as the data store.

Advantages:

Easy setup

No database maintenance

Accessible to non-technical staff

Real-time updates

Project Structure
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
Data Storage

The application uses three Google Sheets tabs.

Visitors
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
Deliveries
ParcelID
Item
Employee
Email
Courier
Location
Status
ReceivedTime
CollectedTime
PrebookedVisitors
BookingID
Name
IDNumber
Purpose
Host
VisitDate
Notes
Installation
1 Install dependencies
pip install flask google-api-python-client google-auth
2 Configure Google Sheets API

Create a Google Cloud Service Account and enable:

Google Sheets API

Download the service account JSON credentials.

3 Set environment variables

Example:

SHEET_ID=your_google_sheet_id
GOOGLE_SERVICE_ACCOUNT_JSON=your_service_account_json_string
4 Run the application
python app.py

The server will start on:

http://localhost:5000
Deployment

The app can be deployed easily using:

Render

Railway

Fly.io

Heroku

VPS servers

Because it uses Google Sheets instead of a database, deployment is very simple.

Security Considerations

The system currently assumes a trusted internal network.

Recommended improvements for production:

Authentication for reception users

Admin role permissions

Audit logging

HTTPS enforcement

Future Improvements

Possible enhancements include:

Visitor photo capture

QR code check-in

Email visitor notifications

Slack alerts for deliveries

Automatic badge expiry reminders

Visitor approval workflows

CSV / PDF export for analytics

Multi-location support

Use Cases

This system can be used for:

Office receptions

Corporate headquarters

Co-working spaces

Event venues

University departments

Security operations centers

Technology Stack

Backend

Python

Flask

Frontend

HTML

CSS

JavaScript

Chart.js

Data Layer

Google Sheets API

Author

Developed as a modern reception operations dashboard demonstrating:

Python backend development

API integration

dashboard analytics

operational workflow automation

License

MIT License
