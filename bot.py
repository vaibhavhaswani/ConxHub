import logging
import asyncio
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os
from dotenv import load_dotenv
import sys
from contextlib import asynccontextmanager
import signal

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Bot Configuration
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN or not CHAT_ID:
    logger.error("Missing required environment variables. Please check your .env file.")
    sys.exit(1)

SCRIPTS = {
    'conxhub': {
        'file': 'main.py',
        'description': 'ConxHub Processing Script'
    },
    # Add more scripts here as needed
    'example': {
        'file': 'example.py',
        'description': 'Example Processing Script'
    }
}

@asynccontextmanager
async def create_bot():
    """Context manager for bot lifecycle"""
    app = Application.builder().token(TOKEN).build()
    try:
        await app.initialize()
        await app.start()
        yield app
    finally:
        try:
            await app.stop()
            await app.shutdown()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

async def execute_script(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute selected script with proper error handling"""
    query = update.callback_query
    script_key = query.data.replace('run_', '')
    
    if script_key not in SCRIPTS:
        await query.message.edit_text("❌ Invalid script selected")
        return
        
    script = SCRIPTS[script_key]
    message = await query.message.edit_text(f"⚙️ Executing {script['description']}...")
    
    try:
        process = await asyncio.create_subprocess_exec(
            'python', script['file'],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            await message.edit_text("✅ ConxHub Processing completed successfully!")
            if stdout:
                logger.info(f"Script output: {stdout.decode().strip()}")
        else:
            error_msg = stderr.decode().strip() if stderr else "No error output available"
            logger.error(f"Script failed with error: {error_msg}")
            await message.edit_text(f"❌ Processing failed:\n{error_msg}")
    except Exception as e:
        logger.error(f"Error executing script: {e}")
        await message.edit_text(f"❌ Error: {str(e)}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    try:
        keyboard = []
        for key, script in SCRIPTS.items():
            button = InlineKeyboardButton(
                f"Run {script['description']}", 
                callback_data=f"run_{key}"
            )
            keyboard.append([button])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Welcome to Script Runner Bot!\nAvailable scripts:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error handling start command: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    try:
        query = update.callback_query
        await query.answer()  # Acknowledge the button press
        if query.data.startswith('run_'):
            await execute_script(update, context)
    except Exception as e:
        logger.error(f"Error handling button: {e}")

async def setup_bot(app: Application):
    """Setup bot handlers and send startup notification"""
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Send startup notification
    try:
        await app.bot.send_message(
            chat_id=CHAT_ID,
            text="🚀 ConxHub Bot is now online!"
        )
    except Exception as e:
        logger.error(f"Failed to send startup notification: {e}")

async def run_bot():
    """Run the bot with proper lifecycle management"""
    try:
        async with create_bot() as app:
            await setup_bot(app)
            logger.info("Bot started successfully")
            
            # Set up signal handlers
            stop_signal = asyncio.Event()
            signals = (signal.SIGINT, signal.SIGTERM, signal.SIGABRT)
            for sig in signals:
                signal.signal(sig, lambda s, _: stop_signal.set())
            
            # Start polling in the background
            async with app:
                await app.updater.start_polling()
                logger.info("Bot is polling for updates...")
                # Wait until one of the signals is received
                await stop_signal.wait()
                
    except Exception as e:
        logger.error(f"Bot operation error: {e}")

def main():
    """Entry point with proper asyncio handling"""
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()