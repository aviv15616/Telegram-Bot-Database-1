import sqlite3
from functools import wraps
from telegram import Update
from telegram.ext import CallbackContext

# =============================
#  Authorization Decorators
# =============================

def authorized_only(handler):
    """Decorator that restricts access to authorized users only."""
    @wraps(handler)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id
        if is_authorized(user_id):
            return await handler(update, context, *args, **kwargs)
        else:
            await _deny_access(update)
    return wrapper


def admin_only(handler):
    """Decorator that restricts access to admin users only."""
    @wraps(handler)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id
        if is_admin(user_id):
            return await handler(update, context, *args, **kwargs)
        else:
            await _deny_access(update)
    return wrapper


async def _deny_access(update: Update):
    """Sends a polite denial message when user is not authorized."""
    message = "🚫 You are not authorized to use this command."
    if update.message:
        await update.message.reply_text(message)
    elif update.callback_query:
        await update.callback_query.answer(message)


# =============================
#  Authorization Logic
# =============================

DB_PATH = "../Data/users.db"  # Neutralized path


def is_admin(user_id: int) -> bool:
    """Checks if a given user is marked as admin in the database."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT isAdmin FROM users WHERE userID = ?", (user_id,))
            result = cursor.fetchone()
        return bool(result and result[0] == 1)
    except sqlite3.Error as e:
        print(f"[DB ERROR] {e}")
        return False


def is_authorized(user_id: int) -> bool:
    """Checks whether the user exists in the database (authorized)."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE userID = ?", (user_id,))
            count = cursor.fetchone()[0]
        return count > 0
    except sqlite3.Error as e:
        print(f"[DB ERROR] {e}")
        return False


# =============================
#  File Utilities (optional)
# =============================

def add_user_to_whitelist(user_id: int, nickname: str = None):
    """Adds a user to a local whitelist file."""
    file_path = "allowed_users.txt"
    with open(file_path, "a", encoding="utf-8") as file:
        entry = f"{user_id},{nickname}\n" if nickname else f"{user_id}\n"
        file.write(entry)
