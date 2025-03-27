from telegram import Update, InputMediaPhoto
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from PIL import Image
import io
import os

# Store user images temporarily
user_images = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me 4 images one by one and I’ll combine them into a 2x2 image.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()

    if user_id not in user_images:
        user_images[user_id] = []

    user_images[user_id].append(photo_bytes)

    count = len(user_images[user_id])
    if count < 4:
        await update.message.reply_text(f"Received image {count}/4. Please send {4 - count} more.")
    else:
        await update.message.reply_text("Combining images...")
        combined_image = combine_images(user_images[user_id])
        bio = io.BytesIO()
        bio.name = 'combined.jpg'
        combined_image.save(bio, 'JPEG')
        bio.seek(0)

        await update.message.reply_photo(photo=bio)
        user_images[user_id] = []  # Reset after sending

def combine_images(images_bytes):
    images = [Image.open(io.BytesIO(img)).resize((300, 300)) for img in images_bytes]
    new_image = Image.new('RGB', (600, 600))

    new_image.paste(images[0], (0, 0))
    new_image.paste(images[1], (300, 0))
    new_image.paste(images[2], (0, 300))
    new_image.paste(images[3], (300, 300))

    return new_image

if __name__ == '__main__':
    # bot_token = "7739487074:AAFe534Etiqom7vv6JoBiwO5kYehP-Sfek8"
    TOKEN = os.environ["BOT_TOKEN"]
    bot_token = TOKEN
    app = ApplicationBuilder().token(bot_token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot is running...")
    app.run_polling()