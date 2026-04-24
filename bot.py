# بوت التصميم المعماري الاحترافي - النسخة النهائية المستقرة
# المطور: بكري بيس

import os
import json
import re
import math
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# ---------------------- إعدادات -------------------------
BOT_TOKEN = "7933927887:AAEK-uYKwa0T2X6bK5hIlO-DdAgOHy09Gvg"
GEMINI_API_KEY = "AIzaSyBqv5YfBlsQsJCyvz56TaA-tUXr26c6-Ow"
DEVELOPER_NAME = "بكري بيس"
BOT_USERNAME = "@BakriArchBot"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# ---------------------- تحليل الطلب -------------------------
def extract_restaurant_data(text: str) -> dict:
    prompt = f"""
    أنت مهندس معماري خبير في تصميم المطاعم. قم بتحليل طلب المستخدم التالي واستخرج البيانات التالية في JSON:

    الطلب: {text}

    أخرج JSON فقط بهذا الشكل:
    {{
        "total_area": عدد بين 180-300,
        "style": "نمط التصميم",
        "indoor_capacity": عدد,
        "outdoor_capacity": عدد,
        "has_bar": true/false,
        "has_nile_view": true/false
    }}
    """
    try:
        response = model.generate_content(prompt)
        json_text = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(json_text)
    except:
        return {
            "total_area": 250,
            "style": "Modern Luxury",
            "indoor_capacity": 50,
            "outdoor_capacity": 30,
            "has_bar": True,
            "has_nile_view": True
        }

# ---------------------- توليد مخطط 2D -------------------------
def generate_floor_plan(data: dict) -> str:
    width = 1000
    height = 800
    img = Image.new('RGB', (width, height), color='#F5F5F0')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        font = ImageFont.load_default()
        font_big = ImageFont.load_default()
    
    # الجدران الخارجية
    draw.rectangle([50, 50, 950, 750], outline='black', width=3)
    
    # إطلالة على النيل (واجهة زجاجية)
    for i in range(8):
        x = 70 + i * 110
        draw.rectangle([x, 50, x + 100, 200], fill='#ADD8E6', outline='blue', width=2)
    
    draw.text((500, 120), "🌊 NILE VIEW (Panoramic Glass)", fill='blue', anchor='mm', font=font_big)
    
    # صالة داخلية
    draw.rectangle([70, 250, 600, 700], fill='#A4C2F4', outline='black', width=2)
    draw.text((335, 475), "INDOOR DINING", fill='black', anchor='mm', font=font_big)
    draw.text((335, 505), f"Capacity: {data.get('indoor_capacity', 50)} seats", fill='black', anchor='mm', font=font)
    
    # طاولات داخلية
    for row in range(3):
        for col in range(3):
            tx = 120 + col * 160
            ty = 300 + row * 130
            draw.ellipse([tx, ty, tx + 40, ty + 40], fill='#8B4513', outline='black')
            draw.text((tx + 20, ty + 20), str(4), fill='white', anchor='mm', font=font)
    
    # جلسة خارجية
    draw.rectangle([620, 250, 920, 550], fill='#B6D7A8', outline='black', width=2)
    draw.text((770, 400), "OUTDOOR DINING", fill='black', anchor='mm', font=font_big)
    draw.text((770, 430), f"Capacity: {data.get('outdoor_capacity', 30)} seats", fill='black', anchor='mm', font=font)
    
    # طاولات خارجية
    for i in range(4):
        ox = 660 + i * 70
        oy = 300
        draw.ellipse([ox, oy, ox + 50, oy + 50], fill='#D2B48C', outline='black')
    
    # بار
    if data.get('has_bar', True):
        draw.rectangle([620, 570, 920, 700], fill='#F9CB9C', outline='black', width=2)
        draw.text((770, 635), "🍸 BAR AREA", fill='black', anchor='mm', font=font_big)
    
    # مطبخ
    draw.rectangle([70, 550, 250, 700], fill='#D5A6BD', outline='black', width=2)
    draw.text((160, 625), "KITCHEN", fill='black', anchor='mm', font=font_big)
    
    # حمامات
    draw.rectangle([270, 550, 370, 650], fill='#CFE2F3', outline='black', width=2)
    draw.text((320, 600), "TOILETS", fill='black', anchor='mm', font=font)
    
    # مخزن
    draw.rectangle([390, 550, 490, 650], fill='#EA9999', outline='black', width=2)
    draw.text((440, 600), "STORAGE", fill='black', anchor='mm', font=font)
    
    # منطقة خدمة
    draw.rectangle([510, 550, 600, 650], fill='#D9D9D9', outline='black', width=2)
    draw.text((555, 600), "STAFF", fill='black', anchor='mm', font=font)
    
    # مسارات الحركة
    draw.line([70, 720, 920, 720], fill='red', width=2)
    draw.text((500, 735), "Main Circulation Path", fill='red', anchor='mm', font=font)
    
    # نباتات وزينة
    for i in range(6):
        px = 40 + i * 160
        draw.ellipse([px, 740, px + 30, 770], fill='#228B22')
    
    # نص سفلي
    draw.text((500, 790), f"{BOT_USERNAME} | {DEVELOPER_NAME} | Area: {data.get('total_area', 250)} m²", fill='#333', anchor='mm', font=font)
    
    filename = f"floor_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(filename)
    return filename

# ---------------------- توليد 3D -------------------------
def generate_3d_view(data: dict) -> str:
    width = 1000
    height = 700
    img = Image.new('RGB', (width, height), color='#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font = ImageFont.load_default()
        font_big = ImageFont.load_default()
    
    # بناء المطعم
    draw.rectangle([150, 150, 850, 550], fill='#4a4a4a', outline='white', width=3)
    
    # واجهة زجاجية
    for i in range(5):
        x = 180 + i * 140
        draw.rectangle([x, 180, x + 120, 450], fill='#87CEEB', outline='white', width=2)
    
    # سقف
    draw.polygon([(150, 150), (500, 80), (850, 150)], fill='#A0A0A0', outline='white')
    
    # برجولات
    draw.line([150, 550, 850, 550], fill='#D2B48C', width=5)
    for i in range(5):
        px = 180 + i * 170
        draw.rectangle([px, 550, px + 10, 600], fill='#D2B48C')
    
    # جلسة خارجية
    for i in range(6):
        ox = 200 + i * 100
        draw.ellipse([ox, 580, ox + 50, 630], fill='#D2B48C', outline='white')
    
    # إطلالة النيل (خلفية)
    draw.rectangle([150, 450, 850, 550], fill='#4169E1')
    for i in range(10):
        wx = 200 + i * 70
        draw.ellipse([wx, 480, wx + 30, 510], fill='white')
    
    # نباتات
    for i in range(6):
        px = 60 + i * 150
        draw.ellipse([px, 620, px + 40, 660], fill='#228B22')
    
    # نصوص
    draw.text((500, 50), "RESTAURANT 3D VIEW", fill='white', anchor='mm', font=font_big)
    draw.text((500, 90), "Nile Front - Panoramic Glass Facade", fill='#aaa', anchor='mm', font=font)
    draw.text((500, 680), f"{BOT_USERNAME} | {DEVELOPER_NAME}", fill='#666', anchor='mm', font=font)
    
    filename = f"3d_view_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(filename)
    return filename

# ---------------------- أزرار البوت -------------------------
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🍽️ تصميم مطعم", callback_data="restaurant")],
        [InlineKeyboardButton("❓ تعليمات", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🏛️ *بوت التصميم المعماري*\n"
        f"🎓 *{BOT_USERNAME}*\n\n"
        f"🍽️ *أرسل وصف المطعم*\n\n"
        f"مثال:\n"
        f"مطعم على النيل، 250 متر، صالة داخلية 50 شخص، جلسة خارجية، بار، مطبخ\n\n"
        f"👨‍💻 {DEVELOPER_NAME}",
        reply_markup=get_main_keyboard()
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "restaurant":
        try:
            await query.edit_message_text(
                "🍽️ *أرسل وصف المطعم*\n\n"
                "مثال: مطعم على النيل، 250 متر، صالة داخلية 50 شخص، جلسة خارجية، بار، مطبخ، إطلالة زجاجية",
                reply_markup=get_main_keyboard()
            )
        except:
            await query.message.reply_text(
                "🍽️ *أرسل وصف المطعم*",
                reply_markup=get_main_keyboard()
            )
        context.user_data['mode'] = 'restaurant'
    
    elif query.data == "help":
        try:
            await query.edit_message_text(
                "📖 *التعليمات*\n\n"
                "1️⃣ اضغط 'تصميم مطعم'\n"
                "2️⃣ أرسل وصف المطعم\n"
                "3️⃣ ستحصل على مخطط 2D + نموذج 3D",
                reply_markup=get_main_keyboard()
            )
        except:
            await query.message.reply_text(
                "📖 *التعليمات*\n\nاضغط 'تصميم مطعم' ثم أرسل الوصف",
                reply_markup=get_main_keyboard()
            )

async def handle_restaurant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('mode') != 'restaurant':
        await update.message.reply_text("🍽️ اضغط على 'تصميم مطعم' أولاً", reply_markup=get_main_keyboard())
        return
    
    text = update.message.text
    await update.message.reply_text("🎨 *جاري تصميم المطعم...*\n⏳ يرجى الانتظار")
    
    data = extract_restaurant_data(text)
    
    floor_plan = generate_floor_plan(data)
    view_3d = generate_3d_view(data)
    
    with open(floor_plan, 'rb') as f:
        await update.message.reply_photo(f, caption=f"📐 مخطط 2D للمطعم\n{text[:100]}")
    
    with open(view_3d, 'rb') as f:
        await update.message.reply_photo(f, caption="🏗️ نموذج 3D - إطلالة على النيل")
    
    os.remove(floor_plan)
    os.remove(view_3d)
    context.user_data['mode'] = None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('mode') == 'restaurant':
        await handle_restaurant(update, context)
    else:
        await update.message.reply_text("🍽️ اضغط على 'تصميم مطعم' للبدء", reply_markup=get_main_keyboard())

# ---------------------- التشغيل -------------------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("=" * 60)
    print(f"✅ {BOT_USERNAME} يعمل...")
    print("🍽️ بوت تصميم المطاعم على النيل")
    print("=" * 60)
    app.run_polling()

if __name__ == "__main__":
    main()
