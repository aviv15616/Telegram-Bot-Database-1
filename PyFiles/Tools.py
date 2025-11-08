import json
import logging
import os
import sqlite3

from telegram import *  # This imports all objects from the telegram module
from telegram.ext import *  # This imports all objects from the telegram.ext module

from PyFiles.DatabaseManager import get_accounts_from_db
from PyFiles.Cleaners.upload_to_drive import main as upload_to_drive_main
from PyFiles.Getters import fetch_bank

max_message_length_logs = 3000
max_message_length_accounts =1800


async def send_accounts_json_file(update: Update, context: CallbackContext, page_number: int) -> None:
    """Send the accounts JSON file to the user and paginate its content."""
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the absolute path of the current script
    json_file_path = os.path.join(script_dir, '..', 'Database', 'accounts.json')  # Build the absolute path

    chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id

    # Ensure the JSON file exists
    if not os.path.exists(json_file_path):
        await context.bot.send_message(chat_id=chat_id, text="The file is not available at the moment.")
        return

    try:
        # Load and format the JSON content
        with open(json_file_path, 'r', encoding='utf-8') as file:
            try:
                content = json.load(file)
            except json.JSONDecodeError:
                await context.bot.send_message(chat_id=chat_id, text="Error decoding JSON content.")
                return

        formatted_content = format_json_content(content)
        chunks = split_text(formatted_content, max_message_length_accounts)
        total_pages = len(chunks)
        if total_pages > 5:
            await context.bot.send_message(chat_id=chat_id, text="Message is too long, sending JSON file instead.")
            await send_accounts_json_file2(update, context)  # Send JSON file using new function
            return
        # Ensure the requested page number is within valid range
        if total_pages == 0:
            await context.bot.send_message(chat_id=chat_id, text="No content to display.")
            return
        if page_number < 0 or page_number >= total_pages:
            page_number = 0

        # Prepare buttons for pagination
        keyboard = []
        if page_number > 0:
            keyboard.append([InlineKeyboardButton("הקודם", callback_data=f'view_accounts_page_{page_number - 1}')])
        if page_number < total_pages - 1:
            keyboard.append([InlineKeyboardButton("הבא", callback_data=f'view_accounts_page_{page_number + 1}')])
        keyboard.append([InlineKeyboardButton("חזור לתפריט הראשי", callback_data='return_to_main_menu')])
        keyboard.append([InlineKeyboardButton("ייצא לJson", callback_data='export_json2')])
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send or edit the message with the paginated content
        if 'accounts_message_id' in context.user_data:
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=context.user_data['accounts_message_id'],
                    text=f'```\n{chunks[page_number]}\n```',
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            except Exception as e:
                sent_message = await context.bot.send_message(
                    chat_id=chat_id,
                    text=f'```\n{chunks[page_number]}\n```',
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                context.user_data['accounts_message_id'] = sent_message.message_id
        else:
            sent_message = await context.bot.send_message(
                chat_id=chat_id,
                text=f'```\n{chunks[page_number]}\n```',
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            context.user_data['accounts_message_id'] = sent_message.message_id

    except FileNotFoundError:
        await context.bot.send_message(chat_id=chat_id, text="The file does not exist.")
    except PermissionError:
        await context.bot.send_message(chat_id=chat_id, text="Permission denied when accessing the file.")
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"An unexpected error occurred: {e}")


async def send_accounts_json_file2(update: Update, context: CallbackContext) -> None:
    """Send the JSON file to the user."""
    json_file = '../Database/accounts.json'
    # Ensure the JSON file exists
    if not os.path.exists(json_file):
        if update.message:
            await update.message.reply_text("The file is not available at the moment.")
        return
    try:
        # Determine if the update is a message or callback query
        if update.message:
            chat_id = update.message.chat_id
            # Send the JSON file
            with open(json_file, 'rb') as file:
                await update.message.reply_document(document=file)
        elif update.callback_query:
            chat_id = update.callback_query.message.chat_id
            # Send the JSON file
            with open(json_file, 'rb') as file:
                await context.bot.send_document(chat_id=chat_id, document=file)
        else:
            if update.message:
                await update.message.reply_text("Unable to send file. Update type is not recognized.")
    except Exception as e:
        if update.message:
            await update.message.reply_text(f"Error sending file: {e}")


async def send_logs_json_file(update: Update, context: CallbackContext, page_number: int) -> None:
    """Send the logs JSON file to the user and paginate its content."""
    json_file_path = '../Database/logs.json'  # Update to the logs.json file path

    chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id

    # Ensure the JSON file exists
    if not os.path.exists(json_file_path):
        await context.bot.send_message(chat_id=chat_id, text="The file is not available at the moment.")
        return

    try:
        # Load and format the JSON content
        with open(json_file_path, 'r', encoding='utf-8') as file:
            try:
                content = json.load(file)
            except json.JSONDecodeError:
                await context.bot.send_message(chat_id=chat_id, text="Error decoding JSON content.")
                return

        logs = content.get("logs", [])  # Extract the 'logs' array from the JSON
        formatted_content = format_json_content(logs)  # Assuming format_json_content can handle the log array
        chunks = split_text(formatted_content, max_message_length_logs)
        total_pages = len(chunks)
        if total_pages > 5:
            await context.bot.send_message(chat_id=chat_id, text="Message is too long, sending JSON file instead.")
            await send_logs_json_file2(update, context)  # Send JSON file using new function
            return
        # Ensure the requested page number is within valid range
        if total_pages == 0:
            await context.bot.send_message(chat_id=chat_id, text="No content to display.")
            return
        if page_number < 0 or page_number >= total_pages:
            page_number = 0

        # Prepare buttons for pagination
        keyboard = []
        if page_number > 0:
            keyboard.append([InlineKeyboardButton("הקודם", callback_data=f'view_logs_page_{page_number - 1}')])
        if page_number < total_pages - 1:
            keyboard.append([InlineKeyboardButton("הבא", callback_data=f'view_logs_page_{page_number + 1}')])
        keyboard.append([InlineKeyboardButton("חזור לתפריט הראשי", callback_data='return_to_main_menu')])
        keyboard.append([InlineKeyboardButton("ייצא לJson", callback_data='export_json2')])
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send or edit the message with the paginated content
        if 'logs_message_id' in context.user_data:
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=context.user_data['logs_message_id'],
                    text=f'```\n{chunks[page_number]}\n```',
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            except Exception as e:
                sent_message = await context.bot.send_message(
                    chat_id=chat_id,
                    text=f'```\n{chunks[page_number]}\n```',
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                context.user_data['logs_message_id'] = sent_message.message_id
        else:
            sent_message = await context.bot.send_message(
                chat_id=chat_id,
                text=f'```\n{chunks[page_number]}\n```',
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            context.user_data['logs_message_id'] = sent_message.message_id

    except FileNotFoundError:
        await context.bot.send_message(chat_id=chat_id, text="The file does not exist.")
    except PermissionError:
        await context.bot.send_message(chat_id=chat_id, text="Permission denied when accessing the file.")
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"An unexpected error occurred: {e}")

async def send_logs_json_file2(update: Update, context: CallbackContext) -> None:
    """Send the JSON file to the user."""
    json_file_path = '../Database/logs.json'
    # Determine the chat_id based on the update type
    if update.message:
        chat_id = update.message.chat_id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat_id
    else:
        # If neither message nor callback_query is present, exit the function
        print("Update does not contain message or callback_query.")
        return
    # Ensure the JSON file exists
    if not os.path.exists(json_file_path):
        if update.message:
            await update.message.reply_text("The file is not available at the moment.")
        elif update.callback_query:
            await context.bot.send_message(chat_id=chat_id, text="The file is not available at the moment.")
        return
    try:
        # Send the JSON file
        with open(json_file_path, 'rb') as file:
            if update.message:
                await update.message.reply_document(document=file)
            elif update.callback_query:
                await context.bot.send_document(chat_id=chat_id, document=file)
    except Exception as e:
        if update.message:
            await update.message.reply_text(f"Error sending file: {e}")
        elif update.callback_query:
            await context.bot.send_message(chat_id=chat_id, text=f"Error sending file: {e}")


def split_text(formatted_content: str, max_message_length: int = 4096) -> list:
    """Split text into chunks while preserving logical blocks based on braces or line length."""
    lines = formatted_content.splitlines()
    chunks = []
    current_chunk = ""
    current_block = ""
    open_braces = 0  # Tracks nested block levels

    for line in lines:
        open_braces += line.count("{") - line.count("}")
        current_block += line + "\n"

        # If block is finished and fits within max_message_length, add it to current chunk
        if open_braces == 0:
            if len(current_chunk) + len(current_block) > max_message_length:
                # If the current block is too long, start a new chunk
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = current_block
            else:
                current_chunk += current_block

            current_block = ""  # Reset the current block after processing

    # Final check for remaining content
    if current_block.strip():
        if len(current_chunk) + len(current_block) > max_message_length:
            # If current chunk is too long, split the current block
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            chunks.append(current_block.strip())
        else:
            current_chunk += current_block

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def format_json_content(content):
    """Format the JSON content for sending as a message."""
    return json.dumps(content, indent=4, ensure_ascii=False)


def delete_json_file(file_path: str) -> None:
    """Empty the contents of a JSON file, setting it to an empty list."""
    try:
        with open(file_path, 'w') as file:
            json.dump({'logs': []}, file, indent=4)
        print(f"File '{file_path}' has been emptied.")
        upload_to_drive_main()
    except Exception as e:
        print(f"Error emptying file: {e}")
def delete_db_file(db_path: str) -> None:
    """
    Empties all tables in a SQLite database.

    :param db_path: Path to the SQLite database file.
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Fetch all table names in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Delete data from all tables
        for table in tables:
            table_name = table[0]
            cursor.execute(f"DELETE FROM {table_name};")
            print(f"Emptied table: {table_name}")

        # Commit changes and close the connection
        conn.commit()
        conn.close()

        print(f"Database '{db_path}' has been emptied.")
        upload_to_drive_main()  # Call additional logic here
    except Exception as e:
        print(f"Error emptying database: {e}")
def delete_all_accounts(db_path: str, json_path: str) -> None:
    """
    Empties all tables in the accounts database and sets the accounts JSON file to an empty list.

    :param db_path: Path to the SQLite database file.
    :param json_path: Path to the accounts JSON file.
    """
    try:
        # Step 1: Empty the database
        print(f"Starting to empty database at: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Fetch all table names in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Delete data from all tables
        for table in tables:
            table_name = table[0]
            cursor.execute(f"DELETE FROM {table_name};")
            print(f"Emptied table: {table_name}")

        # Commit changes and close the connection
        conn.commit()
        conn.close()
        print(f"Database '{db_path}' has been emptied.")

        # Step 2: Empty the JSON file
        print(f"Starting to empty JSON file at: {json_path}")
        with open(json_path, 'w') as file:
            json.dump({'logs': []}, file, indent=4)
        print(f"File '{json_path}' has been emptied.")

        # Call the upload function after JSON file cleanup
        upload_to_drive_main()

    except Exception as e:
        print(f"Error occurred during cleanup: {e}")

async def transfer(update: Update, context: CallbackContext) -> None:
    logging.info(f"Context data before transfer: {context.user_data}")
    # Ensure amount and account type are provided
    if 'amount' not in context.user_data or 'account_type' not in context.user_data:
        await update.message.reply_text('🔄 Make sure you have entered both the amount and account type.')
        return
    try:
        amount = float(context.user_data['amount'])
        if not (0 <= amount <= 10000):
            raise ValueError
    except ValueError:
        await update.message.reply_text('🔢 מספרים בין 0 ל10000 בלבד!')
        return
    account_type = context.user_data['account_type']
    # Fetch and shuffle accounts
    accounts = get_accounts_from_db()
    sorted_accounts = sort_accounts(accounts)
    print(f"Sorted Accounts: {sorted_accounts}")
    # Try to find a suitable account to transfer to
    for account in sorted_accounts:
        print(f"Account Tuple: {account}")
        if account[0] == account_type and can_receive_amount(account, amount, account_type):
            account_type, account_id, balance, branch_number, bank_number, daily, monthly, commission, reason, full_name, date = account
            for value in account:
                print(f"Value: {value}")
            # Create the message with confirmation
            if account_type == 'M':
                message = (f"העברה על סך {amount:.2f} \n\n"
                           f"*פרטי חשבון:*\n"
                           f"סוג: {account_type}\n"
                           f"שם מלא: {full_name}\n"
                           f"מספר חשבון בנק: {account_id}\n"
                           f"מספר סניף: {branch_number}\n"
                           f"מספר בנק: {bank_number}\n"
                           f"יתרה נוכחית: {balance:.2f}\n"
                           f"יתרה חדשה: {balance - amount:.2f}")
            elif account_type in ['P']:
                message = (f"העברה על סך {amount:.2f} \n\n"
                           f"*פרטי חשבון:*\n"
                           f"סוג: {account_type}\n"
                           f"מספר טלפון: {account_id}\n"
                           f"יתרה נוכחית: {balance:.2f}\n"
                           f"יתרה חדשה: {balance - amount:.2f}")
            elif account_type in ['B']:
                message = (f"העברה על סך {amount:.2f} \n\n"
                           f"*פרטי חשבון:*\n"
                           f"סוג: {account_type}\n"
                           f"מספר טלפון: {account_id}\n"
                           f"סיבה: {reason}\n"
                           f"יתרה נוכחית: {balance:.2f}\n"
                           f"יתרה חדשה: {balance - amount:.2f}")
            # Create the confirmation and cancellation buttons
            keyboard = [
                [InlineKeyboardButton("אשר", callback_data=f'confirm_transfer_{account_type}_{account_id}_{amount}')],
                [InlineKeyboardButton("בטל", callback_data='cancel_transfer')],
                [InlineKeyboardButton("חזור לתפריט הראשי", callback_data='return_to_main_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
            context.user_data['transfer_data'] = {
                'account_type': account_type,
                'account_id': account_id,
                'amount': amount,
                'balance': balance
            }
            return
    # No suitable account found, send a message and the return to main menu button
    keyboard = [
        [InlineKeyboardButton("בצע עוד העברה", callback_data='transfer')],
        [InlineKeyboardButton("חזור לתפריט הראשי", callback_data='return_to_main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('לא נמצא חשבון להעביר אליו את הכמות הנבחרת.', reply_markup=reply_markup)


async def transfer_same(update: Update, context: CallbackContext) -> None:
    # Ensure amount and account type are provided
    if 'amount' not in context.user_data or 'account_type' not in context.user_data or 'account_id' not in context.user_data:
        await update.message.reply_text('🔄 Make sure you have entered both the amount and account type.')
        return
    try:
        amount = float(context.user_data['amount'])
        if not (0 <= amount <= 10000):
            raise ValueError
    except ValueError:
        await update.message.reply_text('🔢 מספרים בין 0 ל10000 בלבד!')
        return
    account_type = context.user_data['account_type']
    account_id = context.user_data['account_id']
    # Fetch and shuffle accounts
    accounts = get_accounts_from_db()
    sorted_accounts = sort_accounts(accounts)
    # Try to find a suitable account to transfer to
    for account in sorted_accounts:
        if account[0] == account_type and account[1] == account_id and can_receive_amount(account, amount,
                                                                                          account_type):
            account_type, account_id, balance, branch_number, bank_number, daily, monthly, commission, reason, full_name, date = account
            # Create the message with confirmation
            if account_type == 'M':
                message = (f"העברה על סך {amount:.2f} \n\n"
                           f"*פרטי חשבון:*\n"
                           f"סוג: {account_type}\n"
                           f"שם מלא: {full_name}\n"
                           f"מספר חשבון בנק: {account_id}\n"
                           f"מספר סניף: {branch_number}\n"
                           f"מספר בנק: {bank_number}\n"
                           f"יתרה נוכחית: {balance:.2f}\n"
                           f"יתרה חדשה: {balance - amount:.2f}")
            elif account_type in ['P']:
                message = (f"העברה על סך {amount:.2f} \n\n"
                           f"*פרטי חשבון:*\n"
                           f"סוג: {account_type}\n"
                           f"מספר טלפון: {account_id}\n"
                           f"יתרה נוכחית: {balance:.2f}\n"
                           f"יתרה חדשה: {balance - amount:.2f}")
            elif account_type in ['B']:
                message = (f"העברה על סך {amount:.2f} \n\n"
                           f"*פרטי חשבון:*\n"
                           f"סוג: {account_type}\n"
                           f"מספר טלפון: {account_id}\n"
                           f"סיבה: {reason}\n"
                           f"יתרה נוכחית: {balance:.2f}\n"
                           f"יתרה חדשה: {balance - amount:.2f}")
            # Create the confirmation and cancellation buttons
            keyboard = [
                [InlineKeyboardButton("אשר", callback_data=f'confirm_transfer_{account_type}_{account_id}_{amount}')],
                [InlineKeyboardButton("בטל", callback_data='cancel_transfer')],
                [InlineKeyboardButton("חזור לתפריט הראשי", callback_data='return_to_main_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
            context.user_data['transfer_data'] = {
                'account_type': account_type,
                'account_id': account_id,
                'amount': amount,
                'balance': balance
            }
            return
    # No suitable account found, send a message and the return to main menu button
    keyboard = [
        [InlineKeyboardButton("בצע עוד העברה", callback_data='transfer')],
        [InlineKeyboardButton("חזור לתפריט הראשי", callback_data='return_to_main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('לא נמצא חשבון להעביר אליו את הכמות הנבחרת.', reply_markup=reply_markup)


def can_receive_amount(account, amount_to_receive, type):
    print("Account data:", account)  # Debugging line
    account_type, account_id, balance, branch_number, bank_number, daily, monthly, commission, reason, full_name, date = account
    # Check if the amount to receive is greater than the current balance
    if amount_to_receive > balance:
        return False
    if account_type == 'M' and fetch_bank(account_id) == '9' and amount_to_receive > 3499:
        return False
    if account_type != type:
        return False
    # Check if the account is of type M
    if account_type == 'M':
        # Check daily and monthly constraints
        if daily == 2:
            return False
        if monthly == 10:
            return False
    return True


# Assuming you have a function to get the nickname based on user_id
def exists_in_accounts(account_type, account_id):
    conn = sqlite3.connect('../Database/accounts.db')
    cursor = conn.cursor()
    try:
        # Query to check if the account exists
        query = """
        SELECT COUNT(*) FROM accounts
        WHERE account_type = ? AND account_id = ?
        """
        cursor.execute(query, (account_type, account_id))
        count = cursor.fetchone()[0]
        return count > 0
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()


def sort_accounts(accounts):
    """Sort accounts by date in ascending order, treating NULL as the lowest value."""
    # Use sorted with a custom key function to handle None as the lowest value
    return sorted(accounts, key=lambda account: (account[10] is None, account[10]))
