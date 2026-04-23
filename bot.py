# بوت التصميم المعماري الاحترافي - الإصدار النهائي المصحح
# المطور: بكري بيس

import os
import json
import re
import math
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
from PIL import Image
import io

# ===================== إعدادات البوت =====================
BOT_TOKEN = "7933927887:AAEK-uYKwa0T2X6bK5hIlO-DdAgOHy09Gvg"
GEMINI_API_KEY = "AIzaSyBqv5YfBlsQsJCyvz56TaA-tUXr26c6-Ow"
DEVELOPER_NAME = "بكري بيس"
BOT_USERNAME = "@BakriArchBot"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash-exp")
vision_model = genai.GenerativeModel("gemini-2.0-flash-exp")

# ===================== القواعد الهندسية العالمية =====================
ROOM_STANDARDS = {
    "living": {"min_width": 4, "max_width": 8, "min_length": 5, "max_length": 10, "min_area": 20, "name_ar": "صالة"},
    "master_bedroom": {"min_width": 4, "max_width": 6, "min_length": 5, "max_length": 7, "min_area": 20, "name_ar": "غرفة نوم رئيسية"},
    "bedroom": {"min_width": 3, "max_width": 4.5, "min_length": 4, "max_length": 6, "min_area": 12, "name_ar": "غرفة نوم"},
    "kitchen": {"min_width": 3, "max_width": 5, "min_length": 4, "max_length": 6, "min_area": 12, "name_ar": "مطبخ"},
    "bathroom": {"min_width": 1.8, "max_width": 2.5, "min_length": 2, "max_length": 3, "min_area": 3.6, "name_ar": "حمام"}
}

STYLES = {
    "modern": "حديث - خطوط نظيفة، نوافذ كبيرة",
    "classic": "كلاسيكي - أعمدة وتفاصيل زخرفية",
    "islamic": "إسلامي - عقود وزخارف هندسية",
    "minimalist": "بسيط - أقل تفاصيل ومساحات مفتوحة"
}

# ===================== دوال البوت =====================
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🏗️ تصميم جديد", callback_data="new_text")],
        [InlineKeyboardButton("📐 معايير الغرف", callback_data="standards")],
        [InlineKeyboardButton("🎨 أنماط التصميم", callback_data="styles")],
        [InlineKeyboardButton("ℹ️ تعليمات", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def extract_building_data(text: str) -> dict:
    prompt = f"""
    استخرج معلومات البناء من النص التالي. أخرج JSON فقط:
    {{
        "total_area": عدد,
        "rooms": [
            {{"type": "living|master_bedroom|bedroom|kitchen|bathroom", "count": عدد, "width": عدد, "length": عدد}}
        ],
        "style": "modern|classic|islamic|minimalist",
        "floors": عدد
    }}
    النص: {text}
    """
    try:
        response = model.generate_content(prompt)
        json_text = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(json_text)
    except:
        return {
            "total_area": 120,
            "rooms": [
                {"type": "living", "count": 1, "width": 6, "length": 7},
                {"type": "master_bedroom", "count": 1, "width": 5, "length": 6},
                {"type": "bedroom", "count": 2, "width": 4, "length": 5},
                {"type": "kitchen", "count": 1, "width": 4, "length": 5},
                {"type": "bathroom", "count": 2, "width": 2, "length": 3}
            ],
            "style": "modern",
            "floors": 1
        }

def generate_svg_floor_plan(data: dict) -> str:
    rooms = []
    total_rooms_count = sum(room['count'] for room in data['rooms'])
    cols = min(4, max(2, math.ceil(math.sqrt(total_rooms_count))))
    rows = math.ceil(total_rooms_count / cols)
    cell_w = 150
    cell_h = 150

    idx = 0
    for room in data['rooms']:
        for _ in range(room['count']):
            row = idx // cols
            col = idx % cols
            width = room.get('width', 4) * 20
            length = room.get('length', 5) * 20
            name_ar = ROOM_STANDARDS.get(room['type'], {}).get('name_ar', room['type'])
            rooms.append({
                "type": room['type'],
                "name_ar": name_ar,
                "x": col * cell_w,
                "y": row * cell_h,
                "w": width,
                "h": length
            })
            idx += 1

    total_w = cols * cell_w + 50
    total_h = rows * cell_h + 100

    colors = {
        "living": "#FFD966", "master_bedroom": "#9FC5E8", "bedroom": "#A4C2F4",
        "kitchen": "#F9CB9C", "bathroom": "#D5A6BD"
    }

    svg_content = f'<svg width="{total_w}" height="{total_h}" xmlns="http://www.w3.org/2000/svg" style="background:#F5F5F0;">'
    
    for room in rooms:
        color = colors.get(room['type'], "#E0E0E0")
        svg_content += f'<rect x="{room["x"]}" y="{room["y"]}" width="{room["w"]}" height="{room["h"]}" fill="{color}" stroke="#333" stroke-width="2"/>'
        svg_content += f'<text x="{room["x"] + room["w"]/2}" y="{room["y"] + room["h"]/2}" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="14" font-weight="bold">{room["name_ar"]}</text>'
        svg_content += f'<text x="{room["x"] + room["w"]/2}" y="{room["y"] + room["h"]/2 + 20}" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="10" fill="#555">{room["w"]/20:.1f}×{room["h"]/20:.1f} م</text>'

    svg_content += f'<text x="10" y="{total_h - 20}" font-family="Arial" font-size="14" fill="#333">المساحة: {data.get("total_area", 100)} م² | النمط: {data.get("style", "modern")}</text>'
    svg_content += f'<text x="10" y="{total_h - 5}" font-family="Arial" font-size="10" fill="#666">{BOT_USERNAME} | {DEVELOPER_NAME}</text>'
    svg_content += '</svg>'

    filename = f"floor_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    return filename

def generate_facade_svg(data: dict) -> str:
    style = data.get('style', 'modern')
    svg = f'<svg width="800" height="500" xmlns="http://www.w3.org/2000/svg" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">'
    svg += f'<rect x="50" y="100" width="700" height="350" fill="rgba(255,255,255,0.9)" stroke="#333" stroke-width="3" rx="10"/>'
    svg += f'<rect x="100" y="150" width="180" height="220" fill="rgba(200,220,240,0.8)" stroke="#333" stroke-width="2" rx="5"/>'
    svg += f'<rect x="310" y="130" width="180" height="260" fill="rgba(200,220,240,0.8)" stroke="#333" stroke-width="2" rx="5"/>'
    svg += f'<rect x="520" y="150" width="180" height="220" fill="rgba(200,220,240,0.8)" stroke="#333" stroke-width="2" rx="5"/>'
    svg += f'<rect x="350" y="420" width="100" height="30" fill="#8B7355" stroke="#333" stroke-width="2" rx="10"/>'
    svg += f'<text x="400" y="60" text-anchor="middle" font-family="Arial" font-size="24" font-weight="bold" fill="white">واجهة {style}</text>'
    svg += f'<text x="400" y="480" text-anchor="middle" font-family="Arial" font-size="12" fill="white">© {DEVELOPER_NAME}</text>'
    svg += '</svg>'
    
    filename = f"facade_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(svg)
    return filename

def generate_3d_svg(data: dict) -> str:
    floors = data.get('floors', 1)
    height = 350 + (floors - 1) * 80
    svg = f'<svg width="800" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);">'
    svg += f'<polygon points="200,{height-80} 400,{height-80} 400,{height-40} 200,{height-40}" fill="#4a4a4a" stroke="#fff" stroke-width="2"/>'
    svg += f'<polygon points="400,{height-80} 600,{height-80} 600,{height-40} 400,{height-40}" fill="#3a3a3a" stroke="#fff" stroke-width="2"/>'
    svg += f'<polygon points="200,200 400,160 600,200 400,200" fill="#5a5a5a" stroke="#fff" stroke-width="2"/>'
    svg += f'<polygon points="200,200 400,200 400,{height-80} 200,{height-80}" fill="#6a6a6a" stroke="#fff" stroke-width="2"/>'
    svg += f'<polygon points="400,160 600,200 600,{height-80} 400,{height-80}" fill="#5a5a5a" stroke="#fff" stroke-width="2"/>'
    svg += f'<text x="400" y="100" text-anchor="middle" font-family="Arial" font-size="22" font-weight="bold" fill="#fff">نموذج ثلاثي الأبعاد</text>'
    svg += f'<text x="400" y="130" text-anchor="middle" font-family="Arial" font-size="14" fill="#aaa">{data.get("total_area", 100)} م² | {floors} دور</text>'
    svg += '</svg>'
    
    filename = f"3d_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(svg)
    return filename

# ===================== معالجات البوت =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🏛️ *بوت التصميم المعماري الاحترافي*\n"
        f"🎓 *{BOT_USERNAME}*\n\n"
        f"📌 أرسل وصف المبنى وسأصممه لك!\n"
        f"مثال: بيت 120 متر، 3 غرف نوم، صالة، مطبخ، حمامين، نمط حديث\n\n"
        f"👨‍💻 {DEVELOPER_NAME}",
        reply_markup=get_main_keyboard()
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "new_text":
        await query.edit_message_text("📝 أرسل وصف المبنى:", reply_markup=get_main_keyboard())
        context.user_data['mode'] = 'text'
    elif data == "standards":
        text = "📐 *المعايير القياسية للغرف*\n\n"
        for key, std in ROOM_STANDARDS.items():
            text += f"• *{std['name_ar']}*: {std['min_width']}-{std['max_width']} × {std['min_length']}-{std['max_length']} م\n"
        await query.edit_message_text(text, reply_markup=get_main_keyboard())
    elif data == "styles":
        text = "🎨 *أنماط التصميم*\n\n"
        for key, desc in STYLES.items():
            text += f"• *{key}*: {desc}\n"
        await query.edit_message_text(text, reply_markup=get_main_keyboard())
    elif data == "help":
        await query.edit_message_text(
            "📖 *التعليمات*\n\n"
            "1️⃣ اكتب وصف المبنى\n"
            "2️⃣ سأقوم بتوليد:\n"
            "   - مخطط 2D\n"
            "   - واجهة معمارية\n"
            "   - نموذج 3D\n\n"
            "مثال: بيت 150 متر، 3 غرف، صالة، مطبخ، حمامين",
            reply_markup=get_main_keyboard()
        )

async def handle_text_design(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('mode') != 'text':
        await update.message.reply_text("🏛️ اضغط على 'تصميم جديد' أولاً", reply_markup=get_main_keyboard())
        return
    
    text = update.message.text
    await update.message.reply_text("🎨 *جاري التصميم...*")
    
    data = extract_building_data(text)
    floor_plan = generate_svg_floor_plan(data)
    facade = generate_facade_svg(data)
    model_3d = generate_3d_svg(data)
    
    with open(floor_plan, 'rb') as f:
        await update.message.reply_document(f, filename=floor_plan, caption=f"📐 المخطط 2D")
    with open(facade, 'rb') as f:
        await update.message.reply_document(f, filename=facade, caption="🏛️ الواجهة")
    with open(model_3d, 'rb') as f:
        await update.message.reply_document(f, filename=model_3d, caption="🏗️ النموذج 3D")
    
    os.remove(floor_plan)
    os.remove(facade)
    os.remove(model_3d)
    context.user_data['mode'] = None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get('mode')
    
    if mode == 'text':
        await handle_text_design(update, context)
    else:
        await update.message.reply_text("🏛️ اضغط على 'تصميم جديد' للبدء", reply_markup=get_main_keyboard())

# ===================== التشغيل =====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("=" * 60)
    print(f"✅ {BOT_USERNAME} يعمل...")
    print("=" * 60)
    app.run_polling()

if __name__ == "__main__":
    main()
