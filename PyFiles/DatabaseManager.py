import json
import sqlite3
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import logging

from PyFiles.Authorizer import isAdmin
from PyFiles.Cleaners.upload_to_drive import main as upload_to_drive_main
from PyFiles.config import PROTECTED_USER_IDS, DB_FILE

column_mapping1 = {
        'account_type': 'סוג חשבון',
        'account_id': 'מזהה חשבון',
        'balance': 'יתרה',
        'branch_number': 'מספר סניף',
        'bank_number': 'מספר בנק',
        'daily': 'העברות יומיות',
        'monthly': 'העברות חודשיות',
        'reason': 'סיבה',
        'full_name': 'שם מלא',
        'commission': 'עמלה',
        'date': 'תאריך העברה אחרונה',
    }
async def show_delete_user_menu(update: Update, context: CallbackContext) -> None:
    """Show the delete user menu with a list of users and the return to main menu button."""
    query = update.callback_query
    await query.answer()
    users = get_all_users_from_db()
    keyboard = []
    for user_id, nickname in users:
        button_text = f"{user_id} {nickname}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'delete_user_{user_id}')])
    keyboard.append([InlineKeyboardButton('חזור לתפריט הראשי', callback_data='return_to_main_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Select a user to delete:", reply_markup=reply_markup)
def export_db_to_json(db_file: str, json_file: str, table_name: str, column_mapping=None) -> None:
    """Export data from an SQL table to a JSON file with customizable column names."""
    if column_mapping is None:
        column_mapping = column_mapping1
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        # Get columns from the table
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]  # Extract column names
        # If no column mapping is provided, use default column names
        if column_mapping is None or not column_mapping:
            column_mapping = {col: col for col in columns}
        # Ensure that all columns in the column_mapping are present in the table
        for col in column_mapping.keys():
            if col not in columns:
                raise ValueError(f"Column '{col}' in column_mapping not found in table '{table_name}'")
        # Create a comma-separated string of columns
        columns_str = ', '.join(column_mapping.keys())
        # Fetch data from the specified columns
        cursor.execute(f"SELECT {columns_str} FROM {table_name}")
        rows = cursor.fetchall()
        # Map the data to the new column names
        data = []
        for row in rows:
            row_dict = {column_mapping[col]: val for col, val in zip(column_mapping.keys(), row)}
            data.append(row_dict)
        with open(json_file, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        conn.close()
        print(f"Data exported to {json_file}")
    except Exception as e:
        print(f"Error exporting data: {e}")
def insert_new_entry_to_db(userID: str, nickname: str, isAdmin: str) -> None:
    try:
        conn = sqlite3.connect('../Database/users.db')
        cursor = conn.cursor()
        if userID in PROTECTED_USER_IDS:
            isAdmin = '1'
        # Insert new information into the table
        cursor.execute('''
        INSERT OR REPLACE INTO users (userID, nickname, isAdmin)
        VALUES (?, ?, ?)
        ''', (userID, nickname, isAdmin))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Database error: {str(e)}")
    try:
        conn = sqlite3.connect('../Database/users.db')
        cursor = conn.cursor()
        if userID in PROTECTED_USER_IDS:
            isAdmin = '1'
        # Insert new information into the table
        cursor.execute('''
        INSERT OR REPLACE INTO users (userID, nickname, isAdmin)
        VALUES (?, ?, ?)
        ''', (userID, nickname, isAdmin))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Database error: {str(e)}")
def delete_account_from_db(account_type, account_id):

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM accounts WHERE account_type = ? AND account_id = ?', (account_type, account_id))
        conn.commit()
        # Check if the deletion was successful
        if cursor.rowcount > 0:
            deleted = True
        else:
            deleted = False
    # Export the database to JSON regardless of deletion success
    export_db_to_json(DB_FILE, '../Database/accounts.json', 'accounts', column_mapping1)
    upload_to_drive_main()
    return deleted
def get_accounts_from_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT account_type, account_id, balance, branch_number, bank_number, daily, monthly,commission,reason, full_name,date FROM accounts')
        return cursor.fetchall()
def add_account_to_db(account_type, account_id, balance, branch_number, bank_number, daily, monthly,commission, reason="ללא סיבה", full_name="ריק", date=None):
    print(
        f"Adding account: {account_type}, {account_id}, {balance}, {branch_number}, {bank_number}, {daily}, {monthly}, {commission}, {reason}, {full_name}, {date}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO accounts (account_type, account_id, balance, branch_number, bank_number, daily, monthly,commission, reason, full_name, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,?, ?)
        ''', (account_type, account_id, balance, branch_number, bank_number, daily, monthly,commission, reason, full_name, date))
        conn.commit()
    # Ensure the table name is provided as a string
    table_name = 'accounts'
    export_db_to_json(DB_FILE, '../Database/accounts.json', table_name, column_mapping1)
def get_all_users_from_db():
    """Fetch all users from the database."""
    conn = sqlite3.connect('../Database/users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT userID, nickname FROM users")
    users = cursor.fetchall()
    conn.close()
    return users
def initialize_db():

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_type TEXT NOT NULL,
            account_id TEXT NOT NULL,
            balance REAL,
            branch_number TEXT,
            bank_number TEXT,
            daily REAL,
            monthly REAL,
            commission REAL,
            reason TEXT "ללא סיבה",
            full_name TEXT,
            date TEXT,
            UNIQUE(account_type, account_id)
        )
        ''')
        conn.commit()
    with sqlite3.connect('../Database/users.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
        userID TEXT UNIQUE,
        nickname TEXT,
        isAdmin INTEGER DEFAULT 0
        )
        ''')
        conn.commit()
async def delete_user_by_userID(update: Update, context: CallbackContext, userID: int) -> None:
    try:
        # Connect to the database
        conn = sqlite3.connect('../Database/users.db')
        cursor = conn.cursor()
        # Check if the userID is in the protected list
        if str(userID) in PROTECTED_USER_IDS:
            await update.callback_query.message.reply_text("Can't delete this user ID.")
            return
        # Delete the user with the specified userID
        cursor.execute("DELETE FROM users WHERE userID = ?", (userID,))
        conn.commit()
        conn.close()
        # Check if any rows were deleted
        if cursor.rowcount > 0:
            await update.callback_query.message.reply_text(f"User with userID {userID} has been deleted.")
        else:
            await update.callback_query.message.reply_text(f"No user found with userID {userID}.")
        # Show the list of users again
        await show_delete_user_menu(update, context)
    except sqlite3.Error as e:
        await update.callback_query.message.reply_text(f"Database error: {e}")
def update_account_balance(database_path, account_type, account_id, new_balance):

    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    current_date = datetime.now().isoformat()
    try:
        # Base SQL query to update the balance and date
        update_query = """
        UPDATE accounts 
        SET balance = ?, date = ? 
        WHERE account_type = ? AND account_id = ?;
        """
        # Execute the query with the provided parameters
        cursor.execute(update_query, (new_balance, current_date, account_type, account_id))
        # Check if any row was updated
        if cursor.rowcount == 0:
            print(f"No account found with account_type '{account_type}' and account_id '{account_id}'")
        else:
            print(f"Balance for account {account_id} of type {account_type} updated to {new_balance}")
            # If account_type is 'M', increment daily and monthly counts
            if account_type == 'M':
                increment_query = """
                UPDATE accounts 
                SET daily = daily + 1, 
                    monthly = monthly + 1 
                WHERE account_type = ? AND account_id = ?;
                """
                cursor.execute(increment_query, (account_type, account_id))
                print(f"Daily and monthly counts for account {account_id} of type {account_type} incremented by 1")
        # Commit the changes
        conn.commit()
        # Export the updated table to JSON
        table_name = 'accounts'
        export_db_to_json(database_path, '../Database/accounts.json', table_name, column_mapping1)
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the database connection
        conn.close()
def reset_daily_credentials():
    print("Resetting daily credentials for all accounts...")
    accounts = get_accounts_from_db()
    if not accounts:
        print("No accounts found to update.")
    for account in accounts:
        account_type = account[0]
        account_id = account[1]
        update_credential(account_type, account_id, 'daily', 0)
    print("Daily credentials reset.")
def reset_monthly_credentials():
    print("Resetting monthly credentials for all accounts...")
    accounts = get_accounts_from_db()
    if not accounts:
        print("No accounts found to update.")
    for account in accounts:
        account_type = account[0]
        account_id = account[1]
        update_credential(account_type, account_id, 'monthly', 0)
    print("Monthly credentials reset.")
def update_credential(account_type, account_id, credential_type, new_value):
    connection = sqlite3.connect('../Database/accounts.db')  # Replace with your database connection
    cursor = connection.cursor()
    try:
        if credential_type == 'daily':
            cursor.execute("UPDATE accounts SET daily = ? WHERE account_type = ? AND account_id = ?",
                           (new_value, account_type, account_id))
        elif credential_type == 'monthly':
            cursor.execute("UPDATE accounts SET monthly = ? WHERE account_type = ? AND account_id = ?",
                           (new_value, account_type, account_id))
        connection.commit()
        # Update the JSON file after modifying the database

        table_name = 'accounts'
        export_db_to_json('../Database/accounts.db', 'Database/accounts.json', table_name, column_mapping1)
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        connection.close()



async def delete_user(update: Update, context: CallbackContext) -> None:
    """Handle the delete_user callback and show the list of users."""
    query = update.callback_query
    await query.answer()
    users = get_all_users_from_db()
    keyboard = []
    for user_id, nickname in users:
        if isAdmin(user_id):
            button_text = f"מנהל {user_id} {nickname}"
        else:
            button_text = f"סוכן {user_id} {nickname}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'delete_user_{user_id}')])
    keyboard.append([InlineKeyboardButton('return to main menu', callback_data='return_to_main_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="בחר סוכן למחיקה:", reply_markup=reply_markup)