# Hostel Management System

This project is a simple Flask application for managing hostel rooms and student assignments. It relies on a MySQL database.

## Setup Instructions

1. Install dependencies (preferably in a virtual environment):

```bash
pip install -r FlaskProject/requirements.txt
```

2. Create the database and tables locally. Update `FlaskProject/config.py` if your MySQL credentials differ. Then run:

```bash
python FlaskProject/models/database_backup.py
```

This script will create the **`hostel_management`** database (or the name specified in `config.py`) along with all required tables and a default admin user (`admin` / `admin123`). The application itself connects through `models/database.py`, which loads the same configuration values.

3. Start the application:

```bash
python FlaskProject/app.py
```

Then open `http://127.0.0.1:5000` in your browser.

When creating a new account via `/signup`, choose one of the available roles:
`Admin`, `Staff`, or `Warden`. These match the allowed values in the database.
