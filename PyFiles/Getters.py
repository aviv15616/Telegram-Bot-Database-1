import sqlite3

from telegram import Update
from telegram.ext import CallbackContext

def fetch_name(account_type, account_id):
    # Establish connection to the database
    conn = sqlite3.connect('../Database/accounts.db')  # Change path if needed
    cursor = conn.cursor()

    # Write the SQL query to fetch the full_name based on account_type and account_id
    query = """
    SELECT full_name
    FROM accounts
    WHERE account_type = ? AND account_id = ?
    """

    # Execute the query
    cursor.execute(query, (account_type, account_id))

    # Fetch the result
    result = cursor.fetchone()

    # Close the database connection
    conn.close()

    # If result is None, return an empty string, else return the full_name
    if result:
        return result[0]  # Assuming full_name is the first column in the result
    else:
        print(f"Full name not found for account type {account_type} and account ID {account_id}")
        return ''  # Return an empty string if no result is found

def fetch_bank(account_id):
    # Connect to the database (replace 'our_database.db' with the actual database file)
    connection = sqlite3.connect('../Database/accounts.db')
    cursor = connection.cursor()

    # Query to fetch the bank_number by account_id
    query = "SELECT bank_number FROM accounts WHERE account_id = ?"
    cursor.execute(query, (account_id,))

    # Fetch the result (assuming account_id is unique)
    result = cursor.fetchone()

    # Close the connection
    connection.close()

    # Return the bank_number if found, otherwise return None
    if result:
        return result[0]
    else:
        return None
def fetch_logs():
    # Function to fetch logs from file, reading from bottom to top
    log_file_path = 'logs.txt'
    with open(log_file_path, 'r', encoding='windows-1255') as file:
        logs = file.readlines()
    # Return logs reversed so that the latest entries are first
    return [log.strip() for log in reversed(logs)]
def fetch_reason(account_type, account_id):
    # Connect to your database (replace with your connection details)
    conn = sqlite3.connect('../Database/accounts.db')
    cursor = conn.cursor()
    # Define the query to fetch the reason (this example assumes that the reason is stored in the database)
    # If the reason is a static string based on the account type (like in your logic), we can skip fetching it from DB
    query = '''
    SELECT reason 
    FROM accounts 
    WHERE account_type = ? AND account_id = ?
    '''
    # Execute the query with parameters
    cursor.execute(query, (account_type, account_id))
    # Fetch the result
    result = cursor.fetchone()
    # Close the connection
    conn.close()
    # If reason is found, return it. If not, return a default value or a static reason based on account_type
    if result:
        return result[0]  # Assuming the reason is stored in the 'reason' column
    else:
        # Return a default reason based on the account type if no reason is found in DB
        if account_type == 'M':
            return f'ללא סיבה'
        elif account_type == 'P':
            return f'ללא סיבה'
        elif account_type == 'B':
            return f'ללא סיבה'
        else:
            return f'ללא סיבה'
def get_account_balance(account_type, account_id):
    # Connect to your database and fetch the account balance
    # Assuming you have a function fetch_balance that queries the balance from your DB
    balance = fetch_balance(account_type, account_id)
    return balance


def fetch_commission(account_type, account_id):
    """
    Fetch the commission for the given account_type and account_id from the database.

    Args:
        account_type (str): The account type to search for.
        account_id (str): The account ID to search for.

    Returns:
        float: The commission value for the specified account, or 0 if not found.
    """
    # Path to your database file
    db_file = '../Database/accounts.db'  # Replace with your actual database file name

    # Connect to the SQLite database
    try:
        connection = sqlite3.connect(db_file)
        cursor = connection.cursor()

        # Query to fetch the commission
        query = """
        SELECT commission
        FROM accounts  -- Replace with your actual table name
        WHERE account_type = ? AND account_id = ?;
        """

        # Execute the query with parameters
        cursor.execute(query, (account_type, account_id))
        result = cursor.fetchone()

        # If a result is found, return the commission value, otherwise return 0
        if result:
            return result[0]  # Convert to float if necessary
        else:
            return 0.0
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return 0.0
    finally:
        # Ensure the database connection is closed
        if connection:
            connection.close()
def fetch_balance(account_type, account_id):
    # Connect to your database (replace with your connection details)
    conn = sqlite3.connect('../Database/accounts.db')
    cursor = conn.cursor()
    # Define the query to fetch the balance
    query = '''
    SELECT balance 
    FROM accounts 
    WHERE account_type = ? AND account_id = ?
    '''
    # Execute the query with parameters
    cursor.execute(query, (account_type, account_id))
    # Fetch the result
    result = cursor.fetchone()
    # Close the connection
    conn.close()
    # Return the balance if found, else return 0 or appropriate value
    if result:
        return result[0]
    return 0
def get_heb_acc(acc_type: str) -> str:
    if acc_type == 'M':
        return "חשבון בנק"
    elif acc_type == 'P':
        return "פייבוקס"
    else:
        return "ביט"
def get_nickname(user_id: int) -> str:
    """Fetch the nickname for the given userID from the database."""
    try:
        conn = sqlite3.connect('../Database/users.db')
        cursor = conn.cursor()
        # Fetch the nickname from the database
        cursor.execute("SELECT nickname FROM users WHERE userID = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]  # Return the nickname
        else:
            return "Unknown User"  # Return a default value if userID is not found
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return "Error fetching nickname"
async def ask_for_user_id(update: Update, context: CallbackContext):
    # Ensure we are working with a message
    if update.message:
        await update.message.reply_text('Please send the user ID to add.')
        context.user_data['state'] = 'ADDING_USER_ID'