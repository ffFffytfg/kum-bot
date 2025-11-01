import os
import logging
import random
from typing import Optional
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Game state storage (in-memory, resets on restart)
game_state = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "🤖 Hello! I'm a Gemini-powered bot!\n\n"
        "Commands:\n"
        "/help - Show all commands\n"
        "/ask [question] - Ask me anything\n"
        "/dice - Roll a dice\n"
        "/8ball [question] - Magic 8-ball\n"
        "/trivia - Random trivia question\n"
        "/rps [rock/paper/scissors] - Play Rock Paper Scissors\n"
        "/flip - Flip a coin\n\n"
        "In groups, mention me or reply to my messages to chat!"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message."""
    await update.message.reply_text(
        "📚 Available Commands:\n\n"
        "🤖 AI Commands:\n"
        "/ask [question] - Ask Gemini anything\n\n"
        "🎮 Mini-Games:\n"
        "/dice - Roll a 6-sided dice\n"
        "/flip - Flip a coin\n"
        "/8ball [question] - Ask the magic 8-ball\n"
        "/trivia - Get a random trivia question\n"
        "/rps [choice] - Rock, Paper, Scissors\n"
        "  Example: /rps rock\n\n"
        "💬 Group Chat:\n"
        "Mention @botname or reply to my messages to chat with Gemini!"
    )


async def ask_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask Gemini a question."""
    if not context.args:
        await update.message.reply_text("Please provide a question! Example: /ask What is Python?")
        return

    question = ' '.join(context.args)
    await update.message.reply_text("🤔 Thinking...")

    try:
        response = model.generate_content(question)
        await update.message.reply_text(response.text)
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages in group chats where bot is mentioned or replied to."""
    message = update.message
    bot_username = context.bot.username

    # Check if bot is mentioned or message is a reply to bot
    is_mentioned = f"@{bot_username}" in message.text if message.text else False
    is_reply_to_bot = (
            message.reply_to_message
            and message.reply_to_message.from_user.id == context.bot.id
    )

    if not (is_mentioned or is_reply_to_bot):
        return

    # Extract the actual message (remove mention)
    text = message.text.replace(f"@{bot_username}", "").strip()

    if not text:
        await message.reply_text("Yes? How can I help you?")
        return

    try:
        response = model.generate_content(text)
        await message.reply_text(response.text)
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        await message.reply_text(f"❌ Sorry, I encountered an error: {str(e)}")


async def roll_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roll a dice mini-game."""
    result = random.randint(1, 6)
    dice_emoji = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"][result - 1]
    await update.message.reply_text(f"🎲 You rolled: {dice_emoji} ({result})")


async def flip_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Flip a coin mini-game."""
    result = random.choice(["Heads", "Tails"])
    emoji = "🪙" if result == "Heads" else "🔘"
    await update.message.reply_text(f"{emoji} The coin landed on: **{result}**!")


async def magic_8ball(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Magic 8-ball mini-game."""
    responses = [
        "Yes, definitely!", "It is certain.", "Without a doubt.",
        "You may rely on it.", "As I see it, yes.", "Most likely.",
        "Outlook good.", "Signs point to yes.", "Reply hazy, try again.",
        "Ask again later.", "Better not tell you now.", "Cannot predict now.",
        "Concentrate and ask again.", "Don't count on it.", "My reply is no.",
        "My sources say no.", "Outlook not so good.", "Very doubtful."
    ]

    if not context.args:
        await update.message.reply_text("🔮 Ask the magic 8-ball a yes/no question!\nExample: /8ball Will I win?")
        return

    result = random.choice(responses)
    await update.message.reply_text(f"🔮 The magic 8-ball says: **{result}**")


async def rock_paper_scissors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rock Paper Scissors mini-game."""
    choices = ["rock", "paper", "scissors"]

    if not context.args or context.args[0].lower() not in choices:
        await update.message.reply_text(
            "✊✋✌️ Choose rock, paper, or scissors!\n"
            "Example: /rps rock"
        )
        return

    user_choice = context.args[0].lower()
    bot_choice = random.choice(choices)

    emoji_map = {"rock": "✊", "paper": "✋", "scissors": "✌️"}

    # Determine winner
    if user_choice == bot_choice:
        result = "It's a tie! 🤝"
    elif (
            (user_choice == "rock" and bot_choice == "scissors") or
            (user_choice == "paper" and bot_choice == "rock") or
            (user_choice == "scissors" and bot_choice == "paper")
    ):
        result = "You win! 🎉"
    else:
        result = "I win! 🤖"

    await update.message.reply_text(
        f"You chose: {emoji_map[user_choice]} {user_choice}\n"
        f"I chose: {emoji_map[bot_choice]} {bot_choice}\n\n"
        f"{result}"
    )


async def trivia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trivia mini-game."""
    questions = [
        {"q": "What is the capital of France?", "a": "Paris"},
        {"q": "What is 2 + 2?", "a": "4"},
        {"q": "What is the largest planet in our solar system?", "a": "Jupiter"},
        {"q": "Who painted the Mona Lisa?", "a": "Leonardo da Vinci"},
        {"q": "What is the smallest prime number?", "a": "2"},
        {"q": "In what year did World War II end?", "a": "1945"},
        {"q": "What is the chemical symbol for gold?", "a": "Au"},
        {"q": "How many continents are there?", "a": "7"},
    ]

    chat_id = update.effective_chat.id

    # Check if answering previous question
    if chat_id in game_state and 'trivia_answer' in game_state[chat_id]:
        if context.args:
            user_answer = ' '.join(context.args).strip()
            correct_answer = game_state[chat_id]['trivia_answer']

            if user_answer.lower() == correct_answer.lower():
                await update.message.reply_text("✅ Correct! Well done! 🎉")
            else:
                await update.message.reply_text(f"❌ Wrong! The correct answer was: {correct_answer}")

            del game_state[chat_id]['trivia_answer']
            await update.message.reply_text("Type /trivia for another question!")
            return

    # New question
    question_data = random.choice(questions)
    game_state[chat_id] = {'trivia_answer': question_data['a']}

    await update.message.reply_text(
        f"❓ Trivia Question:\n\n{question_data['q']}\n\n"
        f"Reply with: /trivia [your answer]"
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")


def main():
    """Start the bot."""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        return

    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not found in environment variables!")
        return

    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ask", ask_gemini))
    application.add_handler(CommandHandler("dice", roll_dice))
    application.add_handler(CommandHandler("flip", flip_coin))
    application.add_handler(CommandHandler("8ball", magic_8ball))
    application.add_handler(CommandHandler("rps", rock_paper_scissors))
    application.add_handler(CommandHandler("trivia", trivia))

    # Message handler for group chats
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_group_message
        )
    )

    # Error handler
    application.add_error_handler(error_handler)

    # Start the bot
    logger.info("Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
