from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from PIL import Image
import io
import os

# Store user images temporarily
user_images = {}

# Grid and size config
COLUMNS = 2
ROWS = 2
CELL_WIDTH = 300
CELL_HEIGHT = 450
FINAL_WIDTH = CELL_WIDTH * COLUMNS
FINAL_HEIGHT = CELL_HEIGHT * ROWS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me 4 images one by one and I’ll combine them into a 2:3 ratio image.")

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
        await update.message.reply_text("Combining images into 2:3 layout...")
        combined_image = combine_images(user_images[user_id])
        bio = io.BytesIO()
        bio.name = 'combined.jpg'
        combined_image.save(bio, 'JPEG')
        bio.seek(0)

        await update.message.reply_photo(photo=bio)
        user_images[user_id] = []  # Reset after sending

def crop_to_fit(image, target_width, target_height):
    original_width, original_height = image.size
    target_ratio = target_width / target_height
    original_ratio = original_width / original_height

    if original_ratio > target_ratio:
        # Crop width
        new_width = int(target_ratio * original_height)
        offset = (original_width - new_width) // 2
        box = (offset, 0, offset + new_width, original_height)
    else:
        # Crop height
        new_height = int(original_width / target_ratio)
        offset = (original_height - new_height) // 2
        box = (0, offset, original_width, offset + new_height)

    return image.crop(box).resize((target_width, target_height), Image.ANTIALIAS)

def combine_images(images_bytes):
    images = [Image.open(io.BytesIO(img)) for img in images_bytes]
    processed_images = [crop_to_fit(img, CELL_WIDTH, CELL_HEIGHT) for img in images]

    combined = Image.new('RGB', (FINAL_WIDTH, FINAL_HEIGHT))

    for idx, img in enumerate(processed_images):
        x = (idx % COLUMNS) * CELL_WIDTH
        y = (idx // COLUMNS) * CELL_HEIGHT
        combined.paste(img, (x, y))

    return combined

if __name__ == '__main__':
    TOKEN = os.environ["BOT_TOKEN"]
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot is running...")
    app.run_polling()
