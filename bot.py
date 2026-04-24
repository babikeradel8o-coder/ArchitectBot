# بوت التصميم المعماري الاحترافي - نسخة المطاعم
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
import io

# ---------------------- إعدادات البوت -------------------------
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

    المطلوب:
    {{
        "total_area": 180-300,
        "location": "على ضفاف نهر (إطلالة مباشرة على النيل)",
        "style": "Modern, Elegant, Luxury",
        "zones": {{
            "entrance": {{"width": 3, "length": 4, "name": "مدخل رئيسي"}},
            "reception": {{"width": 4, "length": 5, "name": "منطقة استقبال"}},
            "indoor_dining": {{"width": 12, "length": 15, "capacity": 50, "name": "صالة طعام داخلية"}},
            "outdoor_dining": {{"width": 10, "length": 12, "capacity": 30, "name": "جلسة خارجية على النيل"}},
            "bar": {{"width": 5, "length": 6, "name": "بار/كافيه"}},
            "kitchen": {{"width": 6, "length": 8, "name": "مطبخ"}},
            "toilets": {{"width": 3, "length": 5, "name": "دورات مياه"}},
            "storage": {{"width": 3, "length": 4, "name": "مخزن"}},
            "staff": {{"width": 3, "length": 4, "name": "منطقة خدمة موظفين"}}
        }},
        "special_features": ["واجهة زجاجية على النيل", "مظلات", "برجولات", "مسارات خدمة منفصلة"]
    }}

    أخرج JSON فقط، بدون أي نص إضافي.
    """
    try:
        response = model.generate_content(prompt)
        json_text = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(json_text)
    except:
        return {
            "total_area": 250,
            "style": "Modern Luxury",
            "zones": {
                "entrance": {"width": 3, "length": 4, "name": "مدخل رئيسي"},
                "reception": {"width": 4, "length": 5, "name": "منطقة استقبال"},
                "indoor_dining": {"width": 12, "length": 15, "capacity": 50, "name": "صالة طعام داخلية"},
                "outdoor_dining": {"width": 10, "length": 12, "capacity": 30, "name": "جلسة خارجية على النيل"},
                "bar": {"width": 5, "length": 6, "name": "بار/كافيه"},
                "kitchen": {"width": 6, "length": 8, "name": "مطبخ"},
                "toilets": {"width": 3, "length": 5, "name": "دورات مياه"},
                "storage": {"width": 3, "length": 4, "name": "مخزن"},
                "staff": {"width": 3, "length": 4, "name": "منطقة خدمة موظفين"}
            }
        }

# ---------------------- توليد مخطط 2D احترافي للمطعم -------------------------
def generate_restaurant_floor_plan(data: dict) -> str:
    width = 1200
    height = 900
    img = Image.new('RGB', (width, height), color='#F5F5F0')
    draw = ImageDraw.Draw(img)
    
    # أركان المخطط الأساسية
    start_x = 100
    start_y = 100
    zone_width = 1000
    zone_height = 700
    
    # رسم الجدران الخارجية
    draw.rectangle([start_x, start_y, start_x + zone_width, start_y + zone_height], outline='black', width=3)
    
    # تقسيم المناطق
    zones = data.get('zones', {})
    
    # الألوان حسب المنطقة
    colors = {
        "entrance": "#FFD966",
        "reception": "#FFB347",
        "indoor_dining": "#A4C2F4",
        "outdoor_dining": "#B6D7A8",
        "bar": "#F9CB9C",
        "kitchen": "#D5A6BD",
        "toilets": "#CFE2F3",
        "storage": "#EA9999",
        "staff": "#D9D9D9"
    }
    
    # توزيع المناطق على الشبكة
    positions = {
        "entrance": (100, 800, 150, 150),
        "reception": (250, 780, 120, 150),
        "indoor_dining": (100, 150, 500, 600),
        "outdoor_dining": (600, 150, 500, 400),
        "bar": (600, 550, 250, 200),
        "kitchen": (850, 550, 250, 200),
        "toilets": (100, 600, 100, 150),
        "storage": (200, 600, 100, 150),
        "staff": (750, 750, 150, 100)
    }
    
    # رسم كل منطقة
    for zone_id, (x, y, w, h) in positions.items():
        zone_data = zones.get(zone_id, {})
        name = zone_data.get('name', zone_id)
        color = colors.get(zone_id, "#E0E0E0")
        
        draw.rectangle([x, y, x + w, y + h], fill=color, outline='black', width=2)
        
        # إضافة النص
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            font = ImageFont.load_default()
        
        draw.text((x + w/2, y + h/2), name, fill='black', anchor='mm', font=font)
        
        # إضافة الأبعاد
        draw.text((x + w/2, y + h - 10), f"{w}×{h}", fill='#555', anchor='mm', font=font)
    
    # إضافة الإطلالة على النيل (واجهة زجاجية)
    for i in range(5):
        x = 620 + i * 90
        draw.rectangle([x, 100, x + 80, 180], fill='#ADD8E6', outline='blue', width=2)
    
    # إضافة مسارات الحركة
    draw.line([280, 780, 500, 750], fill='red', width=2)
    draw.line([500, 750, 600, 650], fill='red', width=2)
    draw.line([600, 650, 750, 650], fill='red', width=2)
    
    # إضافة الأثاث (طاولات)
    for row in range(4):
        for col in range(3):
            tx = 150 + col * 140
            ty = 200 + row * 120
            draw.ellipse([tx, ty, tx + 30, ty + 30], fill='#8B4513', outline='black')
    
    # جلسة خارجية (طاولات خارجية)
    for i in range(6):
        ox = 650 + i * 70
        oy = 250
        draw.ellipse([ox, oy, ox + 40, oy + 40], fill='#D2B48C', outline='black')
    
    # عناصر طبيعية (نباتات)
    for i in range(8):
        px = 50 + i * 120
        py = 850
        draw.ellipse([px, py, px + 30, py + 30], fill='#228B22', outline='darkgreen')
    
    # نص البار
    draw.text((700, 600), "🍸 BAR AREA", fill='white', anchor='mm', font=font)
    
    # نص الإطلالة
    draw.text((800, 80), "🌊 NILE VIEW", fill='blue', anchor='mm', font=font)
    
    # وصف المطعم
    desc = f"RESTAURANT FLOOR PLAN\nStyle: {data.get('style', 'Modern Luxury')}\nTotal Area: {data.get('total_area', 250)} m²\nNile Front View"
    draw.text((width/2, height-30), desc, fill='#333', anchor='mm', font=font)
    
    filename = f"restaurant_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(filename)
    return filename

# ---------------------- توليد نموذج 3D -------------------------
def generate_restaurant_3d(data: dict) -> str:
    width = 1200
    height = 800
    img = Image.new('RGB', (width, height), color='#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    # واجهة زجاجية مطلة على النيل
    draw.rectangle([200, 200, 800, 600], fill='#ADD8E6', outline='white', width=3)
    
    # بناء المطعم
    draw.rectangle([150, 150, 850, 650], fill='#4a4a4a', outline='white', width=2)
    
    # سقف (مظلات)
    draw.polygon([(150, 150), (500, 80), (850, 150)], fill='#A0A0A0', outline='white')
    
    # نوافذ زجاجية
    for i in range(4):
        x = 250 + i * 150
        draw.rectangle([x, 250, x + 120, 500], fill='#87CEEB', outline='white', width=2)
    
    # برجولات خارجية
    draw.line([150, 650, 850, 650], fill='#D2B48C', width=5)
    
    for i in range(5):
        px = 180 + i * 170
        draw.rectangle([px, 650, px + 10, 700], fill='#D2B48C')
    
    # منطقة خارجية
    for i in range(6):
        ox = 200 + i * 120
        draw.ellipse([ox, 680, ox + 40, 720], fill='#D2B48C', outline='white')
    
    # نباتات وزينة
    for i in range(5):
        px = 100 + i * 200
        draw.ellipse([px, 730, px + 40, 770], fill='#228B22')
    
    # نص توضيحي
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    draw.text((width/2, 60), "🌊 RESTAURANT 3D VIEW - NILE FRONT 🌊", fill='white', anchor='mm', font=font)
    draw.text((width/2, height - 40), f"{BOT_USERNAME} | {DEVELOPER_NAME}", fill='#888', anchor='mm', font=font)
    
    filename = f"restaurant_3d_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(filename)
    return filename

# ---------------------- أزرار البوت -------------------------
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🍽️ تصميم مطعم", callback_data="restaurant")],
        [InlineKeyboardButton("🏢 تصميم عمارة", callback_data="building")],
        [InlineKeyboardButton("📐 معايير التصميم", callback_data="standards")],
        [InlineKeyboardButton("❓ تعليمات", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🏛️ *بوت التصميم المعماري الاحترافي*\n"
        f"🎓 *{BOT_USERNAME}*\n\n"
        f"📌 *أرسل وصف المطعم أو المبنى*\n\n"
        f"🍽️ *مثال تصميم مطعم:*\n"
        f"مطعم على ضفاف النيل، 250 متر، صالة داخلية 50 شخص، جلسة خارجية، بار، مطبخ، إطلالة زجاجية\n\n"
        f"👨‍💻 {DEVELOPER_NAME}",
        reply_markup=get_main_keyboard()
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "restaurant":
        await query.edit_message_text(
            "🍽️ *أرسل وصف المطعم*\n\n"
            "مثال:\n"
            "مطعم على ضفاف النيل، مساحة 250 متر، صالة داخلية 50 شخص، جلسة خارجية على الماء، بار، مطبخ، مخزن، حمامات، إطلالة زجاجية، نمط حديث فاخر",
            reply_markup=get_main_keyboard()
        )
        context.user_data['mode'] = 'restaurant'
    
    elif data == "building":
        await query.edit_message_text(
            "🏢 *أرسل وصف المبنى*\n\n"
            "مثال:\n"
            "بيت 150 متر، 3 غرف نوم، صالة، مطبخ، حمامين، نمط حديث",
            reply_markup=get_main_keyboard()
        )
        context.user_data['mode'] = 'building'
    
    elif data == "standards":
        text = "📐 *المعايير القياسية للمطاعم*\n\n"
        text += "• صالة داخلية: 50-100 متر مربع\n"
        text += "• جلسة خارجية: 30-60 متر مربع\n"
        text += "• مطبخ: 20-40 متر مربع\n"
        text += "• بار: 15-25 متر مربع\n"
        text += "• مخزن: 10-15 متر مربع\n"
        text += "• ممرات حركة: 120-150 سم\n"
        text += "• إطلالة على النيل: واجهة زجاجية كاملة"
        await query.edit_message_text(text, reply_markup=get_main_keyboard())
    
    elif data == "help":
        await query.edit_message_text(
            "📖 *التعليمات*\n\n"
            "1️⃣ اختر 'تصميم مطعم' أو 'تصميم عمارة'\n"
            "2️⃣ أرسل وصفاً مفصلاً\n"
            "3️⃣ سأقوم بتوليد:\n"
            "   - مخطط 2D مفصل\n"
            "   - نموذج 3D واقعي\n"
            "   - واجهات معمارية\n\n"
            "🍽️ *مثال مطعم:*\n"
            "مطعم على النيل، 250 متر، صالة داخلية 50 شخص، جلسة خارجية، بار، مطبخ",
            reply_markup=get_main_keyboard()
        )

async def handle_restaurant_design(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('mode') != 'restaurant':
        return
    
    text = update.message.text
    await update.message.reply_text("🍽️ *جاري تصميم المطعم...*\n⏳ سيتم توليد مخطط 2D + نموذج 3D")
    
    data = extract_restaurant_data(text)
    
    floor_plan = generate_restaurant_floor_plan(data)
    model_3d = generate_restaurant_3d(data)
    
    with open(floor_plan, 'rb') as f:
        await update.message.reply_photo(f, caption=f"📐 مخطط المطعم 2D\n{text[:100]}")
    
    with open(model_3d, 'rb') as f:
        await update.message.reply_photo(f, caption="🏗️ نموذج ثلاثي الأبعاد\n🌊 إطلالة على النيل")
    
    os.remove(floor_plan)
    os.remove(model_3d)
    context.user_data['mode'] = None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get('mode')
    
    if mode == 'restaurant':
        await handle_restaurant_design(update, context)
    else:
        await update.message.reply_text(
            "🏛️ *اختر نوع التصميم أولاً*\n\n"
            "🍽️ مطعم\n"
            "🏢 عمارة",
            reply_markup=get_main_keyboard()
        )

# ---------------------- التشغيل -------------------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("=" * 60)
    print(f"✅ {BOT_USERNAME} - بوت تصميم المطاعم")
    print(f"🍽️ يدعم تصميم مطاعم على ضفاف النيل")
    print("=" * 60)
    app.run_polling()

if __name__ == "__main__":
    main()
