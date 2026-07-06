import asyncio
import os
import time
import random
import datetime
import re
import json
from collections import defaultdict
import aiohttp

# Telethon Imports
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import EditBannedRequest, JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import ChatBannedRights, InputPhoto, InputDocument

# ==========================================================
# 🌟 TELEGRAM BOT CONFIGURATION & CREDENTIALS
# ==========================================================
API_ID = 33938821
API_HASH = '24a5e855b4cf3ce48e054c32ea725aa4'
BOT_TOKEN = '8957362371:AAGC_GviR84bM0kl3Zmp4Ek9Okq56C9tWJM'
DEVELOPER_USERNAME = 'amirx_xpipo'
DEVELOPER_ID = 8050958688

# اختياري: يمكنك وضع مفتاح Gemini API هنا للذكاء الاصطناعي أو تفعيله عبر متغيرات البيئة
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# مسارات ملفات حفظ البيانات المحلية لضمان ثباتها عند إعادة التشغيل
GROUPS_FILE = "groups.json"
ADMINS_FILE = "admins.json"
WARNINGS_FILE = "warnings.json"
RULES_FILE = "rules.txt"
WELCOME_FILE = "welcome.json"
AUTO_SETTINGS_FILE = "auto_settings.json"
DEFAULT_ADMINS = [6941580330]

# ==========================================================
# 💾 DATA STORAGE & PERSISTENCE ENGINE (محرك حفظ البيانات)
# ==========================================================
def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {path}: {e}")
    return default

def save_json(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving {path}: {e}")

# تحميل وحفظ المجموعات المفعلة
active_groups = set(load_json(GROUPS_FILE, []))
def save_groups(): save_json(GROUPS_FILE, list(active_groups))

# إدارة رتب الإدارة والمسؤولين
admins = load_json(ADMINS_FILE, DEFAULT_ADMINS)
def is_admin(sender): 
    if not sender: return False
    return sender.username == DEVELOPER_USERNAME or sender.id in admins or sender.id == DEVELOPER_ID

# تحميل وحفظ التحذيرات
warnings_data = defaultdict(list, load_json(WARNINGS_FILE, {}))
def save_warnings(): save_json(WARNINGS_FILE, dict(warnings_data))

# وسائط الترحيب المخصصة
welcome_media = load_json(WELCOME_FILE, {})
def save_welcome_media(): save_json(WELCOME_FILE, welcome_media)

# متغيرات التشغيل الديناميكية في الذاكرة
mute_status = {}
message_count = defaultdict(int)
last_muted_user = {}
client = TelegramClient('bot', API_ID, API_HASH)
BOT_PHOTO = None

# إعدادات الحماية الشاملة والقابلة للتحكم والتبديل السريع
bot_settings = load_json(AUTO_SETTINGS_FILE, {
    "mute_duration": 300,        # مدة الكتم الافتراضية بالثواني (5 دقائق)
    "link_protection": True,     # كتم الروابط والإعلانات وحذفها
    "forward_protection": True,  # منع التوجيهات الخارجية المنشورة من القنوات وحذفها
    "swear_protection": True,    # تصفية الشتائم والكلام البذيء وحذفها تلقائياً
    "anti_flood": True,          # منع السبام والإغراق بالرسائل السريعة
    "anti_raid": True,           # منع الحسابات العشوائية السريعة الدخول
    "verification_captcha": True,# التحقق البشري الذكي للأعضاء الجدد (Captcha)
    "service_cleanup": True,     # الحذف التلقائي لإشعارات الخدمة "انضم/غادر المجموعة"
    "chat_locked": False,        # قفل الدردشة بشكل كامل
})

def save_settings():
    save_json(AUTO_SETTINGS_FILE, bot_settings)

# تتبع رسائل المستخدمين لمنع السبام (Anti-Flood)
user_messages_timestamps = defaultdict(list)
# تحديات التحقق البشري المعلقة
pending_captchas = {} # الهيكل: {user_id: {"chat_id": chat_id, "message_id": msg_id, "timestamp": ts, "first_name": name}}

# ==========================================================
# 🤖 GEMINI AI CO-PILOT INTEGRATION (دمج ذكاء اصطناعي بيبو)
# ==========================================================
async def ask_gemini_ai(prompt):
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_KEY":
        return "⚠️ عذراً المطور لم يقم بتفعيل مفتاح الذكاء الاصطناعي Gemini في السيرفر بعد."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    system_instruction = (
        "أنت مساعد بيبو الذكي (Pipo AI)، بوت تليجرام شهير ومحبوب جداً ومحترف لإدارة وحماية مجموعات تليجرام. "
        "مهمتك هي الإجابة عن استفسارات الأعضاء بطريقة ودية، فكاهية، ذكية وسريعة باللغة العربية الفصحى مع لمسة لهجة جزائرية خفيفة وودودة إن أمكن. "
        "تحدث باختصار ودون تعقيد واجعل كلامك مشوقاً ومليئاً بالطاقة الإيجابية!"
    )
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]}
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers={"Content-Type": "application/json"}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    return "🤖 بيبو تعبان شوية حالياً، يرجى المحاولة لاحقاً يا صديقي!"
    except Exception as e:
        return f"❌ حدث خطأ أثناء الاتصال بالذكاء الاصطناعي: {str(e)}"

# ==========================================================
# 🛡️ ADVANCED CONFLICT & TEXT DETECTORS (الفلاتر المتطورة)
# ==========================================================
CONFLICT_WORDS = [
    r'\b(يا غبي|يا حمار|يا أحمق|اسكت|اخرس|انقلع|غبي|حمار|غبية|حمقاء|كلب|يا كلب|حيوان)\b',
    r'\b(stupid|shut up|idiot|fool|dumb|moron|stfu|f shut up)\b',
    r'\b(بلا شرف|عديم الشرف|كذاب|يا كذاب|منافق|حقير|سفيه|رخيص)\b'
]

BAD_WORDS = [
    r'\b(كس|طيز|زب|نيك|شرموطة|قحبة|منيكة|منيوك|مسطي|مصطي|قلبوز)\b',
    r'\b(zeb|zebi|zebbi|kahba|9ahba|9ahb|9hba|kess|kessou|tiz|tizi|3ass|3asska)\b',
    r'\b(قود|god|goud|gawd|gwd)\b',
    r'\b(طحان|طيحان|tahhan|tihan|t7an|t7an|t7han|t7han)\b',
    r'\b(9ahb|9hba|9ahba|9hab|9haba|9hba|9hb|9ahb)\b',
    r'\b(zebi|zebbi|zeb|zbi|zbbi|zebby|zeby)\b',
    r'\b(kess|kes|ks|kessou|kesou|ksou)\b',
    r'\b(tiz|tizi|tizy|tezi|tezy)\b',
    r'\b(3ass|3as|3asska|3aska|3assk)\b',
    r'\b(nik|nikom|nikk|neek|nekk|nkk|n6|n6k)\b',
    r'\b(9wd|9wad|9awd|gawd|goud|god|9od)\b',
    r'ن[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*ي[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[كڪKbB6]',
    r'[كڪKbB][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[سښصث5\$]',
    r'[ططـظظـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[يىېۍ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[زژڗژظڞ]',
    r'[زژڗژ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[ببـپپـ]',
    r'[قڨ9][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[ححـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[ببـپپـ]',
    r'f[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[uوؤ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[cكڪ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[kكڪ]',
    r'[nن][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[i1!|][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[gج][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[gج][\s\.\,\;\:\!\@\#\$\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[e3][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[rر]',
    r'\b(زبي|زبيي|كسك|طيزك|قحبتك|قحبتي)\b',
    r'\b(يا[\s]*ود[\s]*الكبدة|يا[\s]*ولد[\s]*القحبة|ولد[\s]*الزانية)\b',
    r'\b(نعل[\s]*الدين|نعل[\s]*الوالدين|نعل[\s]*الرب|نعل[\s]*ملتك)\b',
    r'\b(الله[\s]*ينعل|الله[\s]*يلعن|ينعل[\s]*دين|يلعن[\s]*دين)\b',
    r'ن\s*م\s*ي',
    r'[ننـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[مm][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[يىېۍ]',
    r'[ننـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*m[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*e[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[يىېۍ]',
]

LINK_PATTERNS = [
    r'https?://\S+', 
    r't\.me/\S+', 
    r'www\.\S+', 
    r'@\S+\s+(جروب|قناة|اشترك|تبادل)', # تتبع الإعلانات واليوزرات المزعجة
    r'telegram\.me/\S+'
]

conflict_tracker = defaultdict(lambda: defaultdict(list))
CONFLICT_THRESHOLD = 3
CONFLICT_WINDOW = 300
CONFLICT_COOLDOWN = 600

def detect_conflict(text):
    for p in CONFLICT_WORDS:
        if re.search(p, text, re.IGNORECASE):
            return True
    return False

def contains_swear(t): 
    if not t: return False
    return any(re.search(p, t, re.I) for p in BAD_WORDS)

def contains_link(t): 
    if not t: return False
    return any(re.search(p, t, re.I) for p in LINK_PATTERNS)

def is_forward(m): 
    return bool(m.forward)

# ==========================================================
# 💎 PREMIUM DESIGN COVERS (زخرفة وصياغة النصوص الجمالية)
# ==========================================================
def style_box(title, text, footer="👑 PIPO PROTECT"):
    """صياغة إطارات جمالية راقية للإعلانات والإشعارات الفنية"""
    border_top    = "╔════════════════════════╗"
    border_mid    = "╠────────────────────────╢"
    border_bottom = "╚════════════════════════╝"
    
    styled = (
        f"⚡ {title} ⚡\n"
        f"{border_top}\n\n"
        f"{text}\n\n"
        f"{border_mid}\n"
        f"✨ {footer} ✨\n"
        f"{border_bottom}"
    )
    return styled

async def reply_with_pic(event, text, emoji="", buttons=None):
    full = f"{emoji} {text} {emoji}" if emoji else text
    if BOT_PHOTO:
        try: 
            await client.send_file(event.chat_id, BOT_PHOTO, caption=full, buttons=buttons)
            return
        except: 
            pass
    await event.reply(full, buttons=buttons)

# ==========================================================
# ⚡ CORE MODERATION FUNCTIONS (محرك كتم وحظر الأعضاء)
# ==========================================================
async def mute_user(chat, user, dur):
    try: 
        await client(EditBannedRequest(chat, user, ChatBannedRights(
            until_date=datetime.datetime.fromtimestamp(time.time()+dur), 
            send_messages=True,
            send_media=True,
            send_stickers=True,
            send_gifs=True
        )))
        return True
    except Exception as e: 
        print(f"Mute Error: {e}")
        return False

async def unmute_user(chat, user):
    try: 
        await client(EditBannedRequest(chat, user, ChatBannedRights(until_date=None, send_messages=False)))
        return True
    except Exception as e: 
        print(f"Unmute Error: {e}")
        return False

async def ban_user(chat, user):
    try: 
        await client(EditBannedRequest(chat, user, ChatBannedRights(until_date=None, view_messages=True)))
        return True
    except Exception as e: 
        print(f"Ban Error: {e}")
        return False

async def unban_user(chat, user):
    try: 
        await client(EditBannedRequest(chat, user, ChatBannedRights(until_date=None, view_messages=False)))
        return True
    except Exception as e: 
        print(f"Unban Error: {e}")
        return False

# ==========================================================
# 📥 AUTO-JOIN COMMANDS (سحب البوت للمجموعات وتفعيله تلقائياً)
# ==========================================================
@client.on(events.NewMessage(from_users=DEVELOPER_ID, pattern=r'^/دخول\s+(.+)', func=lambda e: e.is_private))
async def join_group(event):
    arg = event.pattern_match.group(1).strip()
    try:
        if arg.startswith('https://t.me/') or arg.startswith('t.me/'):
            if 'joinchat' in arg or '+' in arg:
                hash_part = arg.split('/')[-1].split('?')[0]
                await client(ImportChatInviteRequest(hash_part))
                return await reply_with_pic(event, "تم الدخول بنجاح! يرجى استخدام /تفعيل داخل المجموعة لتفعيل الحماية.")
            else:
                username = arg.rstrip('/').split('/')[-1]
                entity = await client.get_entity(f'@{username}')
        elif arg.startswith('@'):
            entity = await client.get_entity(arg)
        else:
            entity = await client.get_entity(int(arg))
        
        await client(JoinChannelRequest(entity))
        active_groups.add(entity.id)
        save_groups()
        await reply_with_pic(event, f"✅ تم دخول المجموعة وتفعيل حماية بيبو بنجاح!\n📝 اسم المجموعة: {entity.title}\n🆔 الآيدي: {entity.id}")
    except Exception as e:
        await reply_with_pic(event, f"❌ فشل الدخول: {str(e)}")

# ==========================================================
# 👑 MASTER ADMINISTRATIVE COMMANDS (لوحة تحكم إلكترونية تفاعلية)
# ==========================================================
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    s = await event.get_sender()
    if is_admin(s):
        menu_text = (
            "👋 أهلاً بك يا مطوري العزيز في لوحة تحكم بيبو الخارقة!\n"
            "يمكنك التحكم بكامل المجموعة وتعديل خيارات الحماية بضغطة زر واحدة."
        )
        styled = style_box("لوحة تحكم بيبو للمطورين", menu_text)
        await reply_with_pic(event, styled, "👑", buttons=[
            [Button.inline("🔇 مدة الكتم", b"mute_dur"), Button.inline("📊 الإحصائيات العامة", b"bot_stat")],
            [Button.inline("⚙️ إعدادات الحماية", b"security_settings"), Button.inline("🔓 فك كتم الجميع", b"unmute_all_btn")],
            [Button.inline("🤖 تفعيل الذكاء الاصطناعي", b"toggle_gemini_setup")]
        ])
    else:
        welcome_ordinary = (
            "✨ مرحباً بك! أنا بيبو بوت الحماية والأمان الخارق لمجموعتك.\n"
            "مهمتي الحفاظ على سلامة الدردشة من السابين، المزعجين والسبام.\n\n"
            "💬 أرسل /الاوامر لرؤية كل ما يمكنني القيام به!"
        )
        await reply_with_pic(event, style_box("بيبو حامي المجموعات", welcome_ordinary), "🛡️")

@client.on(events.NewMessage(pattern='^/تفعيل$'))
async def activate_group(event):
    if not is_admin(await event.get_sender()): return
    active_groups.add(event.chat_id)
    save_groups()
    msg = style_box("تفعيل الدردشة", "🛡️ تم تفعيل نظام الحماية الذكي لبيبو في هذه المجموعة!\nجميع الفلاتر والحمايات مفعلة وتعمل بكفاءة 100%.")
    await reply_with_pic(event, msg, "✅")

@client.on(events.NewMessage(pattern='^/تعطيل$'))
async def deactivate_group(event):
    if not is_admin(await event.get_sender()): return
    active_groups.discard(event.chat_id)
    save_groups()
    msg = style_box("تعطيل الدردشة", "⚠️ تم تعطيل حماية بيبو في هذه المجموعة مؤقتاً.\nأتمنى السلامة للجميع!")
    await reply_with_pic(event, msg, "❌")

@client.on(events.NewMessage(pattern='^/المجموعات$'))
async def list_groups(event):
    if not is_admin(await event.get_sender()): return
    if not active_groups: 
        return await reply_with_pic(event, "لا توجد مجموعات مفعلة حالياً.")
    
    txt = "📋 **قائمة المجموعات النشطة تحت حماية بيبو:**\n\n"
    for gid in active_groups:
        try: 
            entity = await client.get_entity(gid)
            txt += f"🔹 **{entity.title}**\n   └ ID: `{gid}`\n"
        except: 
            txt += f"🔹 مجموعة مجهولة\n   └ ID: `{gid}`\n"
    await reply_with_pic(event, txt)

@client.on(events.NewMessage(pattern='^/قفل_المجموعة$'))
async def lock_chat(event):
    if not is_admin(await event.get_sender()): return
    bot_settings["chat_locked"] = True
    save_settings()
    await client.edit_permissions(event.chat_id, send_messages=False)
    await reply_with_pic(event, style_box("قفل المجموعه", "🔒 تم قفل المجموعة بالكامل.\nيسمح للمشرفين فقط بإرسال الرسائل حالياً."), "🔐")

@client.on(events.NewMessage(pattern='^/فك_القفل$'))
async def unlock_chat(event):
    if not is_admin(await event.get_sender()): return
    bot_settings["chat_locked"] = False
    save_settings()
    await client.edit_permissions(event.chat_id, send_messages=True)
    await reply_with_pic(event, style_box("فتح المجموعة", "🔓 تم فتح المجموعة للجميع!\nتمنياتنا لكم بدردشة ممتعة ومحترمة."), "🔓")

@client.on(events.NewMessage(pattern='^/ايدي$'))
async def get_id(event): 
    uid = event.sender_id
    chat_id = event.chat_id
    reply_msg = f"🆔 **آيدي حسابك:** `{uid}`\n📍 **آيدي هذه المجموعة:** `{chat_id}`"
    await reply_with_pic(event, style_box("معلومات المعرفات", reply_msg), "📝")

@client.on(events.NewMessage(pattern='^/حالة_الحماية$'))
async def prot_stat(event):
    stat = (
        f"🛡️ **حالة حماية بيبو الذكية:**\n\n"
        f"🔗 **حماية الروابط:** {'✅ نشط' if bot_settings['link_protection'] else '❌ معطل'}\n"
        f"🔄 **حماية التوجيه:** {'✅ نشط' if bot_settings['forward_protection'] else '❌ معطل'}\n"
        f"🤬 **فلتر الشتائم:** {'✅ نشط' if bot_settings['swear_protection'] else '❌ معطل'}\n"
        f"🌊 **مكافحة السبام (Anti-Flood):** {'✅ نشط' if bot_settings['anti_flood'] else '❌ معطل'}\n"
        f"🤖 **التحقق من الروبوتات (Captcha):** {'✅ نشط' if bot_settings['verification_captcha'] else '❌ معطل'}\n"
        f"🗑️ **تنظيف رسائل الدخول والخروج:** {'✅ نشط' if bot_settings['service_cleanup'] else '❌ معطل'}\n"
        f"🔒 **حالة المجموعة:** {'🔒 مغلقة' if bot_settings['chat_locked'] else '🔓 مفتوحة'}\n"
        f"⏳ **مدة الكتم الافتراضية:** `{bot_settings['mute_duration'] // 60}` دقيقة"
    )
    await reply_with_pic(event, style_box("تقرير الحماية الفني", stat), "📊")

@client.on(events.NewMessage(pattern=r'^/مدة_الكتم (\d+)$'))
async def set_md(event):
    if not is_admin(await event.get_sender()): return
    mins = int(event.pattern_match.group(1))
    bot_settings["mute_duration"] = mins * 60
    save_settings()
    await reply_with_pic(event, f"⏰ تم تعديل مدة الكتم التلقائية إلى: **{mins} دقائق**", "⏳")

@client.on(events.NewMessage(pattern='^/مدة_الكتم$'))
async def sh_md(event): 
    await reply_with_pic(event, f"⏰ مدة الكتم التلقائية الحالية: **{bot_settings['mute_duration'] // 60} دقائق**", "⏳")

@client.on(events.NewMessage(pattern='^/فك_الكل|/فك_كل_الكمات$'))
async def unm_all(event):
    if not is_admin(await event.get_sender()): return
    c = 0
    for u in list(mute_status.keys()):
        try: 
            await unmute_user(event.chat_id, u)
            del mute_status[u]
            c += 1
        except: 
            pass
    await reply_with_pic(event, f"✅ تم فك الكتم عن **{c}** أعضاء بنجاح في هذه المجموعة!", "🔊")

# --- التبديل السريع لحماية الروابط والتوجيه عبر الأوامر السريعة ---
@client.on(events.NewMessage(pattern='^/تفعيل_حماية_الروابط$'))
async def en_l(event):
    if not is_admin(await event.get_sender()): return
    bot_settings["link_protection"] = True
    save_settings()
    await reply_with_pic(event, "✅ تم تفعيل حماية الروابط ومنع الإعلانات بنجاح.", "🛡️")

@client.on(events.NewMessage(pattern='^/تعطيل_حماية_الروابط$'))
async def dis_l(event):
    if not is_admin(await event.get_sender()): return
    bot_settings["link_protection"] = False
    save_settings()
    await reply_with_pic(event, "⚠️ تم تعطيل حماية الروابط. يمكن للأعضاء مشاركة الروابط الآن.", "⚠️")

@client.on(events.NewMessage(pattern='^/تفعيل_حماية_التوجيه$'))
async def en_f(event):
    if not is_admin(await event.get_sender()): return
    bot_settings["forward_protection"] = True
    save_settings()
    await reply_with_pic(event, "✅ تم تفعيل حماية التوجيه لمنع السبام والمنشورات الخارجية.", "🛡️")

@client.on(events.NewMessage(pattern='^/تعطيل_حماية_التوجيه$'))
async def dis_f(event):
    if not is_admin(await event.get_sender()): return
    bot_settings["forward_protection"] = False
    save_settings()
    await reply_with_pic(event, "⚠️ تم تعطيل حماية التوجيه.", "⚠️")

# ==========================================================
# 🛑 ACTIVE MODERATION TOOLS (إدارة العقوبات الفورية والتنبيهات)
# ==========================================================
@client.on(events.NewMessage(pattern='/كتم', func=lambda e: e.is_reply))
async def perm_mute(event):
    if not is_admin(await event.get_sender()): return
    target_msg = await event.get_reply_message()
    target = await target_msg.get_sender()
    if not target: return await reply_with_pic(event, "❌ لم أستطع العثور على العضو المراد كتمه.")
    
    ten_years = 10*365*24*3600
    await mute_user(event.chat_id, target.id, ten_years)
    mute_status[target.id] = {'until': time.time()+ten_years, 'name': target.first_name}
    await reply_with_pic(event, f"🚫 تم كتم العضو **{target.first_name}** بالكامل من قبل المشرف! كفاك ثرثرة غير لائقة. 😂", "🚫")

@client.on(events.NewMessage(pattern='^/(حظر|حضر)$', func=lambda e: e.is_reply))
async def ban_handler(event):
    if not is_admin(await event.get_sender()): return
    target_msg = await event.get_reply_message()
    target = await target_msg.get_sender()
    if not target: return await reply_with_pic(event, "❌ العضو غير موجود.")
    if target.username == DEVELOPER_USERNAME or target.id in admins or target.id == DEVELOPER_ID: 
        return await reply_with_pic(event, "❌ لا يمكن حظر المسؤول أو مطور البوت!")
    
    if await ban_user(event.chat_id, target.id): 
        await reply_with_pic(event, f"🚫 طرد مطرود! تم حظر العضو **{target.first_name}** نهائياً من المجموعة ورميه خارجاً.", "🚫")
    else: 
        await reply_with_pic(event, "❌ فشل حظر العضو، تأكد من صلاحيات البوت.")

@client.on(events.NewMessage(pattern='^/فك_الحظر$', func=lambda e: e.is_reply))
async def unban_handler(event):
    if not is_admin(await event.get_sender()): return
    target_msg = await event.get_reply_message()
    target = await target_msg.get_sender()
    if not target: return await reply_with_pic(event, "❌ العضو غير موجود.")
    
    if await unban_user(event.chat_id, target.id): 
        await reply_with_pic(event, f"🔓 أهلاً بعودتك! تم فك حظر العضو **{target.first_name}** ويمكنه الانضمام والمشاركة مجدداً.")
    else: 
        await reply_with_pic(event, "❌ فشل فك الحظر.")

@client.on(events.NewMessage(pattern='^/تحذير$'))
async def warn(event):
    if not is_admin(await event.get_sender()): return
    if not event.is_reply: 
        return await reply_with_pic(event, "❌ يرجى الرد على رسالة المخالف لإصدار التحذير له.")
    
    target_msg = await event.get_reply_message()
    target = await target_msg.get_sender()
    if not target: return
    
    uid = target.id
    name = target.first_name or "مجهول"
    warnings_data[str(uid)].append(time.time())
    save_warnings()
    
    cur = len(warnings_data[str(uid)])
    await reply_with_pic(event, f"⚠️ العضو **{name}** تم تحذيره بسب ارتكاب مخالفة قوانين الدردشة!\nعدد التحذيرات الحالية: **{cur}/3**", "⚠️")
    
    if cur >= 3:
        if await mute_user(event.chat_id, uid, bot_settings["mute_duration"]):
            mute_status[uid] = {'until': time.time()+bot_settings["mute_duration"], 'name': name}
            await reply_with_pic(event, f"🚫 تم كتم العضو **{name}** تلقائياً لمدة **{bot_settings['mute_duration']//60} دقيقة** بعد بلوغه 3 تحذيرات متتالية!", "🚫")
            if str(uid) in warnings_data:
                del warnings_data[str(uid)]
                save_warnings()

@client.on(events.NewMessage(pattern='^/عرض_التحذيرات$'))
async def show_warn(event):
    target_id = None
    target_name = ""
    if event.is_reply:
        target_msg = await event.get_reply_message()
        u = await target_msg.get_sender()
        if u: 
            target_id = u.id
            target_name = u.first_name
    else:
        args = event.raw_text.split()
        if len(args) >= 2:
            try: 
                target_id = int(args[1])
            except: 
                pass
    if not target_id: 
        return await reply_with_pic(event, "❌ يرجى كتابة الآيدي أو استخدام الأمر بالرد على رسالة العضو.")
    
    c = len(warnings_data.get(str(target_id), []))
    await reply_with_pic(event, f"📊 العضو **{target_name or target_id}** لديه حالياً: **{c}/3 تحذيرات**", "📋")

@client.on(events.NewMessage(pattern=r'^/مسح\s+(\d+)$'))
async def purge(event):
    if not is_admin(await event.get_sender()): return
    count = min(int(event.pattern_match.group(1)), 100)
    if count <= 0: return
    
    msgs = await client.get_messages(event.chat_id, limit=count)
    ids = [m.id for m in msgs if m]
    await client.delete_messages(event.chat_id, ids)
    confirm = await reply_with_pic(event, f"🧹 تم تنظيف وإبادة **{len(ids)}** رسائل من الدردشة بنجاح!")
    await asyncio.sleep(2)
    await confirm.delete()

@client.on(events.NewMessage(pattern='^/عرض_المكتومين$'))
async def muted_list(event):
    if not mute_status: 
        return await reply_with_pic(event, "✅ الدردشة خالية من المكتومين، الجميع يتحدث بحرية!")
    
    now = time.time()
    txt = "📋 **قائمة الأعضاء المكتومين حالياً:**\n\n"
    for uid, d in mute_status.items():
        rem = int(d['until'] - now)
        if rem > 0:
            try: 
                name = (await client.get_entity(uid)).first_name
            except: 
                name = str(uid)
            txt += f"• **{name}** - ⏳ متبقي: `{rem//60}` دقيقة\n"
    await reply_with_pic(event, txt)

@client.on(events.NewMessage(pattern='^/تثبيت$'))
async def pin_msg(event):
    if not is_admin(await event.get_sender()): return
    if not event.is_reply: return await reply_with_pic(event, "❌ رد على الرسالة التي تود تثبيتها في أعلى المجموعة.")
    replied = await event.get_reply_message()
    try: 
        await client.pin_message(event.chat_id, replied.id)
        await reply_with_pic(event, "📌 تم تثبيت الرسالة بنجاح في لوحة الإعلانات للمجموعة.", "📌")
    except Exception as e: 
        await reply_with_pic(event, f"❌ فشل التثبيت: {e}")

@client.on(events.NewMessage(pattern='^/رفع_مسؤول$'))
async def promote_admin(event):
    sender = await event.get_sender()
    if sender.username != DEVELOPER_USERNAME and sender.id != DEVELOPER_ID: return
    
    target_id = None
    target_name = ""
    if event.is_reply:
        target_msg = await event.get_reply_message()
        u = await target_msg.get_sender()
        if u: 
            target_id = u.id
            target_name = u.first_name
    else:
        args = event.raw_text.split()
        if len(args) >= 2:
            try: 
                target_id = int(args[1])
            except: 
                pass
    if not target_id: 
        return await reply_with_pic(event, "❌ أرسل الأمر بالرد أو مع كتابة معرف المشرف الجديد.")
    if target_id in admins: 
        return await reply_with_pic(event, "⚠️ هذا العضو مشرف بالفعل في نظام بيبو.")
    
    admins.append(target_id)
    save_json(ADMINS_FILE, admins)
    await reply_with_pic(event, f"👑 تم رفع **{target_name or target_id}** مسؤولاً إدارياً جديداً لبوت بيبو بنجاح!", "👑")

@client.on(events.NewMessage(pattern='^/تنزيل_مسؤول$'))
async def demote_admin(event):
    sender = await event.get_sender()
    if sender.username != DEVELOPER_USERNAME and sender.id != DEVELOPER_ID: return
    
    target_id = None
    if event.is_reply:
        target_msg = await event.get_reply_message()
        u = await target_msg.get_sender()
        if u: target_id = u.id
    else:
        args = event.raw_text.split()
        if len(args) >= 2:
            try: target_id = int(args[1])
            except: pass
    if not target_id: 
        return await reply_with_pic(event, "❌ يرجى كتابة آيدي المسؤول أو الرد عليه لتنزيله.")
    if target_id not in admins: 
        return await reply_with_pic(event, "⚠️ ليس مشرفاً إدارياً في البوت بالفعل.")
    
    admins.remove(target_id)
    save_json(ADMINS_FILE, admins)
    await reply_with_pic(event, "✅ تم تنزيل المسؤول من الصلاحيات الإدارية للبوت بنجاح.", "👋")

# ==========================================================
# 🛠️ SYSTEM DIAGNOSTIC PERMISSIONS HELPERS (فحص الصلاحيات)
# ==========================================================
@client.on(events.NewMessage(pattern='^/طلب_صلاحية$'))
async def request_admin(event):
    if not is_admin(await event.get_sender()): return
    await client.send_message(event.chat_id,
        "🤖 **نداء هام:** لكي يتمكن بيبو من الحماية الكاملة والترحيب بالأعضاء الجدد، يرجى ترقيتي إلى رتبة **مشرف** داخل المجموعة مع كامل الصلاحيات."
    )

@client.on(events.NewMessage(pattern='^/تحقق_الصلاحيات$'))
async def check_permissions(event):
    if not is_admin(await event.get_sender()): return
    chat = event.chat_id
    try:
        me = await client.get_me()
        perms = await client.get_permissions(chat, me.id)
        required = {
            'send_messages': 'إرسال الرسائل',
            'manage_chat': 'إدارة المجموعة',
            'delete_messages': 'حذف الرسائل',
            'ban_users': 'حظر الأعضاء',
            'invite_users': 'دعوة أعضاء',
            'pin_messages': 'تثبيت الرسائل',
            'add_admins': 'إضافة مشرفين',
            'change_info': 'تغيير معلومات المجموعة'
        }
        missing = [desc for perm, desc in required.items() if not getattr(perms, perm, False)]
        if missing:
            await event.reply(f"⚠️ **هنالك صلاحيات مفقودة للبوت:**\n" + "\n".join(f"❌ {m}" for m in missing) + "\n\n🔧 يرجى تزويد البوت بها حتى يعمل نظام الحماية بكفاءة.")
        else:
            await event.reply("✅ **رائع جداً!** بيبو يمتلك كافة صلاحيات الإشراف المطلوبة لخدمتكم.")
    except Exception as e:
        await event.reply(f"❌ حدث خطأ أثناء التحقق من الصلاحيات: {str(e)}")

# ==========================================================
# 👤 GENERAL MEMBER UTILITIES & FUN ZONE (قسم الألعاب والترفيه)
# ==========================================================
@client.on(events.NewMessage(pattern='^/تقرير$', func=lambda e: e.is_reply))
async def report(event):
    target_msg = await event.get_reply_message()
    reported_user = await target_msg.get_sender()
    reporter = await event.get_sender()
    if not reported_user or not reporter: return
    
    report_text = (
        f"🚨 **بلاغ بلاغ من الأعضاء!** 🚨\n\n"
        f"👤 **المُبلغ:** {reporter.first_name} (ID: `{reporter.id}`)\n"
        f"🚫 **المخالف:** {reported_user.first_name} (ID: `{reported_user.id}`)\n"
        f"📝 **الرسالة المخالفة:** {target_msg.raw_text[:200]}"
    )
    for admin_id in admins:
        try: 
            await client.send_message(admin_id, report_text)
        except: 
            pass
    await reply_with_pic(event, "✅ تم إرسال التقرير للمسؤولين سرياً ومراجعته فوراً.")

@client.on(events.NewMessage(pattern='^/قوانين$'))
async def rules(event):
    if not os.path.exists(RULES_FILE): 
        return await reply_with_pic(event, "📜 لا توجد قوانين محددة بعد للمجموعة من قبل المطور. يرجى التفاهم بود!")
    with open(RULES_FILE, 'r', encoding='utf-8') as f: 
        rules_text = f.read()
    await reply_with_pic(event, f"📜 **قوانين المجموعة الرسمية:**\n\n{rules_text}")

@client.on(events.NewMessage(pattern='^/معلومات$', func=lambda e: e.is_reply))
async def info(event):
    target_msg = await event.get_reply_message()
    target = await target_msg.get_sender()
    if not target: return await reply_with_pic(event, "❌ خطأ في التعرف على العضو.")
    
    uid = target.id
    warns = len(warnings_data.get(str(uid), []))
    is_muted = "✅ غير مكتوم"
    if uid in mute_status:
        rem = mute_status[uid]['until'] - time.time()
        if rem > 0: is_muted = f"🚫 مكتوم مؤقتاً ({int(rem//60)} د)"
    
    rank = "👤 عضو عادي"
    if target.username == DEVELOPER_USERNAME or target.id == DEVELOPER_ID: 
        rank = "👑 مطور البوت الخارق"
    elif uid in admins: 
        rank = "🛡️ مسؤول المجموعات"
        
    info_text = (
        f"👤 **الاسم:** {target.first_name}\n"
        f"🆔 **الآيدي:** `{uid}`\n"
        f"⭐ **الرتبة:** {rank}\n"
        f"⚠️ **التحذيرات:** {warns}/3\n"
        f"🔇 **حالة الكتم:** {is_muted}"
    )
    await reply_with_pic(event, style_box("بطاقة تعريف العضو", info_text), "📋")

@client.on(events.NewMessage(pattern='^/توب_المتفاعلين$'))
async def top(event):
    if not message_count: return await reply_with_pic(event, "❌ لا توجد إحصائيات تفاعل مسجلة بعد.")
    items = sorted(message_count.items(), key=lambda x: x[1], reverse=True)[:5]
    txt = "🏆 **جدول شرف توب المتفاعلين في المجموعة:**\n\n"
    for i, (uid, cnt) in enumerate(items, 1):
        try: 
            name = (await client.get_entity(uid)).first_name
        except: 
            name = str(uid)
        txt += f"🥇 {i}. **{name}** ⇚ `{cnt}` رسائل\n"
    await reply_with_pic(event, txt)

# --- لعبة قياس الحب والتوافق الكوميدية ---
@client.on(events.NewMessage(pattern='^/حب$'))
async def love(event):
    args = event.raw_text.split()
    if event.is_reply:
        target_msg = await event.get_reply_message()
        target = await target_msg.get_sender()
        u1 = (await event.get_sender()).first_name
        u2 = target.first_name if target else "مجهول"
    elif len(args) >= 3: 
        u1, u2 = args[1], args[2]
    else: 
        return await reply_with_pic(event, "❌ استخدم الأمر بالرد على شخص أو اكتب الاسمين كالتالي:\n`/حب أحمد سارة`")
    
    heart = random.choice(['💔','💖','💘','💕','💓'])
    perc = random.randint(50,100) if heart != '💔' else random.randint(5,45)
    await reply_with_pic(event, f"💖 **اختبار الحب المتطور من بيبو:**\n👩‍❤️‍👨 [{u1}] ➕ [{u2}]\n\n💞 نسبة التوافق والحب بينكما هي: **{perc}%** {heart}", "💞")

# --- ميزة إرسال سر مجهول الهوية ---
@client.on(events.NewMessage(pattern='^/سر$'))
async def secret(event):
    text = event.raw_text[5:].strip()
    if not text: return await reply_with_pic(event, "❌ اكتب الرسالة التي تريد إرسالها بشكل مجهول بعد الأمر.")
    await event.delete()
    await asyncio.sleep(0.5)
    await client.send_message(event.chat_id, f"📩 **رسالة مجهولة سرية وصلت:**\n\n💬 « {text} »\n\n🕵️‍♂️ المرسل مجهول الهوية!")

# ==========================================================
# 🤖 GEMINI CHAT COMMANDS (سؤال ذكاء بيبو الاصطناعي)
# ==========================================================
@client.on(events.NewMessage(pattern=r'^/(اسأل|اسال|بيبو|يا_بيبو)\s+(.+)'))
async def ask_bebo_ai(event):
    prompt = event.pattern_match.group(2).strip()
    loading_msg = await event.reply("🤖 *جاري التفكير وصياغة الرد من بيبو الذكي...*")
    response = await ask_gemini_ai(prompt)
    await loading_msg.delete()
    await event.reply(f"🤖 **بيبو الذكي يقول:**\n\n{response}")

# ==========================================================
# 🎉 INTERACTIVE TRUTH / DARE / GAME CHANNELS (قسم صراحة أو تحدي)
# ==========================================================
TRUTHS = [
    "ما هي أكثر صفة تكرهها في نفسك؟",
    "هل كذبت كذبة كبيرة من قبل؟ ما هي؟",
    "من هو الشخص المفضل لديك في هذا الجروب؟",
    "ما هو أكبر مخاوفك في الحياة؟",
    "لو أتيحت لك فرصة تغيير اسمك، ماذا ستسمي نفسك؟",
    "هل تبكي بمفردك غالباً؟"
]

DARES = [
    "اكتب رسالة اعتذار لأخر شخص تحدثت معه على الخاص.",
    "أرسل أكثر إيموجي تحبه في المجموعة بدون تعليق.",
    "قم بتغيير سيرتك الذاتية في تليجرام لمدة ساعة إلى 'أنا أحب بيبو بوت'.",
    "قم بالرد على رسالة المشرف وقل له 'أنت الأفضل اليوم'.",
    "اصمت ولا ترسل أي رسالة في المجموعة لمدة نصف ساعة!"
]

PUNISHMENTS = [
    "عقابك: ألا ترسل أي ملصق (Sticker) لمدة يوم كامل!",
    "عقابك: أن تتحدث باللغة العربية الفصحى فقط طوال اليوم!",
    "عقابك: الإجابة على سؤال المطور القادم بكل صراحة.",
    "عقابك: كتابة منشور جميل تمدح فيه أعضاء هذا الجروب."
]

@client.on(events.NewMessage(pattern='^/حقيقة$'))
async def game_truth(event):
    await reply_with_pic(event, f"🧠 **سؤال حقيقة محرج لك:**\n\n« {random.choice(TRUTHS)} »\n\nأجبنا بكل صراحة وصدق! 😉", "🧐")

@client.on(events.NewMessage(pattern='^/صراحة$'))
async def game_saraha(event):
    await reply_with_pic(event, f"🧠 **سؤال حقيقة محرج لك:**\n\n« {random.choice(TRUTHS)} »\n\nأجبنا بكل صراحة وصدق! 😉", "🧐")

@client.on(events.NewMessage(pattern='^/تحدي$'))
async def game_dare(event):
    await reply_with_pic(event, f"🔥 **تحدي وقبول صريح ومميز:**\n\n« {random.choice(DARES)} »\n\nنفذ التحدي الآن وصور لنا الإثبات! 😎", "💪")

@client.on(events.NewMessage(pattern='^/عقاب$'))
async def game_punish(event):
    await reply_with_pic(event, f"⚡ **عقاب فكاهي وعادل من بيبو:**\n\n« {random.choice(PUNISHMENTS)} »\n\nيرجى الالتزام بالعقاب لسلامة روح التنافس! 😂", "🔨")

# ==========================================================
# 🎁 CAPTCHA HUMAN VALIDATION CHALLENGE (نظام التحقق البشري التفاعلي)
# ==========================================================
@client.on(events.CallbackQuery)
async def handle_captcha_callbacks(event):
    data = event.data.decode('utf-8')
    sender_id = event.sender_id
    
    # التحقق مما إذا كانت الكبسة تابعة للعضو الجديد وتحدي الروبوتات
    if data.startswith("verify_"):
        parts = data.split("_")
        target_uid = int(parts[1])
        
        if sender_id != target_uid:
            await event.answer("⚠️ هذا الزر مخصص للعضو الجديد فقط للتحقق!", alert=True)
            return
            
        # نجاح التحقق! فك الكتم التلقائي وحذفه من قائمة الانتظار
        if target_uid in pending_captchas:
            try:
                # إزالة القيود البرمجية عن التحدث
                await client(EditBannedRequest(
                    pending_captchas[target_uid]["chat_id"],
                    target_uid,
                    ChatBannedRights(until_date=None, send_messages=False)
                ))
                
                # حذف رسالة التحدي (Captcha Message) لتنظيف الدردشة
                await client.delete_messages(
                    pending_captchas[target_uid]["chat_id"],
                    pending_captchas[target_uid]["message_id"]
                )
                
                del pending_captchas[target_uid]
                await event.answer("✅ تم التحقق من هويتك البشرية! استمتع بالدردشة الآن.", alert=True)
                
                # الترحيب الرسمي بالعضو الجديد بعد تجاوزه الاختبار بنجاح
                user_entity = await client.get_entity(target_uid)
                await client.send_message(
                    event.chat_id,
                    f"🎉 **عضو جديد رائع تجاوز الاختبار!**\nمرحباً بك يا {user_entity.first_name} في مجموعتنا المحترمة."
                )
            except Exception as e:
                print(f"Error resolving captcha click: {e}")
                await event.answer("❌ حدث خطأ، يرجى التواصل مع المشرفين.", alert=True)

    # معالجة الضغطات الأخرى من القوائم القديمة
    elif data.startswith("welcomesp_"):
        _, uid = data.split("_")
        try: 
            await client.send_message(int(uid), "🎉 أهلاً وسهلاً بك في مجموعتنا السعيدة! تمنياتنا لك بأفضل الأوقات. 👋")
            await event.answer("تم إرسال ترحيب خاص للخاص الخاص بك!", alert=True)
        except Exception as e:
            await event.answer("يرجى الضغط على زر بدء المحادثة للبوت في الخاص أولاً لكي أرسل لك!", alert=True)
            
    elif data == "rules_btn":
        if os.path.exists(RULES_FILE):
            with open(RULES_FILE, 'r', encoding='utf-8') as f: 
                txt = f.read()
            await event.answer(txt[:200], alert=True)
        else: 
            await event.answer("لا توجد قوانين محددة بعد.", alert=True)
            
    elif data.startswith("myinfo_"):
        uid = int(data.split("_")[1])
        warns = len(warnings_data.get(str(uid), []))
        is_muted = "غير مكتوم" if uid not in mute_status or mute_status[uid]['until'] < time.time() else "مكتوم"
        info = f"📊 تفاصيل حسابك:\n\nالتحذيرات: {warns}/3\nحالة الكتم: {is_muted}"
        await event.answer(info, alert=True)
        
    elif data == "top_btn":
        if not message_count: 
            await event.answer("لا بيانات تفاعل كافية بعد.", alert=True)
        else:
            items = sorted(message_count.items(), key=lambda x: x[1], reverse=True)[:5]
            txt = ""
            for i, (uid, _) in enumerate(items, 1):
                try: 
                    name = (await client.get_entity(uid)).first_name
                    txt += f"{i}. {name}\n"
                except: 
                    pass
            await event.answer(txt if txt else "مرحباً بالمتفاعلين!", alert=True)
            
    elif data == "security_settings":
        # عرض لوحة التحكم بالحمايات التفاعلية السريعة بضغطة زر
        await event.edit(
            "⚙️ **لوحة تفعيل حمايات بيبو السريعة:**",
            buttons=[
                [Button.inline(f"الروابط: {'✅' if bot_settings['link_protection'] else '❌'}", b"toggle_links"),
                 Button.inline(f"التوجيه: {'✅' if bot_settings['forward_protection'] else '❌'}", b"toggle_forwards")],
                [Button.inline(f"الشتائم: {'✅' if bot_settings['swear_protection'] else '❌'}", b"toggle_swear"),
                 Button.inline(f"الروبوتات (Captcha): {'✅' if bot_settings['verification_captcha'] else '❌'}", b"toggle_captcha")],
                [Button.inline("⬅️ العودة للرئيسية", b"back_to_main")]
            ]
        )
        
    elif data.startswith("toggle_"):
        # معالجة كبسات التفعيل والتعطيل السريع للحمايات
        setting_key = data.replace("toggle_", "")
        mapped_keys = {
            "links": "link_protection",
            "forwards": "forward_protection",
            "swear": "swear_protection",
            "captcha": "verification_captcha"
        }
        actual_key = mapped_keys.get(setting_key)
        if actual_key:
            bot_settings[actual_key] = not bot_settings[actual_key]
            save_settings()
            await event.edit(
                "⚙️ **لوحة تفعيل حمايات بيبو السريعة:**",
                buttons=[
                    [Button.inline(f"الروابط: {'✅' if bot_settings['link_protection'] else '❌'}", b"toggle_links"),
                     Button.inline(f"التوجيه: {'✅' if bot_settings['forward_protection'] else '❌'}", b"toggle_forwards")],
                    [Button.inline(f"الشتائم: {'✅' if bot_settings['swear_protection'] else '❌'}", b"toggle_swear"),
                     Button.inline(f"الروبوتات (Captcha): {'✅' if bot_settings['verification_captcha'] else '❌'}", b"toggle_captcha")],
                    [Button.inline("⬅️ العودة للرئيسية", b"back_to_main")]
                ]
            )
            
    elif data == "back_to_main":
        menu_text = (
            "👋 أهلاً بك يا مطوري العزيز في لوحة تحكم بيبو الخارقة!\n"
            "يمكنك التحكم بكامل المجموعة وتعديل خيارات الحماية بضغطة زر واحدة."
        )
        await event.edit(
            style_box("لوحة تحكم بيبو للمطورين", menu_text),
            buttons=[
                [Button.inline("🔇 مدة الكتم", b"mute_dur"), Button.inline("📊 الإحصائيات العامة", b"bot_stat")],
                [Button.inline("⚙️ إعدادات الحماية", b"security_settings"), Button.inline("🔓 فك كتم الجميع", b"unmute_all_btn")],
                [Button.inline("🤖 تفعيل الذكاء الاصطناعي", b"toggle_gemini_setup")]
            ]
        )
        
    elif data == "toggle_gemini_setup":
        await event.answer("لتفعيل الذكاء الاصطناعي، يرجى وضع الـ API Key في الكود الرئيسي للبوت.", alert=True)

# ==========================================================
# 🔔 AUTOMATIC CAPTCHA & WELCOME ENGINE (محرك الترحيب والتحقق الذاتي)
# ==========================================================
@client.on(events.ChatAction)
async def welcome_action_handler(event):
    chat = event.chat_id
    if chat not in active_groups: return
    
    # تنظيف وحذف رسائل الخدمة المزعجة تلقائياً لجروب نظيف ومرتب
    if event.user_joined or event.user_left:
        if bot_settings["service_cleanup"]:
            try:
                msg = await event.get_message()
                if msg:
                    asyncio.create_task(delete_message_after_delay(chat, msg.id, 10))
            except Exception as e:
                print(f"Error clean service msg: {e}")
                
    if event.user_joined:
        user = await event.get_user()
        if user.bot: return # تجاهل الروبوتات المضافة يدوياً
        
        name = user.first_name or "صديقنا"
        uid = user.id
        username = f"@{user.username}" if user.username else "لا يوجد"
        now = datetime.datetime.now()
        
        try: 
            group_title = (await client.get_entity(chat)).title
        except: 
            group_title = "مجموعتنا الرائعة"

        # --- تفعيل الكابتشا والتحقق التلقائي للأعضاء الجدد ---
        if bot_settings["verification_captcha"]:
            # كتم العضو الجدد تلقائياً لحين تجاوز الكابتشا
            await mute_user(chat, uid, 300) # كتم مؤقت
            
            captcha_text = (
                f"🚨 **مرحباً بك يا {name} في {group_title}!** 🚨\n\n"
                f"🛡️ لحماية المجموعة من الحسابات الوهمية والسبام، يرجى الضغط على الزر أدناه لإثبات هويتك البشرية وفك الكتم عنك.\n"
                f"⏳ متبقي لديك: **2 دقيقة** للموافقة وإلا سيتم استبعادك تلقائياً!"
            )
            
            buttons = [[Button.inline("✅ أنا لست روبوت (تحقق) ✅", f"verify_{uid}")]]
            sent_captcha = await client.send_message(chat, captcha_text, buttons=buttons)
            
            # تسجيل بيانات الكابتشا مع توقيت الدخول لتتبع انتهاء المهلة
            pending_captchas[uid] = {
                "chat_id": chat,
                "message_id": sent_captcha.id,
                "timestamp": time.time(),
                "username": username,
                "first_name": name
            }
            return

        # ترحيب عادي جميل في حال تم تعطيل الكابتشا
        welcome_text = (
            f"▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨\n"
            f"ᯓ˹ BIENVENUE DANS LE GROUPE ˼\n"
            f"°•——————  『 {group_title} 』 ——————•°\n"
            f"▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨\n"
            f"°︙ نورت قروبنا يـ  『{name}』 🥂✨\n"
            f"°︙ اسمك ⇚『{name}』\n"
            f"°︙ ايديك ⇚『{uid}』\n"
            f"°︙ يوزرك ⇚『{username}』\n"
            f"°︙ تاريخ انضمامك ☜ {now.strftime('%Y/%m/%d')}\n"
            f"°︙ الساعة ☜ {now.strftime('%I:%M %p')}\n"
            f"▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨"
        )

        buttons = [
            [Button.inline("🎉 ترحيب خاص", f"welcomesp_{uid}")],
            [Button.inline("📜 القوانين", "rules_btn"), Button.inline("👤 معلوماتي", f"myinfo_{uid}")],
            [Button.inline("🏆 توب المتفاعلين", "top_btn")]
        ]

        if welcome_media.get('type'):
            try:
                fr_bytes = bytes.fromhex(welcome_media.get('file_reference', '')) if welcome_media.get('file_reference') else b''
                if welcome_media['type'] == 'photo':
                    media = InputPhoto(id=int(welcome_media['media_id']), access_hash=int(welcome_media['access_hash']), file_reference=fr_bytes)
                else:
                    media = InputDocument(id=int(welcome_media['media_id']), access_hash=int(welcome_media['access_hash']), file_reference=fr_bytes)
                await client.send_file(chat, media, caption=welcome_text, buttons=buttons)
                return
            except: 
                pass

        await client.send_message(chat, welcome_text, buttons=buttons)

# دالة مساعدة لتأخير المسح
async def delete_message_after_delay(chat_id, message_id, delay):
    await asyncio.sleep(delay)
    try:
        await client.delete_messages(chat_id, message_id)
    except:
        pass

# ==========================================================
# ⚡ THE ULTIMATE PROTECTION & ANTI-SPAM ENGINE (محرك المراقبة والتحليل المستمر)
# ==========================================================
@client.on(events.NewMessage())
async def global_handler(event):
    if not event.is_group or not event.raw_text or event.out: return
    chat = event.chat_id
    if chat not in active_groups: return
    
    sender = await event.get_sender()
    if not sender or sender.id == (await client.get_me()).id: return
    if is_admin(sender): return
    
    # زيادة إحصائيات التفاعل وحفظ الرسالة
    message_count[sender.id] += 1
    text = event.raw_text.strip()

    # --- مكافحة السبام التلقائي (Anti-Flood Check) ---
    if bot_settings["anti_flood"]:
        now_ts = time.time()
        user_id = sender.id
        # تصفية الطوابع الزمنية وإبقاء آخر 3 ثوانٍ فقط
        user_messages_timestamps[user_id] = [t for t in user_messages_timestamps[user_id] if now_ts - t < 3]
        user_messages_timestamps[user_id].append(now_ts)
        
        # الحد الأقصى هو إرسال أكثر من 5 رسائل في ظرف 3 ثوانٍ
        if len(user_messages_timestamps[user_id]) > 5:
            await event.delete()
            # كتم مرتكب السبام فوراً لمدة 10 دقائق
            await mute_user(chat, user_id, 600)
            mute_status[user_id] = {'until': now_ts + 600, 'name': sender.first_name}
            await client.send_message(chat, f"🚨 **إشعار سبام:** تم كتم العضو **{sender.first_name}** لمدة **10 دقائق** لتكراره إرسال الرسائل بسرعة مفرطة (Anti-Flood)!")
            return

    # --- فلتر حماية الروابط والإعلانات ---
    if bot_settings["link_protection"] and contains_link(text): 
        await event.delete()
        await client.send_message(chat, f"⚠️ عذراً يا **{sender.first_name}**، يمنع إرسال الروابط والإعلانات هنا تماماً حظر لسلامة الجميع.")
        return
        
    # --- فلتر حماية التوجيه والمنشورات الخارجية ---
    if bot_settings["forward_protection"] and is_forward(event.message): 
        await event.delete()
        await client.send_message(chat, f"⚠️ عذراً يا **{sender.first_name}**، يمنع توجيه المنشورات من قنوات أو مجموعات خارجية.")
        return

    # --- فلتر الكلمات البذيئة والشتائم المتطور ---
    if bot_settings["swear_protection"] and contains_swear(text.lower()):
        now = time.time()
        uid = sender.id
        name = sender.first_name or "مجهول"
        
        await event.delete()
        if await mute_user(chat, uid, bot_settings["mute_duration"]):
            mute_status[uid] = {'until': now+bot_settings["mute_duration"], 'name': name}
            await client.send_message(chat, f"🚫 **كتم فوري:** تم كتم العضو **{name}** لـ **{bot_settings['mute_duration']//60} دقيقة** بسبب إرساله كلاماً غير لائق بالجروب.")
        return

    # --- صانع ومراقب السلام الذكي (رصد المشاحنات والخصام بين الأعضاء) ---
    if detect_conflict(text):
        reply = await event.get_reply_message()
        if reply:
            other_user = await reply.get_sender()
            if other_user and other_user.id != sender.id:
                pair = tuple(sorted((sender.id, other_user.id)))
                now_ts = time.time()
                conflict_tracker[pair][sender.id] = [t for t in conflict_tracker[pair][sender.id] if now_ts - t < CONFLICT_WINDOW]
                conflict_tracker[pair][other_user.id] = [t for t in conflict_tracker[pair][other_user.id] if now_ts - t < CONFLICT_WINDOW]
                conflict_tracker[pair][sender.id].append(now_ts)
                total = len(conflict_tracker[pair][sender.id]) + len(conflict_tracker[pair][other_user.id])
                
                if total >= CONFLICT_THRESHOLD:
                    last_rec = conflict_tracker[pair].get('last_reconcile', 0)
                    if now_ts - last_rec > CONFLICT_COOLDOWN:
                        conflict_tracker[pair]['last_reconcile'] = now_ts
                        try:
                            await client.send_message(chat,
                                "🕊️ لاحظت تبادل كلمات حادة بينكما. أرجو التوقف فوراً، فأنتم إخوة.\n"
                                "{وَأَصْلِحُوا ذَاتَ بَيْنِكُمْ}\nتصافحوا وتآخوا، فما أجمل الودّ! 🌹"
                            )
                        except: pass

# ==========================================================
# 🚀 LAUNCH & HEARTBEAT MONITOR (بدء تشغيل البوت ومراقبة النبض)
# ==========================================================
async def main():
    global BOT_PHOTO
    await client.start(bot_token=BOT_TOKEN)
    me = await client.get_me()
    print(f"✅ PIPO BOT READY: @{me.username} | Command & Control: All Systems Green")
    asyncio.create_task(auto_unmute_monitor())
    await client.run_until_disconnected()

async def auto_unmute_monitor():
    while True:
        now = time.time()
        for uid in list(mute_status.keys()):
            if mute_status[uid]['until'] < now:
                for gid in active_groups:
                    try: await unmute_user(gid, uid)
                    except: pass
                del mute_status[uid]
        await asyncio.sleep(30)

if __name__ == '__main__':
    asyncio.run(main())
