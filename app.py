<!DOCTYPE html>
<html>
<head>
    <title>Delivery Logging</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
<div class="container">
    <h1>Deliveries</h1>

    <h2>Log New Delivery</h2>
    <form action="/log_delivery" method="POST">
        <input name="item" placeholder="Item" required>
        <input name="employee" placeholder="Employee" required>
        <input name="courier" placeholder="Courier" required>
        <input name="location" placeholder="Location" required>
        <button>Log Delivery</button>
    </form>

    <h2>All Deliveries</h2>
    <ul>
        {% for d in deliveries %}
        <li>{{ d["Item"] }} | {{ d["Employee"] }} | {{ d["Courier"] }} | {{ d["Location"] }} | Status: {{ d["Status"] }}</li>
        {% endfor %}
    </ul>

    <a href="/">Back to Home</a>
</div>
</body>
</html>
