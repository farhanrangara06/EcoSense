# EcoSense – Community Environmental Awareness & Action Platform

**Know Your Environment. Understand the Change. Take Action.**

EcoSense is a research-based community solution that helps residents across India see current environmental conditions, understand risks in plain language, track trends, report concerns, and hold authorities accountable.

---

## Features

- **Live Environmental Dashboard** – AQI, Temperature, Humidity with severity levels
- **Plain-Language Explanations** – Technical readings converted to simple advice
- **Trend Analysis** – 24h / 7-day / 30-day charts with Chart.js
- **Concern Reporting** – Citizens report smoke, garbage, pollution, etc.
- **Status Tracking** – Pending → Reviewed → Resolved workflow
- **Admin Dashboard** – Manage reports, areas, and environmental data
- **Demo Mode** – Presentation scenarios for CEP viva
- **Pan-India Coverage** – 90+ cities across all states & union territories with live Open-Meteo data
- **India Cities Page** – Live AQI grid for every monitored city with search & state filter

---

## Prerequisites

1. **Python 3.8+** – [Download Python](https://www.python.org/downloads/)
2. **MySQL 8.0+** – [Download MySQL](https://dev.mysql.com/downloads/installer/)

---

## Setup Instructions

### Step 1: Install Python

Download and install Python from https://www.python.org/downloads/

During installation, check **"Add Python to PATH"**.

Verify:
```
python --version
```

### Step 2: Install MySQL

Download MySQL Community Server from https://dev.mysql.com/downloads/installer/

During setup, set a root password (remember it!).

### Step 3: Create the Database

Open MySQL Command Line or MySQL Workbench and run:

```sql
CREATE DATABASE ecosense;
```

Or import the full schema:
```
mysql -u root -p < database/database.sql
```

### Step 4: Configure Database Connection

Edit `config.py` and set your MySQL password:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'YOUR_MYSQL_PASSWORD',  # <-- Change this
    'database': 'ecosense',
    'port': 3306,
}
```

### Step 5: Install Python Dependencies

Open terminal in the `EcoSense` folder:

```
cd EcoSense
pip install -r requirements.txt
```

### Step 6: Start the Application

```
python app.py
```

The server starts at: **http://127.0.0.1:5000**

Open this URL in your browser.

### Step 7: Default Admin Account

| Field    | Value                    |
|----------|--------------------------|
| Email    | admin@ecosense.in     |
| Password | admin123                 |

The database is auto-initialized with sample areas and an admin account on first run.

### Step 8: Run Demo Mode (for CEP Presentation)

1. Go to **Check Area** (Dashboard)
2. Scroll to **Demo Mode** panel
3. Click a scenario:
   - **Normal Conditions** – AQI 45 (Good)
   - **Pollution Spike** – AQI 187 (Poor)
   - **Severe Pollution** – AQI 250 (Hazardous)
   - **Hot Weather** – 39°C
   - **High Humidity** – 90%
4. Dashboard updates instantly with new severity and explanations

### Step 9: Run Data Collector (Optional)

To simulate live sensor data every 5 minutes:

```
python data_collector.py --loop
```

Run once without loop:
```
python data_collector.py
```

---

## CEP Demonstration Flow

1. **Citizen** opens EcoSense → selects Mira Road
2. Dashboard shows AQI 187 (Poor) with explanation
3. Citizen clicks **View Trends** → sees worsening air quality
4. Citizen clicks **Report a Concern** → submits smoke report
5. System creates **EW-001** with status **Pending**
6. **Admin** logs in → sees pending report
7. Admin marks **Reviewed** → adds note
8. Admin marks **Resolved** → adds resolution note
9. **Citizen** checks **My Reports** → sees **Resolved** status

This demonstrates: **Awareness → Understanding → Trend → Action → Accountability**

---

## Project Structure

```
EcoSense/
├── app.py              # Main Flask application
├── config.py           # Configuration settings
├── database.py         # Database helpers and seeding
├── utils.py            # Severity classification & trends
├── data_collector.py   # Simulated data collector
├── requirements.txt    # Python dependencies
├── database/
│   └── database.sql    # MySQL schema
├── templates/          # HTML pages
├── static/
│   ├── css/style.css
│   └── js/             # Dashboard, trends, reports
```

---

## API Endpoints

| Method | Endpoint                        | Description              |
|--------|---------------------------------|--------------------------|
| GET    | /api/areas                      | List all areas           |
| GET    | /api/areas/:id/latest           | Latest reading           |
| GET    | /api/areas/:id/history          | Historical readings      |
| POST   | /api/reports                    | Submit concern           |
| GET    | /api/my-reports                 | Citizen's reports        |
| GET    | /api/admin/reports              | All reports (admin)      |
| PUT    | /api/admin/reports/:id          | Update report status     |
| POST   | /api/demo-mode                  | Activate demo scenario   |

---

## Adding New Areas (Pan-India)

Admin can add areas from any Indian city via **Admin → Areas**, or directly in MySQL:

```sql
INSERT INTO areas (name, city, state, description)
VALUES ('Whitefield', 'Bangalore', 'Karnataka', 'IT corridor area');
```

No code changes needed — the system picks up new areas automatically.

---

## Security Notes

- Passwords are hashed with Werkzeug
- Session-based authentication
- Admin routes are protected
- SQL injection prevented with parameterized queries
- Users can only view their own reports

---

## License

Educational project for CEP (Community Engagement Project).
