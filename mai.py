# PagaLEscrowBot - A Simple Telegram Escrow Bot in Python
# This is a basic implementation using the python-telegram-bot library.
# An escrow bot helps facilitate secure transactions by holding funds (simulated here)
# until both parties confirm. For real payments, integrate with a payment gateway like Stripe or PayPal.
# WARNING: This is for educational purposes. Do not use for real financial transactions without proper security and legal compliance.

# Installation requirements:
# pip install python-telegram-bot

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace 'YOUR_BOT_TOKEN' with your actual Telegram Bot Token from BotFather
BOT_TOKEN = '8499035595:AAEH9O4-t7NuhvneC9MOg4vTzqUYEjnVUQY'

# In-memory storage for escrows (use a database like SQLite in production)
escrows = {}  # Format: {escrow_id: {'buyer': user_id, 'seller': user_id, 'amount': amount, 'description': desc, 'status': 'pending/open/confirmed/cancelled'}}

def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    welcome_text = f"""
Welcome, {user.first_name}! 👋

I'm PagaLEscrowBot, a simple escrow service bot for secure transactions on Telegram.

How it works:
1. /initiate - Start a new escrow (as buyer or seller).
2. /list - List active escrows.
3. /confirm - Confirm receipt (for buyer).
4. /release - Release funds (for seller after confirmation).
5. /cancel - Cancel an escrow.

For real payments, this bot simulates escrow. Integrate with payment APIs for actual fund holding.
    """
    update.message.reply_text(welcome_text)

def initiate_escrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Initiate a new escrow. Usage: /initiate <amount> <description> @seller_username"""
    if not context.args:
        update.message.reply_text("Usage: /initiate <amount> <description> @seller_username\nExample: /initiate 100 USD for laptop @seller123")
        return
    
    try:
        amount = context.args[0]
        description = ' '.join(context.args[1:-1])  # Everything except last arg (seller)
        seller_username = context.args[-1]  # Last arg is seller @username
        
        # Generate escrow ID (simple counter for demo)
        escrow_id = len(escrows) + 1
        
        escrows[escrow_id] = {
            'buyer': update.effective_user.id,
            'seller': seller_username,
            'amount': amount,
            'description': description,
            'status': 'pending'
        }
        
        keyboard = [
            [InlineKeyboardButton("I am the Seller", callback_data=f'seller_confirm_{escrow_id}')],
            [InlineKeyboardButton("Cancel", callback_data=f'cancel_{escrow_id}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(
            f"Escrow initiated!\nID: {escrow_id}\nAmount: {amount}\nDescription: {description}\nSeller: {seller_username}\n\nWaiting for seller confirmation.",
            reply_markup=reply_markup
        )
        
        # Notify seller (simulate; in real, forward message or use username resolution)
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"Escrow {escrow_id} initiated by {update.effective_user.username}. Check /list.")
        
    except Exception as e:
        update.message.reply_text(f"Error initiating escrow: {str(e)}")

def list_escrows(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all escrows involving the user."""
    user_id = update.effective_user.id
    user_escrows = [e for e in escrows.items() if user_id == e[1]['buyer'] or e[1]['seller'] == f"@{update.effective_user.username}"]
    
    if not user_escrows:
        update.message.reply_text("No active escrows found.")
        return
    
    text = "Your Escrows:\n\n"
    for escrow_id, details in user_escrows:
        role = "Buyer" if user_id == details['buyer'] else "Seller"
        text += f"ID: {escrow_id} | Role: {role} | Amount: {details['amount']} | Status: {details['status']} | Desc: {details['description'][:50]}...\n"
    
    update.message.reply_text(text)

def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    query.answer()
    
    data = query.data
    if data.startswith('seller_confirm_'):
        escrow_id = int(data.split('_')[-1])
        escrow = escrows.get(escrow_id)
        if not escrow:
            query.edit_message_text("Escrow not found.")
            return
        
        if escrow['status'] != 'pending':
            query.edit_message_text("Escrow already processed.")
            return
        
        # Simulate seller confirmation (in real, verify seller)
        seller_username = f"@{query.from_user.username}"
        if seller_username != escrow['seller']:
            query.edit_message_text("You are not the seller.")
            return
        
        escrow['status'] = 'open'
        query.edit_message_text(
            f"Escrow {escrow_id} confirmed by seller!\nStatus: Open\nBuyer can now send payment (simulated).\nUse /confirm {escrow_id} to confirm receipt."
        )
        
    elif data.startswith('cancel_'):
        escrow_id = int(data.split('_')[-1])
        escrow = escrows.get(escrow_id)
        if not escrow or escrow['status'] != 'pending':
            query.edit_message_text("Cannot cancel.")
            return
        
        del escrows[escrow_id]
        query.edit_message_text(f"Escrow {escrow_id} cancelled.")

def confirm_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Buyer confirms receipt. Usage: /confirm <escrow_id>"""
    if not context.args:
        update.message.reply_text("Usage: /confirm <escrow_id>")
        return
    
    try:
        escrow_id = int(context.args[0])
        escrow = escrows.get(escrow_id)
        if not escrow:
            update.message.reply_text("Escrow not found.")
            return
        
        if update.effective_user.id != escrow['buyer']:
            update.message.reply_text("You are not the buyer.")
            return
        
        if escrow['status'] != 'open':
            update.message.reply_text("Escrow not open for confirmation.")
            return
        
        escrow['status'] = 'confirmed'
        update.message.reply_text(
            f"Receipt confirmed for Escrow {escrow_id}!\nSeller can now release funds.\nUse /release {escrow_id}."
        )
        
    except ValueError:
        update.message.reply_text("Invalid escrow ID.")

def release_funds(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Seller releases funds after confirmation. Usage: /release <escrow_id>"""
    if not context.args:
        update.message.reply_text("Usage: /release <escrow_id>")
        return
    
    try:
        escrow_id = int(context.args[0])
        escrow = escrows.get(escrow_id)
        if not escrow:
            update.message.reply_text("Escrow not found.")
            return
        
        seller_username = f"@{update.effective_user.username}"
        if seller_username != escrow['seller']:
            update.message.reply_text("You are not the seller.")
            return
        
        if escrow['status'] != 'confirmed':
            update.message.reply_text("Escrow not confirmed by buyer yet.")
            return
        
        escrow['status'] = 'completed'  # Or 'released'
        update.message.reply_text(f"Funds released for Escrow {escrow_id}! Transaction completed.")
        
    except ValueError:
        update.message.reply_text("Invalid escrow ID.")

def cancel_escrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel an escrow. Usage: /cancel <escrow_id>"""
    if not context.args:
        update.message.reply_text("Usage: /cancel <escrow_id>")
        return
    
    try:
        escrow_id = int(context.args[0])
        escrow = escrows.get(escrow_id)
        if not escrow:
            update.message.reply_text("Escrow not found.")
            return
        
        user_id = update.effective_user.id
        seller_username = f"@{update.effective_user.username}"
        if user_id != escrow['buyer'] and seller_username != escrow['seller']:
            update.message.reply_text("You are not part of this escrow.")
            return
        
        if escrow['status'] == 'completed':
            update.message.reply_text("Cannot cancel completed escrow.")
            return
        
        del escrows[escrow_id]
        update.message.reply_text(f"Escrow {escrow_id} cancelled.")
        
    except ValueError:
        update.message.reply_text("Invalid escrow ID.")

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("initiate", initiate_escrow))
    application.add_handler(CommandHandler("list", list_escrows))
    application.add_handler(CommandHandler("confirm", confirm_receipt))
    application.add_handler(CommandHandler("release", release_funds))
    application.add_handler(CommandHandler("cancel", cancel_escrow))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
