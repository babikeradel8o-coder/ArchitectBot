# بوت التصميم المعماري الاحترافي - الإصدار النهائي
# المطور: بكري بيس
# يشمل: توليد مخططات 2D، واجهات، نماذج 3D، تحليل الصور، معايير عالمية

import os
import json
import re
import math
import base64
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

# تهيئة الذكاء الاصطناعي
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash-exp")
vision_model = genai.GenerativeModel("gemini-2.0-flash-exp")

# ===================== القواعد الهندسية العالمية =====================
ROOM_STANDARDS = {
    "living": {"min_width": 4, "max_width": 8, "min_length": 5, "max_length": 10, "min_area": 20, "name_ar": "صالة"},
    "master_bedroom": {"min_width": 4, "max_width": 6, "min_length": 5, "max_length": 7, "min_area": 20, "name_ar": "غرفة نوم رئيسية"},
    "bedroom": {"min_width": 3, "max_width": 4.5, "min_length": 4, "max_length": 6, "min_area": 12, "name_ar": "غرفة نوم"},
    "kitchen": {"min_width": 3, "max_width": 5, "min_length": 4, "max_length": 6, "min_area": 12, "name_ar": "مطبخ"},
    "bathroom": {"min_width": 1.8, "max_width": 2.5, "min_length": 2, "max_length": 3, "min_area": 3.6, "name_ar": "حمام"},
    "dining": {"min_width": 3, "max_width": 5, "min_length": 4, "max_length": 6, "min_area": 12, "name_ar": "غرفة طعام"},
    "hall": {"min_width": 2, "max_width": 4, "min_length": 3, "max_length": 6, "min_area": 6, "name_ar": "ممر"},
    "study": {"min_width": 3, "max_width": 4, "min_length": 4, "max_length": 5, "min_area": 12, "name_ar": "مكتب"},
    "gym": {"min_width": 4, "max_width": 6, "min_length": 5, "max_length": 8, "min_area": 20, "name_ar": "صالة رياضية"},
    "storage": {"min_width": 1.5, "max_width": 2.5, "min_length": 2, "max_length": 3, "min_area": 3, "name_ar": "مخزن"}
}

STYLES = {
    "modern": "حديث - خطوط نظيفة، نوافذ كبيرة، أسطح مسطحة",
    "classic": "كلاسيكي - أعمدة، تفاصيل زخرفية، أسقف مرتفعة",
    "islamic": "إسلامي - عقود، زخارف هندسية، مشربيات",
    "minimalist": "بسيط - أقل تفاصيل، مساحات مفتوحة، ألوان محايدة",
    "contemporary": "معاصر - مزيج من الحداثة والكلاسيكية",
    "industrial": "صناعي - خرسانة مكشوفة، معادن، نوافذ كبيرة"
}

# ===================== تحليل المخططات من الصور =====================
async def analyze_image(image_bytes: bytes) -> dict:
    """تحليل صورة المخطط واستخراج البيانات بشكل احترافي"""
    image = Image.open(io.BytesIO(image_bytes))
    
    prompt = """
    أنت مهندس معماري خبير. قم بتحليل مخطط المنزل في الصورة واستخرج المعلومات التالية بدقة:
    
    1. المساحة التقريبية للمنزل بالمتر المربع
    2. جميع الغرف الموجودة مع أنواعها وأبعادها التقريبية
    3. النمط المعماري
    4. عدد الأدوار
    
    استخدم المعايير القياسية:
    - غرفة نوم: عرض 3-4.5م، طول 4-6م
    - صالة: عرض 4-8م، طول 5-10م
    - مطبخ: عرض 3-5م، طول 4-6م
    - حمام: عرض 1.8-2.5م، طول 2-3م
    
    أخرج JSON فقط بهذا الشكل الدقيق:
    {
        "total_area": number,
        "rooms": [
            {"type": "living|bedroom|kitchen|bathroom", "count": number, "width": number, "length": number}
        ],
        "style": "string",
        "floors": number
    }
    """
    
    try:
        response = vision_model.generate_content([prompt, image])
        json_text = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(json_text)
    except Exception as e:
        print(f"خطأ في تحليل الصورة: {e}")
        return None

# ===================== تحليل النص الذكي =====================
def extract_building_data(text: str) -> dict:
    """استخراج بيانات البناء من النص باستخدام Gemini"""
    prompt = f"""
    أنت مهندس معماري خبير. قم بتحويل طلب المستخدم إلى JSON ممتاز يصف مخطط المنزل.

    الطلب: {text}

    استخدم القياسات القياسية التالية:
    - صالة: عرض 4-8م، طول 5-10م (مساحة 20-80م²)
    - غرفة نوم رئيسية: عرض 4-6م، طول 5-7م (مساحة 20-42م²)
    - غرفة نوم: عرض 3-4.5م، طول 4-6م (مساحة 12-27م²)
    - مطبخ: عرض 3-5م، طول 4-6م (مساحة 12-30م²)
    - حمام: عرض 1.8-2.5م، طول 2-3م (مساحة 3.6-7.5م²)

    أخرج JSON فقط بهذا الشكل:
    {{
        "total_area": number,
        "rooms": [
            {{"type": "living|master_bedroom|bedroom|kitchen|bathroom|dining", "count": number, "width": number, "length": number}}
        ],
        "style": "modern|classic|islamic|minimalist|contemporary|industrial",
        "floors": number
    }}
    """
    try:
        response = model.generate_content(prompt)
        json_text = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(json_text)
    except:
        return {
            "total_area": 150,
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

# ===================== توليد مخططات SVG احترافية =====================
def generate_svg_floor_plan(data: dict) -> str:
    """توليد مخطط 2D احترافي بتنسيق SVG"""
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
            width = room.get('width', cell_w) * 10
            length = room.get('length', cell_h) * 10
            rooms.append({
                "type": room['type'],
                "name_ar": ROOM_STANDARDS.get(room['type'], {}).get('name_ar', room['type']),
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
        "kitchen": "#F9CB9C", "bathroom": "#D5A6BD", "dining": "#B6D7A8",
        "hall": "#EAD1DC", "study": "#CFE2F3", "gym": "#FCE5CD", "storage": "#D9D9D9"
    }

    svg_content = f'''<svg width="{total_w}" height="{total_h}" xmlns="http://www.w3.org/2000/svg" style="background: #F5F5F0;">
    <defs>
        <style>
            .room-text {{ font-family: 'Arial', sans-serif; font-size: 14px; font-weight: bold; fill: #333; }}
            .dimension {{ font-family: 'Arial', sans-serif; font-size: 11px; fill: #555; }}
            .title {{ font-family: 'Arial', sans-serif; font-size: 16px; font-weight: bold; fill: #2C3E50; }}
            .grid-line {{ stroke: #DDD; stroke-width: 0.5; stroke-dasharray: 4; }}
        </style>
    </defs>
    
    {''.join([f'<line x1="0" y1="{y}" x2="{total_w}" y2="{y}" class="grid-line"/>' for y in range(0, int(total_h), 50)])}
    {''.join([f'<line x1="{x}" y1="0" x2="{x}" y2="{total_h}" class="grid-line"/>' for x in range(0, int(total_w), 50)])}
    '''

    for room in rooms:
        color = colors.get(room['type'], "#E0E0E0")
        svg_content += f'''
    <rect x="{room['x']}" y="{room['y']}" width="{room['w']}" height="{room['h']}" fill="{color}" stroke="#333" stroke-width="2.5" rx="5"/>
    <text x="{room['x'] + room['w']/2}" y="{room['y'] + room['h']/2 - 10}" text-anchor="middle" dominant-baseline="middle" class="room-text">{room['name_ar']}</text>
    <text x="{room['x'] + room['w']/2}" y="{room['y'] + room['h']/2 + 15}" text-anchor="middle" dominant-baseline="middle" class="dimension">{room['w']/10:.1f}×{room['h']/10:.1f} م</text>'''

    svg_content += f'''
    <text x="20" y="{total_h - 30}" class="title">📐 المساحة الكلية: {data.get('total_area', 100)} م²</text>
    <text x="20" y="{total_h - 10}" class="title">🎨 النمط: {STYLES.get(data.get('style', 'modern'), data.get('style', 'modern'))}</text>
    <text x="{total_w - 250}" y="{total_h - 10}" class="dimension">✨ {BOT_USERNAME} | {DEVELOPER_NAME}</text>
</svg>'''

    filename = f"floor_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    return filename

def generate_facade_svg(data: dict) -> str:
    """توليد واجهة معمارية احترافية"""
    style = data.get('style', 'modern')
    floors = data.get('floors', 1)
    height = 400 + (floors - 1) * 80
    
    svg = f'''<svg width="900" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
    <rect x="50" y="100" width="800" height="{height-150}" fill="rgba(255,255,255,0.9)" stroke="#333" stroke-width="3" rx="10"/>
    <rect x="100" y="150" width="200" height="{height-250}" fill="rgba(200,220,240,0.8)" stroke="#333" stroke-width="2" rx="5"/>
    <rect x="350" y="130" width="100" height="{height-230}" fill="rgba(200,220,240,0.8)" stroke="#333" stroke-width="2" rx="5"/>
    <rect x="500" y="150" width="200" height="{height-250}" fill="rgba(200,220,240,0.8)" stroke="#333" stroke-width="2" rx="5"/>
    <rect x="350" y="{height-120}" width="200" height="50" fill="#8B7355" stroke="#333" stroke-width="2" rx="20"/>
    <text x="450" y="70" text-anchor="middle" font-family="Arial" font-size="24" font-weight="bold" fill="white">واجهة {STYLES.get(style, style)}</text>
    <text x="450" y="{height-20}" text-anchor="middle" font-family="Arial" font-size="12" fill="white">© {DEVELOPER_NAME} | {BOT_USERNAME}</text>
</svg>'''
    filename = f"facade_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(svg)
    return filename

def generate_3d_svg(data: dict) -> str:
    """توليد نموذج ثلاثي الأبعاد بسيط"""
    floors = data.get('floors', 1)
    total_area = data.get('total_area', 100)
    height = 350 + (floors - 1) * 80
    
    svg = f'''<svg width="800" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);">
    <polygon points="200,{height-80} 400,{height-80} 400,{height-40} 200,{height-40}" fill="#4a4a4a" stroke="#fff" stroke-width="2"/>
    <polygon points="400,{height-80} 600,{height-80} 600,{height-40} 400,{height-40}" fill="#3a3a3a" stroke="#fff" stroke-width="2"/>
    <polygon points="200,200 400,160 600,200 400,200" fill="#5a5a5a" stroke="#fff" stroke-width="2"/>
    <polygon points="200,200 400,200 400,{height-80} 200,{height-80}" fill="#6a6a6a" stroke="#fff" stroke-width="2"/>
    <polygon points="400,160 600,200 600,{height-80} 400,{height-80}" fill="#5a5a5a" stroke="#fff" stroke-width="2"/>
    <text x="400" y="100" text-anchor="middle" font-family="Arial" font-size="22" font-weight="bold" fill="#fff">نموذج ثلاثي الأبعاد</text>
    <text x="400" y="130" text-anchor="middle" font-family="Arial" font-size="14" fill="#aaa">{total_area} م² | {floors} دور</text>
    <text x="400" y="{height-15}" text-anchor="middle" font-family="Arial" font-size="10" fill="#666">© {DEVELOPER_NAME}</text>
</svg>'''
    filename = f"3d_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(svg)
    return filename

# ===================== أزرار البوت =====================
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🏗️ تصميم جديد (نص)", callback_data="new_text")],
        [InlineKeyboardButton("🖼️ تحليل مخطط (صورة)", callback_data="new_image")],
        [InlineKeyboardButton("📐 معايير الغرف", callback_data="standards")],
        [InlineKeyboardButton("🎨 أنماط التصميم", callback_data="styles")],
        [InlineKeyboardButton("📏 حساب المساحات", callback_data="calculator")],
        [InlineKeyboardButton("ℹ️ تعليمات", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ===================== دوال البوت =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🏛️ *بوت التصميم المعماري الاحترافي*\n"
        f"🎓 *{BOT_USERNAME}*\n\n"
        f"📌 *يمكنك:*\n"
        f"1️⃣ إرسال وصف نصي للمبنى\n"
        f"2️⃣ رفع صورة مخطط لتحليله وإعادة رسمه\n\n"
        f"📐 *معايير هندسية عالمية (كليات الهندسة)*\n"
        f"• صالة: 20-80 م²\n"
        f"• غرفة نوم رئيسية: 20-42 م²\n"
        f"• غرفة نوم: 12-27 م²\n"
        f"• مطبخ: 12-30 م²\n"
        f"• حمام: 3.6-7.5 م²\n\n"
        f"👨‍💻 المطور: {DEVELOPER_NAME}",
        reply_markup=get_main_keyboard()
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "new_text":
        await query.edit_message_text("📝 أرسل وصف المبنى:", reply_markup=get_main_keyboard())
        context.user_data['mode'] = 'text'
    
    elif data == "new_image":
        await query.edit_message_text("🖼️ أرسل صورة المخطط:", reply_markup=get_main_keyboard())
        context.user_data['mode'] = 'image'
    
    elif data == "standards":
        text = "📐 *المعايير القياسية للغرف (كليات الهندسة)*\n\n"
        for key, std in ROOM_STANDARDS.items():
            text += f"• *{std['name_ar']}*: {std['min_width']}-{std['max_width']} × {std['min_length']}-{std['max_length']} م\n"
        await query.edit_message_text(text, reply_markup=get_main_keyboard())
    
    elif data == "styles":
        text = "🎨 *أنماط التصميم المعماري*\n\n"
        for key, desc in STYLES.items():
            text += f"• *{key}*: {desc}\n"
        await query.edit_message_text(text, reply_markup=get_main_keyboard())
    
    elif data == "calculator":
        await query.edit_message_text(
            "📏 *حاسبة المساحات*\n\n"
            "أرسل الأبعاد بصيغة: عرض × طول\n"
            "مثال: 5 × 6",
            reply_markup=get_main_keyboard()
        )
        context.user_data['mode'] = 'calc'
    
    elif data == "help":
        await query.edit_message_text(
            "📖 *تعليمات الاستخدام*\n\n"
            "🖼️ *تحليل صورة:* ارفع صورة مخطط وسأقوم بتحليله وإعادة رسمه بنفس الدقة\n"
            "📝 *وصف نصي:* اكتب مواصفات المبنى (مساحة، غرف، نمط)\n"
            "📐 *معايير الغرف:* تعرف على الأبعاد القياسية حسب كليات الهندسة\n"
            "🎨 *أنماط التصميم:* اختر النمط المعماري المناسب\n"
            "📏 *حساب المساحات:* آلة حاسبة لحساب مساحة الغرف\n\n"
            "💡 *مثال وصف نصي:*\n"
            "بيت 150 متر، 3 غرف نوم، صالة، مطبخ، حمامين، نمط حديث",
            reply_markup=get_main_keyboard()
        )

# ===================== معالجة الصور =====================
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('mode') != 'image':
        await update.message.reply_text("🏛️ استخدم الأزرار أولاً", reply_markup=get_main_keyboard())
        return
    
    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_bytes = await file.download_as_bytearray()
    
    await update.message.reply_text("🔍 *جاري تحليل المخطط...*")
    
    data = await analyze_image(bytes(image_bytes))
    
    if data:
        await update.message.reply_text("✅ *تم تحليل المخطط بنجاح!*\n🎨 جاري إعادة الرسم...")
        floor_plan = generate_svg_floor_plan(data)
        facade = generate_facade_svg(data)
        model_3d = generate_3d_svg(data)
        
        with open(floor_plan, 'rb') as f:
            await update.message.reply_document(f, filename=floor_plan, caption="📐 المخطط المعاد رسمه بدقة")
        with open(facade, 'rb') as f:
            await update.message.reply_document(f, filename=facade, caption="🏛️ الواجهة المعمارية")
        with open(model_3d, 'rb') as f:
            await update.message.reply_document(f, filename=model_3d, caption="🏗️ النموذج ثلاثي الأبعاد")
        
        os.remove(floor_plan)
        os.remove(facade)
        os.remove(model_3d)
    else:
        await update.message.reply_text("❌ لم أستطع تحليل المخطط. حاول إرسال صورة أوضح.")
    
    context.user_data['mode'] = None

# ===================== معالجة النصوص =====================
async def handle_text_design(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('mode') != 'text':
        await update.message.reply_text("🏛️ اضغط على 'تصميم جديد (نص)' أولاً", reply_markup=get_main_keyboard())
        return
    
    text = update.message.text
    await update.message.reply_text("🎨 *جاري التصميم باستخدام المعايير الهندسية...*")
    
    data = extract_building_data(text)
    floor_plan = generate_svg_floor_plan(data)
    facade = generate_facade_svg(data)
    model_3d = generate_3d_svg(data)
    
    with open(floor_plan, 'rb') as f:
        await update.message.reply_document(f, filename=floor_plan, caption=f"📐 المخطط 2D\n{text[:100]}")
    with open(facade, 'rb') as f:
        await update.message.reply_document(f, filename=facade, caption="🏛️ الواجهة المعمارية")
    with open(model_3d, 'rb') as f:
        await update.message.reply_document(f, filename=model_3d, caption="🏗️ النموذج ثلاثي الأبعاد")
    
    os.remove(floor_plan)
    os.remove(facade)
    os.remove(model_3d)
    context.user_data['mode'] = None

# ===================== حاسبة المساحات =====================
async def handle_calculator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('mode') != 'calc':
        return
    
    text = update.message.text
    match = re.search(r'(\d+)\s*[×x]\s*(\d+)', text)
    
    if match:
        width = float(match.group(1))
        length = float(match.group(2))
        area = width * length
        
        # تحديد نوع الغرفة بناءً على المساحة
        room_type = "غرفة"
        if area >= 20:
            room_type = "صالة أو غرفة نوم رئيسية"
        elif area >= 12:
            room_type = "غرفة نوم أو مطبخ"
        elif area >= 6:
            room_type = "حمام أو مخزن"
        
        await update.message.reply_text(
            f"📐 *نتيجة الحساب*\n\n"
            f"العرض: {width} م\n"
            f"الطول: {length} م\n"
            f"المساحة: {area} م²\n\n"
            f"🏠 تناسب: {room_type}"
        )
    else:
        await update.message.reply_text("❌ صيغة غير صحيحة.\nاستخدم: عرض × طول\nمثال: 5 × 6")
    
    context.user_data['mode'] = None

# ===================== المعالج الرئيسي =====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get('mode')
    
    if mode == 'text':
        await handle_text_design(update, context)
    elif mode == 'calc':
        await handle_calculator(update, context)
    else:
        await update.message.reply_text("🏛️ استخدم الأزرار للبدء", reply_markup=get_main_keyboard())

# ===================== التشغيل =====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("=" * 60)
    print(f"✅ {BOT_USERNAME} - بوت التصميم المعماري الاحترافي")
    print(f"👨‍💻 المطور: {DEVELOPER_NAME}")
    print("📐 المميزات: توليد مخططات 2D | واجهات | نماذج 3D | تحليل الصور")
    print("🎓 معتمد على المعايير الهندسية العالمية (كليات الهندسة)")
    print("=" * 60)
    
    app.run_polling()

if __name__ == "__main__":
    main()            idx += 1
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
