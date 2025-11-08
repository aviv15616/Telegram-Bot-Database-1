import os
import sys

# Ensure that PyFiles directory can be found by Python
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
from imports import *
from config import *

from PyFiles.DatabaseManager import initialize_db, reset_daily_credentials, reset_monthly_credentials
from PyFiles.Tools import send_logs_json_file
from PyFiles.UI import handle_text, start, button, handle_pagination
# Create your logger instance
def main() -> None:
    # Create handlers
    start_handler = CommandHandler('start', start)
    # Add handlers to dispatcher
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(reset_daily_credentials, 'cron', day_of_week='sun,mon,tue,wed,thu', hour=18, minute=0)
    scheduler.add_job(reset_daily_credentials, 'cron', day_of_week='fri', hour=13, minute=0)
    scheduler.add_job(reset_monthly_credentials, 'cron', day=1, hour=0, minute=1)
    initialize_db()
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(start_handler)
    application.add_handler(CommandHandler('send_logs', send_logs_json_file))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CallbackQueryHandler(handle_pagination))
    application.run_polling()
if __name__ == '__main__':
    main()
