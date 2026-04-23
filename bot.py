# بوت التصميم المعماري الاحترافي - Architect Bot
# المطور: بكري بيس

import os
import json
import re
import math
from datetime import datetime
import google.generativeai as genai
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image, ImageDraw
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===================== إعدادات البوت =====================
BOT_TOKEN = "7933927887:AAEK-uYKwa0T2X6bK5hIlO-DdAgOHy09Gvg"
GEMINI_API_KEY = "AIzaSyBqv5YfBlsQsJCyvz56TaA-tUXr26c6-Ow"
DEVELOPER_NAME = "بكري بيس"
BOT_USERNAME = "@BakriArchBot"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash-exp")

def extract_building_data(text: str) -> dict:
    prompt = f"""
    استخرج معلومات البناء من النص التالي. أخرج فقط JSON:
    {{"total_area": عدد, "rooms": [{{"type": "نوع", "count": عدد}}], "style": "نوع", "floors": عدد}}
    النص: {text}
    """
    try:
        response = model.generate_content(prompt)
        json_text = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(json_text)
    except:
        return {"total_area": 120, "rooms": [{"type": "living", "count": 1}, {"type": "bedroom", "count": 3}, {"type": "kitchen", "count": 1}, {"type": "bathroom", "count": 2}], "style": "modern", "floors": 1}

def generate_floor_plan(data: dict) -> str:
    fig, ax = plt.subplots(figsize=(12, 10), facecolor='white')
    colors = {"living": "#FFD700", "bedroom": "#87CEEB", "kitchen": "#FFA07A", "bathroom": "#DDA0DD"}
    total_rooms = sum([r["count"] for r in data["rooms"]])
    cols = math.ceil(math.sqrt(total_rooms))
    rows = math.ceil(total_rooms / cols)
    cell_w = math.sqrt(data["total_area"] / total_rooms)
    cell_h = cell_w
    idx = 0
    for room in data["rooms"]:
        for i in range(room["count"]):
            row = idx // cols
            col = idx % cols
            rect = patches.Rectangle((col * cell_w, row * cell_h), cell_w, cell_h, linewidth=2, edgecolor='black', facecolor=colors.get(room["type"], "#E8E8E8"), alpha=0.7)
            ax.add_patch(rect)
            ax.text(col * cell_w + cell_w/2, row * cell_h + cell_h/2, room["type"], ha='center', va='center', fontsize=10, weight='bold')
            idx += 1
    ax.set_xlim(-1, cols * cell_w + 1)
    ax.set_ylim(-1, rows * cell_h + 1)
    ax.set_aspect('equal')
    ax.set_title(f"Floor Plan - {data['style']} | {data['total_area']}m²", fontsize=14)
    filename = f"floor_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    return filename

def generate_facade(data: dict) -> str:
    img = Image.new('RGB', (1200, 800), color='#2C3E50')
    draw = ImageDraw.Draw(img)
    draw.rectangle([150, 150, 1050, 700], outline='white', width=3)
    width = 900
    start_x = 150
    start_y = 150
    col_width = width // 3
    for i in range(3):
        x = start_x + i * col_width + col_width//4
        draw.rectangle([x, start_y + 50, x + col_width//2, start_y + 550], outline='white', width=2)
    draw.rectangle([start_x + width//2 - 80, start_y + 530, start_x + width//2 + 80, start_y + 680], outline='white', width=3)
    draw.line([start_x, start_y, start_x + width//2, start_y - 80, start_x + width, start_y], fill='white', width=4)
    draw.text((600, 50), f"{data['style'].upper()} FACADE", fill='white', anchor='mm')
    filename = f"facade_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(filename)
    return filename

def generate_3d(data: dict) -> str:
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    total_rooms = sum([r["count"] for r in data["rooms"]])
    cols = math.ceil(math.sqrt(total_rooms))
    rows = math.ceil(total_rooms / cols)
    cell_w = 10
    cell_d = 10
    height = 5
    idx = 0
    for room in data["rooms"]:
        for i in range(room["count"]):
            row = idx // cols
            col = idx % cols
            x = col * cell_w
            y = row * cell_d
            xx = [x, x, x+cell_w, x+cell_w, x]
            yy = [y, y+cell_d, y+cell_d, y, y]
            zz = [0, 0, 0, 0, 0]
            ax.plot3D(xx, yy, zz, 'blue')
            zz_top = [height, height, height, height, height]
            ax.plot3D(xx, yy, zz_top, 'blue')
            for cx, cy in [(x, y), (x+cell_w, y), (x+cell_w, y+cell_d), (x, y+cell_d)]:
                ax.plot3D([cx, cx], [cy, cy], [0, height], 'blue')
            idx += 1
    ax.set_xlabel('Width (m)')
    ax.set_ylabel('Depth (m)')
    ax.set_zlabel('Height (m)')
    ax.set_title(f'3D Model - {data["style"]}')
    filename = f"3d_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    return filename

def get_main_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏗️ تصميم جديد", callback_data="new")], [InlineKeyboardButton("❓ مساعدة", callback_data="help")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🏗️ *مرحباً بك في {BOT_USERNAME}*\nأرسل وصف المبنى وسأصممه لك!\nمثال: بيت 120 متر، 3 غرف نوم، صالة، مطبخ، حمامين، نمط حديث", reply_markup=get_main_keyboard())

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "new":
        await query.edit_message_text("📝 أرسل وصف المبنى:", reply_markup=get_main_keyboard())
        context.user_data['waiting'] = True
    elif query.data == "help":
        await query.edit_message_text("أرسل وصفاً مفصلاً للمبنى (مساحة، غرف، نمط)")

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting'):
        return
    text = update.message.text
    await update.message.reply_text("🎨 جاري التصميم...")
    data = extract_building_data(text)
    floor_plan = generate_floor_plan(data)
    facade = generate_facade(data)
    model_3d = generate_3d(data)
    with open(floor_plan, 'rb') as f:
        await update.message.reply_photo(f, caption=f"📐 مخطط 2D\n{text[:100]}")
    with open(facade, 'rb') as f:
        await update.message.reply_photo(f, caption="🏛️ الواجهة")
    with open(model_3d, 'rb') as f:
        await update.message.reply_photo(f, caption="🏗️ نموذج 3D")
    os.remove(floor_plan)
    os.remove(facade)
    os.remove(model_3d)
    context.user_data['waiting'] = False

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting'):
        await generate(update, context)
    else:
        await update.message.reply_text("اضغط على زر 'تصميم جديد' للبدء", reply_markup=get_main_keyboard())

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print(f"✅ {BOT_USERNAME} يعمل...")
    app.run_polling()

if __name__ == "__main__":
    main()
