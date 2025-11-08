# Telegram Data Management Bot

This project is a **Telegram-based data management bot** that allows authorized users and admins to manage account records, view user lists, and perform automatic database backups.  
It was developed as a demonstration of structured bot design, database integration, and real-time interaction using the `python-telegram-bot` framework.

---

## 🚀 Features

- **User Authentication**
  - Restricts access using decorators for authorized users and admins only.
  - Supports dynamic user registration and deletion.
  
- **Account Management**
  - Add, update, or delete account entries (with types, balances, and limits).
  - Automatically updates daily and monthly counters.
  - Exports database tables to JSON for easy synchronization or backup.

- **Database Synchronization**
  - SQLite database used for persistent storage (`accounts.db` and `users.db`).
  - JSON export functionality keeps an updated local snapshot.
  - Integrated upload-to-drive module for cloud backup.

- **Scheduled Maintenance**
  - Daily and monthly reset functions for account activity fields.
  - Timestamp updates for each modified record.

---

## 🧠 Technical Stack

| Component | Description |
|------------|-------------|
| **Python 3.10+** | Core programming language |
| **python-telegram-bot** | Telegram API interaction |
| **SQLite3** | Local database engine |
| **JSON** | Export format for data backup |
| **AsyncIO** | Asynchronous handling of bot commands |

---

## 🗂️ Project Structure

```
project_root/
│
├── app/
│   ├── auth.py                 # Authorization decorators and access control
│   ├── drive_upload.py         # Upload and backup logic
│   ├── config.py               # Constants and protected user IDs
│   └── db_manager.py           # Core logic for accounts and users
│
├── data/
│   ├── accounts.db             # Account storage
│   ├── users.db                # User storage
│   ├── accounts.json           # Exported backup
│   └── logs/                   # Optional logging files
│
├── main.py                     # Entry point for bot execution
└── README.md                   # Project documentation
```

---

## 🧩 Example Functionalities

- **Add Account**
  ```python
  add_account_to_db("M", "12345", 500.0, "001", "10", 1, 5, 0.02, "Initial deposit", "John Doe")
  ```

- **Export to JSON**
  ```python
  export_db_to_json(DB_FILE, "../data/accounts.json", "accounts")
  ```

- **Delete User (via Telegram menu)**
  ```python
  await delete_user(update, context)
  ```

---

## 🔒 Security Note

All sensitive identifiers, business-related data, and credentials have been **fully removed** from this version.  
This repository is intended **solely for portfolio and educational demonstration**.

---

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/telegram-data-manager.git
   cd telegram-data-manager
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the bot:
   ```bash
   python main.py
   ```

---


## 👤 Author
Aviv Neeman - neemanaviv@gmail.com
