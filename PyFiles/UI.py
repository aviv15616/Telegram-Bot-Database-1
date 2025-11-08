import json
import logging
import math
import os
from datetime import datetime

from telegram import *  # This imports all objects from the telegram module
from telegram.ext import *  # This imports all objects from the telegram.ext module

from PyFiles.Authorizer import isauthorized, isAdmin
from PyFiles.Cleaners.upload_to_drive import main as upload_to_drive_main, backup_data_to_new_folder
from PyFiles.DatabaseManager import delete_account_from_db, insert_new_entry_to_db, add_account_to_db, \
    update_account_balance, delete_user, delete_user_by_userID, get_accounts_from_db
from PyFiles.Getters import get_account_balance, get_heb_acc, ask_for_user_id, get_nickname, \
    fetch_commission, fetch_name
from PyFiles.Google import add_sheet_row
from PyFiles.Tools import send_logs_json_file, transfer_same, transfer, delete_json_file, send_logs_json_file2, \
    send_accounts_json_file2, \
    send_accounts_json_file, delete_db_file, delete_all_accounts
from PyFiles.config import ADMIN_ID, SECOND_ADMIN_ID, ITEMS_PER_PAGE


def log_action(action: str, user_id: str) -> None:
    LOG_FILE_PATH = '../Database/logs.json'

    """Log an action to the JSON file with new entries coming at the top."""

    # Create the log entry with timestamp, user info, and the action
    log_entry = {
        'זמן:': datetime.now().isoformat(),
        'משתמש': get_nickname(int(user_id)),  # Get nickname based on user ID
        'פעולה': action
    }

    # Ensure the log file exists and create it if not
    if not os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, 'w', encoding='utf-8') as file:
            json.dump({'logs': []}, file, ensure_ascii=False, indent=4)  # Initialize with empty log list

    # Read existing logs
    with open(LOG_FILE_PATH, 'r', encoding='utf-8') as file:
        logs_data = json.load(file)

    # Ensure the 'logs' key exists
    if 'logs' not in logs_data:
        logs_data['logs'] = []

    # Prepend the new log entry (so the most recent log is at the top)
    logs_data['logs'].insert(0, log_entry)

    # Write the updated logs back to the file, ensuring it's human-readable
    with open(LOG_FILE_PATH, 'w', encoding='utf-8') as file:
        json.dump(logs_data, file, ensure_ascii=False, indent=4)

    # Trigger the file upload (assuming this function handles syncing the logs)
    upload_to_drive_main()
    print("Log entry added successfully and uploaded.")


async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if isauthorized(user_id):
        # Determine the chat ID to use for sending messages
        if update.message:
            chat_id = update.message.chat_id
        elif update.callback_query:
            chat_id = update.callback_query.message.chat_id
        else:
            # Log or handle the error as needed
            return
        # Create the keyboard based on the user ID
        if isAdmin(user_id):
            keyboard = [
                [InlineKeyboardButton("הוסף/ ערוך חשבון", callback_data='add_account')],
                [InlineKeyboardButton("מחק חשבון", callback_data='delete_account')],
                [InlineKeyboardButton("רשימת חשבונות", callback_data='view_accounts')],
                [InlineKeyboardButton("מחק רשימת חשבונות", callback_data='delete_all_accounts')],
                [InlineKeyboardButton("העברה", callback_data='transfer')],
                [InlineKeyboardButton("קוד משיכה", callback_data='withdraw')],
                [InlineKeyboardButton("צפה בפעולות", callback_data='view_logs')],
                [InlineKeyboardButton("מחק פעולות", callback_data='delete_logs')],
                [InlineKeyboardButton("הוסף סוכן", callback_data='add_new_entry')],
                [InlineKeyboardButton("מחק סוכן", callback_data='delete_user')],
                [InlineKeyboardButton("גבה נתונים", callback_data='backup')],
                [InlineKeyboardButton("חזור לתפריט הראשי", callback_data='return_to_main_menu')]
            ]
            text = 'אה יא תותח 👋\n\nבחר אופציה מהתפריט:'
        else:
            keyboard = [
                [InlineKeyboardButton("העברה", callback_data='transfer')],
                [InlineKeyboardButton("קוד משיכה", callback_data='withdraw')],
                [InlineKeyboardButton("חזור לתפריט הראשי", callback_data='return_to_main_menu')]
            ]
            text = 'אה יא תותח 👋\n\nבחר אופציה מהתפריט:'
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text('🚫 אין גישה.')
        return





async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    if not isinstance(query, CallbackQuery):
        logging.error("Update does not contain a CallbackQuery")
        return
    await query.answer()  # Acknowledge the callback
    user_id = query.from_user.id
    data = query.data
    logging.info(f"Callback data received: {data}")
    try:
        if isAdmin(user_id):
            if data == 'add_new_entry':
                await query.message.reply_text('user ID:')
                context.user_data['step'] = 'new_entry_step1'
            elif data == 'confirm_withdraw':
                client = context.user_data['client']
                website = context.user_data['website']
                amount = context.user_data['amount']
                delivery_man = context.user_data['delivery_man']
                add_sheet_row(amount, user_id, client, website, delivery_man, "")
                log_action(f"משיכה בסך {amount} תועדה בהצלחה, שליח: {delivery_man} ", str(user_id))
                print(f"משיכה בסך {amount} תועדה בהצלחה")

                # Create the menu buttons
                keyboard = [
                    [InlineKeyboardButton("חזור לתפריט הראשי", callback_data='return_to_main_menu')],
                    [InlineKeyboardButton("בצע עוד משיכה", callback_data='withdraw')]
                ]

                # Send the message with the buttons
                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(chat_id=user_id, text=f"משיכה בסך {amount} תועדה בהצלחה",
                                               reply_markup=reply_markup)

            elif data == 'edit_users':
                await show_user_management_menu(update, context)
            elif data == 'add_user':
                await ask_for_user_id(update, context)
            elif data == 'delete_user':
                await delete_user(update, context)
            elif data.startswith('delete_user_'):
                user_id = data.split('_')[2]
                await delete_user_by_userID(update, context, user_id)
            elif data.startswith('view_logs_page_'):
                page_number = int(data.split("_")[3])
                await send_logs_json_file(update, context, page_number)
            elif data.startswith('view_accounts_page_'):
                page_number = int(data.split("_")[3])
                await send_accounts_json_file(update, context, page_number)
            elif data.startswith("view_page_"):
                page_number = int(data.split("_")[2])
                await view_accounts(update, context, page_number)
            elif data.startswith("page_"):
                parts = data.split("_")
                action = parts[1]
                page = int(parts[2])
                reply_markup = build_account_buttons(action, page)
                await query.edit_message_reply_markup(reply_markup=reply_markup)
            elif data == 'transfer':
                context.user_data['move'] = 't'
                context.user_data['step'] = 'client_name'
                await query.message.reply_text('הכנס שם לקוח:')
            elif data == 'withdraw':
                context.user_data['move'] = 'w'
                context.user_data['step'] = 'client_name'
                await query.message.reply_text('הכנס שם לקוח:')

            elif data == 'transfer_same_acc':
                context.user_data['step'] = 'amount_same_acc'
                await query.message.reply_text('הכנס כמות להעברה בין 0 ל10000:')
            elif data.startswith('confirm_transfer_'):
                parts = data.split('_')
                account_type = parts[2]
                account_id = parts[3]
                context.user_data['account_id'] = account_id
                amount = float(parts[4])
                # Retrieve the transfer data from user_data
                transfer_data = context.user_data.get('transfer_data', {})
                balance = transfer_data.get('balance', 0)
                # Calculate the new balance
                new_balance = balance - amount
                update_account_balance('../Database/accounts.db', account_type, account_id, new_balance)
                # Log the action
                user_id = update.effective_user.id
                context.user_data['selected_account_id'] = account_id
                context.user_data['selected_account_type'] = account_type
                client_name = context.user_data['client']
                website = context.user_data['website']
                if account_type == 'M':
                    full_name = fetch_name(account_type, account_id)
                else:
                    full_name = ''
                delivery_man = ''
                commission = fetch_commission(account_type, account_id)
                add_sheet_row(amount, user_id, client_name, website, delivery_man, full_name, commission, account_type,
                              account_id)
                if account_type == 'M':
                    log_action(f"העביר {amount} לחשבון {account_id} מסוג : חשבון בנק עם יתרה חדשה של {new_balance}",
                               str(user_id))
                elif account_type == 'P':
                    log_action(f"העביר {amount} לחשבון {account_id} מסוג: פייבוקס עם יתרה חדשה של {new_balance}",
                               str(user_id))
                elif account_type == 'B':
                    log_action(f"העביר {amount} לחשבון {account_id} מסוג: ביט עם יתרה חדשה של {new_balance}",
                               str(user_id))
                # Prepare the keyboard for further options
                keyboard = [
                    [InlineKeyboardButton("בצע עוד העברה", callback_data='transfer')],
                    [InlineKeyboardButton("בצע עוד העברה לאותו החשבון", callback_data='transfer_same_acc')],
                    [InlineKeyboardButton("חזור לתפריט הראשי", callback_data='return_to_main_menu')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                # Get the callback query object
                query = update.callback_query
                # Send a confirmation message and then the keyboard for further actions
                if query:
                    await query.message.reply_text(
                        f'ההעברה של {amount:.2f} ל-חשבון: {account_id:}  מסוג: {account_type} בוצעה בהצלחה! עם יתרה חדשה של:  {new_balance:.2f}',
                        reply_markup=reply_markup)
                else:
                    # Handle case where there's no callback_query, log an error
                    logging.error("No callback_query found in update")
            elif data == 'cancel_transfer':
                await query.message.reply_text('ההעברה בוטלה.')
            elif data == 'cancel_withdraw':
                await query.message.reply_text('המשיכה בוטלה.')
            elif data.startswith('remove_'):
                _, account_type, account_id = data.split('_')
                balance = get_account_balance(account_type, account_id)
                delete_account_from_db(account_type, account_id)
                await query.message.reply_text(f'✅ חשבון {account_id} מסוג {account_type} הוסר.')
                await query.message.edit_text('הרשימה המעודכנת:', reply_markup=build_account_buttons('remove'))
                log_action(f' מחק את חשבון {account_id} מסוג:{get_heb_acc(account_type)} עם יתרה של: {balance} ',
                           str(user_id))
            elif data.startswith('view_logs'):
                await send_logs_json_file(update, context, page_number=0, )
            elif data == 'add_account':
                keyboard = [
                    [InlineKeyboardButton("A", callback_data='B')],
                    [InlineKeyboardButton("B", callback_data='P')],
                    [InlineKeyboardButton("Bank (M)", callback_data='M')],
                    [InlineKeyboardButton("חזור לתפריט הראשי", callback_data='return_to_main_menu')]
                ]
                await query.message.edit_text('בחר סוג חשבון:', reply_markup=InlineKeyboardMarkup(keyboard))
                context.user_data['step'] = 'account_type'
            elif data in ['B', 'P', 'M']:
                context.user_data['account_type'] = data
                if data in ['B', 'P']:
                    await query.message.reply_text('הכנס מספר טלפון:')
                    context.user_data['step'] = 'account_id_b_p_m'
                elif data == 'M':
                    await query.message.reply_text('הכנס מספר חשבון:')
                    context.user_data['step'] = 'account_id_b_p_m'
            elif data == 'delete_logs':
                keyboard = [
                    [InlineKeyboardButton("אשר מחיקת דוח פעולות שוטף", callback_data='confirm_delete_logs')],
                    [InlineKeyboardButton("חזרה לתפריט ראשי", callback_data='return_to_main_menu')]
                ]
                await query.message.reply_text('האם אתה בטוח שברצונך למחוק את כל הפעולות?',
                                               reply_markup=InlineKeyboardMarkup(keyboard))
            elif data == 'delete_all_accounts':
                keyboard = [
                    [InlineKeyboardButton("אשר מחיקת כל החשבונות:", callback_data='confirm_delete_all_accounts')],
                    [InlineKeyboardButton("חזרה לתפריט ראשי", callback_data='return_to_main_menu')]
                ]
                await query.message.reply_text('האם אתה בטוח שברצונך למחוק את כל החשבונות?',reply_markup=InlineKeyboardMarkup(keyboard))
            elif data == 'confirm_delete_logs':
                delete_json_file('../Database/logs.json')
                await query.message.reply_text('🗑️ היומנים נמחקו בהצלחה.')
            elif data == 'confirm_delete_all_accounts':
                delete_all_accounts('../Database/accounts.db','../Database/accounts.json')
                await query.message.reply_text('🗑️ החשבונות נמחקו בהצלחה.')
            elif data == 'edit_account':
                pass
            elif data == 'delete_account':
                await query.message.reply_text('סוג חשבון (B/P/M):')
                context.user_data['step'] = 'deletion'
            elif data == 'view_accounts':
                await send_accounts_json_file(update, context, 0)
            elif data == 'export_json':
                await send_accounts_json_file2(update, context)
            elif data == 'export_json2':
                await send_logs_json_file2(update, context)
            elif data == 'backup':
                backup_data_to_new_folder()
            elif data == 'return_to_main_menu':
                await start(update, context)
            else:
                await query.answer(f"Selected {data}")
        elif isauthorized(user_id):
            if data == 'return_to_main_menu':
                await start(update, context)
            elif data == 'confirm_withdraw':
                client = context.user_data['client']
                website = context.user_data['website']
                amount = context.user_data['amount']
                delivery_man = context.user_data['delivery_man']
                add_sheet_row(amount, user_id, client, website, delivery_man, "")
                log_action(f"משיכה בסך {amount} תועדה בהצלחה, שליח: {delivery_man} ", str(user_id))
                print(f"משיכה בסך {amount} תועדה בהצלחה")

                # Create the menu buttons
                keyboard = [
                    [InlineKeyboardButton("חזור לתפריט הראשי", callback_data='return_to_main_menu')],
                    [InlineKeyboardButton("בצע עוד משיכה", callback_data='withdraw')]
                ]

                # Send the message with the buttons
                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(chat_id=user_id, text=f"משיכה בסך {amount} תועדה בהצלחה",
                                               reply_markup=reply_markup)
            elif data == 'cancel_withdraw':
                await query.message.reply_text('המשיכה בוטלה.')
            elif data == 'transfer':
                context.user_data['move'] = 't'
                context.user_data['step'] = 'client_name'
                await query.message.reply_text('הכנס שם לקוח:')
            elif data == 'withdraw':
                context.user_data['move'] = 'w'
                context.user_data['step'] = 'client_name'
                await query.message.reply_text('הכנס שם לקוח:')
            elif data == 'transfer_same_acc':
                context.user_data['step'] = 'amount_same_acc'
                await query.message.reply_text('הכנס כמות להעברה בין 0 ל10000:')
                await start(update, context)
            elif data.startswith('confirm_transfer_'):
                parts = data.split('_')
                account_type = parts[2]
                account_id = parts[3]
                context.user_data['account_id'] = account_id
                amount = float(parts[4])
                # Retrieve the transfer data from user_data
                transfer_data = context.user_data.get('transfer_data', {})
                balance = transfer_data.get('balance', 0)
                # Calculate the new balance
                new_balance = balance - amount
                update_account_balance('../Database/accounts.db', account_type, account_id, new_balance)
                # Log the action
                user_id = update.effective_user.id
                context.user_data['selected_account_id'] = account_id
                context.user_data['selected_account_type'] = account_type
                client_name = context.user_data['client']
                website = context.user_data['website']
                if account_type == 'M':
                    full_name = fetch_name(account_type, account_id)
                else:
                    full_name = ''
                delivery_man = ''
                commission = fetch_commission(account_type, account_id)
                add_sheet_row(amount, user_id, client_name, website, delivery_man, full_name, commission, account_type,
                              account_id)
                if account_type == 'M':
                    log_action(f"העביר {amount} לחשבון {account_id} מסוג : חשבון בנק עם יתרה חדשה של {new_balance}",
                               str(user_id))
                elif account_type == 'P':
                    log_action(f"העביר {amount} לחשבון {account_id} מסוג: פייבוקס עם יתרה חדשה של {new_balance}",
                               str(user_id))
                elif account_type == 'B':
                    log_action(f"העביר {amount} לחשבון {account_id} מסוג: ביט עם יתרה חדשה של {new_balance}",
                               str(user_id))
                # Prepare the keyboard for further options
                keyboard = [
                    [InlineKeyboardButton("בצע עוד העברה", callback_data='transfer')],
                    [InlineKeyboardButton("בצע עוד העברה לאותו החשבון", callback_data='transfer_same_acc')],
                    [InlineKeyboardButton("חזור לתפריט הראשי", callback_data='return_to_main_menu')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                # Get the callback query object
                query = update.callback_query
                # Send a confirmation message and then the keyboard for further actions
                if query:
                    await query.message.reply_text(
                        f'ההעברה של {amount:.2f} ל-חשבון: {account_id:}  מסוג: {account_type} בוצעה בהצלחה! עם יתרה חדשה של:  {new_balance:.2f}',
                        reply_markup=reply_markup)
                else:
                    # Handle case where there's no callback_query, log an error
                    logging.error("No callback_query found in update")
            else:
                await query.message.reply_text('🚫 אין גישה.')
        else:
            await query.message.reply_text('🚫 אין גישה.')
    except Exception as e:
        logging.error(f"Error handling button press: {str(e)}")


async def handle_pagination(update: Update, context: CallbackContext):
    callback_query = update.callback_query
    data = callback_query.data
    chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id

    if data.startswith('view_page_'):
        parts = data.split('_')
        if len(parts) == 3:
            _, _, page_number = parts
            page_number = int(page_number)  # Convert page_number to integer
            context.user_data['page_number'] = page_number
            await view_accounts(update=update, context=context, page_number=page_number)
        else:
            logging.error(f"Unexpected data format: {data}")
    elif data.startswith('view_logs_page_'):
        page_number = int(data.split("_")[3])
        await send_logs_json_file(update, context, page_number=page_number)
    elif data.startswith('view_accounts_page_'):
        page_number = int(data.split("_")[3])
        await send_accounts_json_file(update, context, page_number=page_number)
    else:
        logging.error(f"Unhandled callback data: {data}")


async def handle_text(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    step = context.user_data.get('step')
    message_text = update.message.text
    if step == 'new_entry_step1':
        context.user_data['new_info1'] = message_text
        await update.message.reply_text('כינוי:')
        context.user_data['step'] = 'new_entry_step2'
    elif step == 'deletion':
        context.user_data['account_type'] = message_text
        await update.message.reply_text('מספר חשבון ')
        context.user_data['step'] = 'deletion2'
    elif step == 'deletion2':
        context.user_data['account_id'] = message_text
        accID = context.user_data['account_id']
        accTY = context.user_data['account_type']
        deleted = delete_account_from_db(accTY, accID)
        if deleted:
            await update.message.reply_text(
                f"חשבון {accID} מסוג {accTY} עם יתרה של:{get_account_balance(accTY, accID)} נמחק בהצלחה.")
            log_action(
                f' מחק את חשבון {accID} מסוג:{get_heb_acc(accTY)} עם יתרה של: {get_account_balance(accTY, accID)} ',
                str(user_id))
        else:
            await update.message.reply_text(f"לא נמצא חשבון {accID} מסוג {accTY} .")
    elif step == 'new_entry_step2':
        context.user_data['new_info2'] = message_text
        await update.message.reply_text('האם מנהל? (0) לא (1) כן:')
        context.user_data['step'] = 'new_entry_step3'
    elif step == 'new_entry_step3':
        new_info1 = context.user_data.get('new_info1')
        new_info2 = context.user_data.get('new_info2')
        isAdmin = message_text
        try:
            # Insert the new entry into the new SQL table
            insert_new_entry_to_db(new_info1, new_info2, isAdmin)
            await update.message.reply_text(f'✅ משתמש {new_info2} מספר {new_info1} נוסף בהצלחה')
            context.user_data.clear()
            # Show options to add/edit another or return to main menu
            keyboard = [
                [InlineKeyboardButton("הוסף/עדכן עוד אחד", callback_data='add_new_entry')],
                [InlineKeyboardButton("מחק סוכן", callback_data='delete_user')],
                [InlineKeyboardButton("חזור לתפריט הראשי", callback_data='return_to_main_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text('בחר פעולה:', reply_markup=reply_markup)
        except Exception as e:
            await update.message.reply_text(f'⚠️ שגיאה: {str(e)}')
    elif step == "client_name":
        context.user_data['client'] = message_text
        await update.message.reply_text('הכנס שם אתר:')
        context.user_data['step'] = 'website'
    elif step == 'website':
        context.user_data['website'] = message_text
        await update.message.reply_text('הכנס סכום להעברה:')
        context.user_data['step'] = 'amount'
    elif step == 'amount':
        move = context.user_data['move']
        try:
            amount = float(message_text)
            if not (0 <= amount <= 10000):
                raise ValueError
            context.user_data['amount'] = amount
            if move == 't':
                await update.message.reply_text('בחר את סוג החשבון (B, P, M):')
                context.user_data['step'] = 'account_type'
            elif move == 'w':
                await update.message.reply_text('הכנס את שם השליח (אם אין שליח הכנס 0):')
                context.user_data['step'] = 'delivery_man'
        except ValueError:
            await update.message.reply_text('🔢 Please enter a valid number between 0 and 10000.')
        return
    elif step == 'account_type':
        account_type = message_text.upper()
        if account_type not in ['B', 'P', 'M']:
            await update.message.reply_text('⚠️ Invalid account type. Please enter B, P, or M.')
            return
        context.user_data['account_type'] = account_type
        # Call the transfer function directly with amount and account type
        logging.info(f"Context data before transfer: {context.user_data}")
        await transfer(update, context)
    elif step == 'delivery_man':
        context.user_data['delivery_man'] = message_text
        client = context.user_data['client']
        website = context.user_data['website']
        amount = context.user_data['amount']
        delivery_man = context.user_data['delivery_man']
        message = (f"אשר משיכה על סך{amount:.2f}  עבור לקוח:{client} באתר: {website} עם שליח:{delivery_man}   \n\n")
        keyboard = [
            [InlineKeyboardButton("אשר", callback_data=f'confirm_withdraw')],
            [InlineKeyboardButton("בטל", callback_data='cancel_withdraw')],
            [InlineKeyboardButton("חזור לתפריט הראשי", callback_data='return_to_main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
    elif step == 'amount_same_acc':
        try:
            amount = float(message_text)
            if not (0 <= amount <= 10000):
                raise ValueError
            context.user_data['amount'] = amount
            await transfer_same(update, context)
        except ValueError:
            await update.message.reply_text('🔢 Please enter a valid number between 0 and 10000.')
        return

    elif step == 'account_id_b_p_m':
        context.user_data['account_id'] = message_text
        await update.message.reply_text('הכנס עמלה באחוזים:')
        context.user_data['step'] = 'commission_b_p_m'
    elif step == 'commission_b_p_m':
        context.user_data['commission'] = message_text
        await update.message.reply_text('הכנס יתרה:')
        context.user_data['step'] = 'balance_b_p_m'
    elif step == 'balance_b_p_m':
        balance = message_text
        try:
            balance = float(balance)
            if balance <= 0:
                await update.message.reply_text('🔢 Balance must be a positive number.')
                return
        except ValueError:
            await update.message.reply_text('🔢 Balance must be a number.')
            return
        account_type = context.user_data.get('account_type')
        if account_type == 'B':
            # Set the reason step
            context.user_data['balance'] = balance
            await update.message.reply_text('הכנס סיבה:')
            context.user_data['step'] = 'reason'
        elif account_type == 'P':
            # Handle other account types
            context.user_data['balance'] = balance
            branch_number = '0'
            bank_number = '0'
            daily = 0.0
            monthly = 0.0
            commission = context.user_data['commission']
            add_account_to_db(account_type, context.user_data['account_id'], balance, branch_number, bank_number, daily,
                              monthly, commission)
            await update.message.reply_text(
                f'✅ חשבון {context.user_data["account_id"]} מסוג {account_type} נוסף/עודכן, יתרה: {context.user_data["balance"]}.')
            log_action(
                f" הוסיף/עדכן את חשבון {context.user_data['account_id']} מסוג פייבוקס עם יתרה של{context.user_data['balance']}",
                str(user_id))
            context.user_data.clear()
            # Show options to add/edit another or return to main menu
            keyboard = [
                [InlineKeyboardButton("הוסף/עדכן עוד אחד", callback_data='add_account')],
                [InlineKeyboardButton("חזור לתפריט הראשי", callback_data='return_to_main_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text('בחר פעולה:', reply_markup=reply_markup)
        elif account_type == 'M':
            context.user_data['balance'] = balance
            await update.message.reply_text('הכנס שם מלא:')
            context.user_data['step'] = 'full_name'
        return
    elif step == 'reason':
        context.user_data['reason'] = message_text
        # Continue with the next step after the reason is provided
        branch_number = '0'
        bank_number = '0'
        daily = 0.0
        monthly = 0.0
        accTY = context.user_data['account_type']
        accID = context.user_data['account_id']
        accBal = context.user_data['balance']
        commission = context.user_data['commission']
        reason = context.user_data['reason']

        add_account_to_db(accTY, accID, accBal, branch_number,
                          bank_number, daily, monthly, commission, reason)
        await update.message.reply_text(
            f'✅ חשבון {accID} מסוג {accTY} נוסף/עודכן, יתרה: {accBal}, סיבה: {reason}')
        log_action(
            f" הוסיף/עדכן את חשבון {accID} מסוג: ביט עם יתרה של{accBal}",
            str(user_id))
        context.user_data.clear()
        # Show options to add/edit another or return to main menu
        keyboard = [
            [InlineKeyboardButton("הוסף/עדכן עוד אחד", callback_data='add_account')],
            [InlineKeyboardButton("חזור לתפריט הראשי", callback_data='return_to_main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('בחר פעולה:', reply_markup=reply_markup)
        return
    elif step == 'full_name':
        context.user_data['full_name'] = message_text
        await update.message.reply_text('מספר סניף:')
        context.user_data['step'] = 'branch_number_m'
    elif step == 'branch_number_m':
        context.user_data['branch_number'] = message_text
        await update.message.reply_text('מספר בנק:')
        context.user_data['step'] = 'bank_number_m'
    elif step == 'bank_number_m':
        context.user_data['bank_number'] = message_text
        await update.message.reply_text('כמה העברות יומיות?:')
        context.user_data['step'] = 'daily_m'
    elif step == 'daily_m':
        daily = message_text
        try:
            daily = float(daily)
            if not (0 <= daily <= 2):
                await update.message.reply_text('🔢 כמות יומית בין 0 ל2.')
                return
        except ValueError:
            await update.message.reply_text('🔢 כמות יומית במספרים בלבד.')
            return
        context.user_data['daily'] = daily
        await update.message.reply_text('כמה העברות חודשיות?:')
        context.user_data['step'] = 'monthly_m'
    elif step == 'monthly_m':
        monthly = message_text
        context.user_data['monthly'] = message_text
        try:
            monthly = float(monthly)
            if not (0 <= monthly <= 10):
                await update.message.reply_text('🔢 כמות חודשית בין 0 ל10.')
                return
            if monthly < context.user_data['daily']:
                await update.message.reply_text('⚠️ כמות חודשית חייבת להיות גדולה/שווה לכמות יומית')
                return
        except ValueError:
            await update.message.reply_text('🔢 כמות חודשית במספרים בלבד')
            return
        # Add or update the M account
        account_type = context.user_data.get('account_type')
        account_id = context.user_data.get('account_id', '')  # Ensure it's a string
        balance = context.user_data.get('balance', 0.0)  # Ensure it's a float
        branch_number = context.user_data.get('branch_number', '')  # Ensure it's a string
        bank_number = context.user_data.get('bank_number', '')  # Ensure it's a string
        daily = context.user_data.get('daily', 0.0)  # Ensure it's a float
        monthly = context.user_data.get('monthly', 0.0)  # Ensure it's a float
        commission = context.user_data.get('commission', 0.0)  # Ensure it's a float
        full_name = context.user_data.get('full_name', 'ריק')  # Ensure it's a string
        date = context.user_data.get('date')  # Default to None if not provided
        reason = context.user_data.get('reason', 'ללא סיבה')  # Default to 'ללא סיבה' if not provided

        # Call the add_account_to_db function with the sanitized data
        add_account_to_db(
            account_type,
            account_id,
            balance,
            branch_number,
            bank_number,
            daily,
            monthly,
            commission,
            reason,
            full_name,
            date
        )
        await update.message.reply_text(
            f'✅ חשבון {context.user_data["account_id"]} מסוג {context.user_data["account_type"]} נוסף/עודכן עם יתרה של {context.user_data["balance"]}')
        log_action(
            f" הוסיף/עדכן את חשבון {context.user_data['account_id']} מסוג: חשבון בנק  עם יתרה של{context.user_data['balance']}",
            str(user_id))
        context.user_data.clear()
        # Show options to add/edit another or return to main menu
        keyboard = [
            [InlineKeyboardButton("הוסף/עדכן עוד אחד", callback_data='add_account')],
            [InlineKeyboardButton("חזור לתפריט הראשי", callback_data='return_to_main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('בחר פעולה:', reply_markup=reply_markup)
        return
    elif step == 'delete_account':
        account_id = message_text
        account_type = context.user_data.get('account_type')
        delete_account_from_db(account_type, account_id)
        await update.message.reply_text(f'✅ חשבון {account_id} מסוג {account_type} הוסר.')
        await update.message.reply_text('הרשימה המעודכנת', reply_markup=build_account_buttons('remove'))
        context.user_data.clear()
    else:
        await update.message.reply_text('פקודה לא מוכרת.')


async def show_user_management_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("Add User", callback_data='add_user')],
        [InlineKeyboardButton("Delete User", callback_data='delete_user')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Edit the message text and reply markup
    await query.message.edit_text('Choose an action:', reply_markup=reply_markup)


async def view_accounts(update: Update, context: CallbackContext, page_number: int) -> None:
    # Determine if update is CallbackQuery or Message
    if isinstance(update, CallbackQuery):
        query = update
        message = query.message
        user_id = query.from_user.id
    else:
        # This case should be rare, handle it if needed
        query = update.callback_query
        message = query.message
        user_id = update.effective_user.id
    if user_id not in [ADMIN_ID, SECOND_ADMIN_ID]:
        await query.answer(text='🚫 אין גישה.')
        return
    # Pagination setup
    page_size = 5
    page_number = page_number or int(context.user_data.get('page_number', 1))
    accounts = get_accounts_from_db()
    if not accounts:
        await message.reply_text('No accounts found.')
        return
    # Sort accounts by account type
    accounts.sort(key=lambda acc: acc[0])
    # Pagination logic
    total_pages = math.ceil(len(accounts) / page_size)

    start_index = (page_number - 1) * page_size
    end_index = min(start_index + page_size, len(accounts))
    message_text = 'Accounts:\n'
    keyboard = []
    for acc in accounts[start_index:end_index]:
        if len(acc) == 10:
            account_type, account_id, balance, branch_number, bank_number, daily, monthly, reason, full_name, date = acc
            if account_type == 'M':
                message_text += (f"*סוג:* {account_type}\n"
                                 f"*מספר חשבון בנק:* {account_id}\n"
                                 f"*יתרה:* {balance:.2f}\n"
                                 f"*מס' סניף:* {branch_number}\n"
                                 f"*מס' בנק:* {bank_number}\n"
                                 f"*העברות יומיות:* {daily:.2f}\n"
                                 f"*העברות חודשיות:* {monthly:.2f}\n\n")
            elif account_type in ['P']:
                message_text += (f"*סוג:* {account_type}\n"
                                 f"*טלפון:* {account_id}\n"
                                 f"*יתרה:* {balance:.2f}\n\n")
            elif account_type in ['B']:
                message_text += (f"*סוג:* {account_type}\n"
                                 f"*סיבה:* {reason}\n"
                                 f"*טלפון:* {account_id}\n"
                                 f"*יתרה:* {balance:.2f}\n\n")
        else:
            message_text += f"Error: Unexpected data format for account ID {acc[1]}\n"
    # Navigation buttons
    if total_pages > 1:
        if page_number > 1:
            keyboard.append([InlineKeyboardButton("◀️ Previous", callback_data=f'view_page_{page_number - 1}')])
        if page_number < total_pages:
            keyboard.append([InlineKeyboardButton("Next ▶️", callback_data=f'view_page_{page_number + 1}')])
    keyboard.append([InlineKeyboardButton("חזור לתפריט הראשי", callback_data='return_to_main_menu')]
                    )
    keyboard.append([InlineKeyboardButton("ייצא ל Json", callback_data='export_json')]
                    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Update the existing message with the new text and keyboard
    if isinstance(update, CallbackQuery):
        await query.message.edit_text(message_text, parse_mode='Markdown', reply_markup=reply_markup)
        await query.answer()  # Acknowledge the callback query
    else:
        await message.edit_text(message_text, parse_mode='Markdown', reply_markup=reply_markup)


def build_account_buttons(action, page=0):
    accounts = get_accounts_from_db()  # Get accounts from the database
    total_pages = (len(accounts) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    # Calculate start and end indices for the current page
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    current_items = accounts[start:end]
    # Create inline keyboard buttons for the current page
    keyboard = [
        [InlineKeyboardButton(
            f"סוג: {acc[0]} | מזהה: {acc[1]} | יתרה: {acc[2]:.2f}",
            callback_data=f"{action}_{acc[0]}_{acc[1]}")
        ]
        for acc in current_items
    ]
    keyboard.append(
        [InlineKeyboardButton(f"חזור לתפריט הראשי", callback_data='return_to_main_menu')]
    )
    # Add navigation buttons
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton("קודם", callback_data=f"page_{action}_{page - 1}"))
    if page < total_pages - 1:
        navigation_buttons.append(InlineKeyboardButton("הבא", callback_data=f"page_{action}_{page + 1}"))
    if navigation_buttons:
        keyboard.append(navigation_buttons)
    return InlineKeyboardMarkup(keyboard)
