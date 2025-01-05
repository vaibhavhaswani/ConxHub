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

# Add COMMANDS dictionary
COMMANDS = {
    'start': '🚀 Start the bot and show available scripts',
    'help': '❓ Show all available commands and usage information',
}

def format_scripts_list() -> str:
    """Format available scripts into a readable list"""
    scripts_text = "📜 *Available Scripts:*\n\n"
    for key, script in SCRIPTS.items():
        scripts_text += f"• {script['description']} (`{key}`)\n"
    return scripts_text

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
        await query.message.edit_text("❌ Invalid script selected. Please try again.")
        return
        
    script = SCRIPTS[script_key]
    message = await query.message.edit_text(f"⚙️ *Executing {script['description']}...*\n\nPlease wait while we process your request.")
    
    try:
        # Notify that the script is running
        await context.bot.send_message(chat_id=CHAT_ID, text=f"🚀 *{script['description']}* is running...")

        process = await asyncio.create_subprocess_exec(
            'python', script['file'],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            await message.edit_text(f"✅ *{script['description']}* completed successfully! 🎉\n\nThank you for your patience.")
            if stdout:
                logger.info(f"Script output: {stdout.decode().strip()}")
            # Notify that the script run is completed
            await context.bot.send_message(chat_id=CHAT_ID, text=f"✅ *{script['description']}* run completed successfully!")
        else:
            error_msg = stderr.decode().strip() if stderr else "No error output available"
            logger.error(f"Script failed with error: {error_msg}")
            await message.edit_text(f"❌ *{script['description']}* failed with the following error:\n\n{error_msg}")
            # Notify that the script run failed
            await context.bot.send_message(chat_id=CHAT_ID, text=f"❌ *{script['description']}* run failed with error:\n\n{error_msg}")
    except Exception as e:
        logger.error(f"Error executing script: {e}")
        await message.edit_text(f"❌ An unexpected error occurred:\n\n{str(e)}")
        # Notify that an unexpected error occurred
        await context.bot.send_message(chat_id=CHAT_ID, text=f"❌ An unexpected error occurred while running *{script['description']}*:\n\n{str(e)}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    try:
        keyboard = []
        for key, script in SCRIPTS.items():
            button = InlineKeyboardButton(
                f"🔄 Run {script['description']}", 
                callback_data=f"run_{key}"
            )
            keyboard.append([button])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🎉 *Welcome to Script Runner Bot!*\n\n"
            "I'm here to help you run various processing scripts.\n\n"
            f"{format_scripts_list()}\n"
            "Use /help to see all available commands.\n\n"
            "Select a script to run:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error handling start command: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "🤖 *ConxHub Bot Help*\n\n"
        "📋 *Available Commands:*\n"
    )
    
    for cmd, desc in COMMANDS.items():
        help_text += f"/{cmd} - {desc}\n"
    
    help_text += f"\n{format_scripts_list()}\n"
    help_text += (
        "\n💡 *How to use:*\n"
        "1. Use /start to see available scripts\n"
        "2. Click on any script button to run it\n"
        "3. Wait for the processing to complete\n"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

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
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Send startup notification
    try:
        await app.bot.send_message(
            chat_id=CHAT_ID,
            text=(
                "🚀 *ConxHub Bot is now online!*\n\n"
                "I'm here to assist you with running various scripts.\n"
                "Use /start to see available scripts or /help for more information.\n\n"
                "Let's get started! 🎉"
            ),
            parse_mode='Markdown'
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