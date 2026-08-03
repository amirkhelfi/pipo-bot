import asyncio, os, time, random, datetime, re, json, logging
from collections import defaultdict
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import EditBannedRequest, JoinChannelRequest, LeaveChannelRequest
from telethon.tl.types import ChatBannedRights, InputPhoto, InputDocument
from aiohttp import web

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
#  البيانات الأساسية
# ============================================================
API_ID = 33938821
API_HASH = '24a5e855b4cf3ce48e054c32ea725aa4'
BOT_TOKEN = '8957362371:AAF_e-BbKcvFBw1cjzILba7bR2Sh8jS81fQ'
DEVELOPER_USERNAME = 'amirx_xpipo'
DEVELOPER_ID = 8050958688

# ============================================================
#  دوال مساعدة للجسون
# ============================================================
def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"خطأ في تحميل {path}: {e}")
    return default

def save_json(path, data):
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"خطأ في حفظ {path}: {e}")

# ============================================================
#  إعدادات المجموعات (كل مجموعة لها ملف خاص)
# ============================================================
def get_group_settings(chat_id):
    path = f"group_settings_{chat_id}.json"
    default = {
        "welcome_media": {"type": None, "media_id": None, "access_hash": None, "file_reference": ""},
        "rules": "",
        "mute_duration": 300,
        "link_protection": True,
        "forward_protection": True,
        "auto_lock_enabled": False,
        "anti_duplicate_enabled": True,
        "anti_porn_enabled": True,
        "captcha_enabled": True,
        "bot_hunter_enabled": True
    }
    return load_json(path, default)

def save_group_settings(chat_id, data):
    path = f"group_settings_{chat_id}.json"
    save_json(path, data)

# ============================================================
#  بيانات المجموعات النشطة والمسؤولين
# ============================================================
GROUPS_FILE = "groups.json"
ADMINS_FILE = "admins.json"
USER_GROUPS_FILE = "user_groups.json"
DEFAULT_ADMINS = [6941580330]

active_groups = set(load_json(GROUPS_FILE, []))
def save_groups():
    save_json(GROUPS_FILE, list(active_groups))

user_groups = load_json(USER_GROUPS_FILE, {})
def save_user_groups():
    save_json(USER_GROUPS_FILE, user_groups)

admins = load_json(ADMINS_FILE, DEFAULT_ADMINS)
def is_admin(sender):
    return sender.username == DEVELOPER_USERNAME or sender.id in admins

# ============================================================
#  المتغيرات العامة
# ============================================================
client = TelegramClient('bot', API_ID, API_HASH)
BOT_PHOTO = None
API_TOKEN = "التوكن-الجديد"
mute_status = {}
bot_locked = False
message_count = defaultdict(int)
chat_locked = False
pending_users = {}
user_last_msg = defaultdict(lambda: defaultdict(float))
_last_goodbye = {}
warnings_data = defaultdict(list)

# ============================================================
#  دوال إعدادات المجموعة
# ============================================================
async def get_welcome_media(chat_id):
    return get_group_settings(chat_id).get("welcome_media", {})

async def set_welcome_media(chat_id, media_data):
    settings = get_group_settings(chat_id)
    settings["welcome_media"] = media_data
    save_group_settings(chat_id, settings)

async def get_rules(chat_id):
    return get_group_settings(chat_id).get("rules", "")

async def set_rules(chat_id, rules_text):
    settings = get_group_settings(chat_id)
    settings["rules"] = rules_text
    save_group_settings(chat_id, settings)

async def get_mute_duration(chat_id):
    return get_group_settings(chat_id).get("mute_duration", 300)

# ============================================================
#  دوال الحماية
# ============================================================
async def mute_user(chat, user, dur):
    try:
        await client(EditBannedRequest(chat, user, ChatBannedRights(
            until_date=datetime.datetime.fromtimestamp(time.time()+dur),
            send_messages=True
        )))
        return True
    except Exception as e:
        logger.error(f"خطأ في الكتم: {e}")
        return False

async def unmute_user(chat, user):
    try:
        await client(EditBannedRequest(chat, user, ChatBannedRights(
            until_date=None,
            send_messages=False
        )))
        return True
    except Exception as e:
        logger.error(f"خطأ في فك الكتم: {e}")
        return False

async def ban_user(chat, user):
    try:
        await client(EditBannedRequest(chat, user, ChatBannedRights(
            until_date=None,
            view_messages=True
        )))
        return True
    except Exception as e:
        logger.error(f"خطأ في الحظر: {e}")
        return False

async def unban_user(chat, user):
    try:
        await client(EditBannedRequest(chat, user, ChatBannedRights(
            until_date=None,
            view_messages=False
        )))
        return True
    except Exception as e:
        logger.error(f"خطأ في فك الحظر: {e}")
        return False

# ============================================================
#  كشف السب والروابط والإباحية
# ============================================================
BAD_WORDS = [
    r'\b(كس|طيز|زب|نيك|شرموطة|قحبة|منيكة|منيوك|مسطي|مصطي|قلب|قلبوز)\b',
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
]
LINK_PATTERNS = [r'https?://\S+', r't\.me/\S+', r'www\.\S+']
PORN_KEYWORDS = ['sex', 'porn', 'xxx', 'nsfw', 'سكس', 'اباحية', 'جنس', 'porno', 'anal', 'بورن', 'shemale', 'trans', 'gay', 'lesbian', 'cum', 'orgasm', 'clit', 'dick', 'vagina', 'penis', 'breast', 'nude', 'naked', 'fuck', 'motherfucker', 'bitch', 'slut', 'whore']

def contains_swear(t):
    return any(re.search(p, t, re.I) for p in BAD_WORDS) if t else False

def contains_link(t):
    return any(re.search(p, t, re.I) for p in LINK_PATTERNS) if t else False

def is_forward(m):
    return bool(m.forward)

# ============================================================
#  المهام الخلفية
# ============================================================
async def auto_unmute():
    while True:
        try:
            now = time.time()
            for uid in list(mute_status.keys()):
                if mute_status[uid]['until'] < now:
                    for gid in active_groups:
                        try:
                            await unmute_user(gid, uid)
                        except:
                            pass
                    del mute_status[uid]
        except Exception as e:
            logger.error(f"خطأ في auto_unmute: {e}")
        await asyncio.sleep(30)

async def auto_lock_unlock():
    global chat_locked
    while True:
        try:
            if not active_groups:
                await asyncio.sleep(30)
                continue
            chat_id = next(iter(active_groups))
            settings = get_group_settings(chat_id)
            if not settings.get("auto_lock_enabled", False):
                await asyncio.sleep(30)
                continue
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            now_dz = now_utc + datetime.timedelta(hours=1)
            h, m = now_dz.hour, now_dz.minute
            if h == 0 and m == 0 and not chat_locked:
                chat_locked = True
                for gid in active_groups:
                    try:
                        await client.edit_permissions(gid, send_messages=False)
                    except:
                        pass
            if h == 10 and m == 0 and chat_locked:
                chat_locked = False
                for gid in active_groups:
                    try:
                        await client.edit_permissions(gid, send_messages=True)
                    except:
                        pass
        except Exception as e:
            logger.error(f"خطأ في auto_lock_unlock: {e}")
        await asyncio.sleep(30)

# ============================================================
#  حدث الترحيب
# ============================================================
@client.on(events.ChatAction(func=lambda e: e.user_joined))
async def legendary_welcome(event):
    try:
        chat = event.chat_id
        if chat not in active_groups:
            return
        user = await event.get_user()
        if user.bot:
            return
        await asyncio.sleep(1)
        name = user.first_name or "لاعب"
        uid = user.id
        username = f"@{user.username}" if user.username else "لا يوجد"
        now = datetime.datetime.now()
        group_title = "المجموعة"
        try:
            group_title = (await client.get_entity(chat)).title
        except:
            pass
        
        welcome_text = (
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"     🏠 {group_title} 🏠\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"     🔴 نورت قروبنا يـ {name}\n"
            f"     🔴 اسمك: {name}\n"
            f"     🔴 ايديك: {uid}\n"
            f"     🔴 يوزرك: {username}\n"
            f"     🔴 تاريخ انضمامك: {now.strftime('%Y/%m/%d')}\n"
            f"     🔴 الساعة: {now.strftime('%I:%M %p')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"     🎉 أهلاً وسهلاً بك معنا!\n"
            f"     📜 القوانين: /قوانين\n"
            f"     👤 معلوماتك: /معلومات (بالرد على رسالتك)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
        buttons = [
            [Button.inline("🎉 ترحيب خاص", f"welcomesp_{uid}")],
            [Button.inline("📜 القوانين", "rules_btn"), Button.inline("👤 معلوماتي", f"myinfo_{uid}")],
            [Button.inline("🏆 توب المتفاعلين", "top_btn")]
        ]
        
        media = await get_welcome_media(chat)
        if media.get('type'):
            try:
                fr_bytes = bytes.fromhex(media.get('file_reference', '')) if media.get('file_reference') else b''
                if media['type'] == 'photo':
                    m = InputPhoto(id=int(media['media_id']), access_hash=int(media['access_hash']), file_reference=fr_bytes)
                else:
                    m = InputDocument(id=int(media['media_id']), access_hash=int(media['access_hash']), file_reference=fr_bytes)
                await client.send_file(chat, m, caption=welcome_text, buttons=buttons)
                return
            except Exception as e:
                logger.error(f"خطأ في إرسال وسائط الترحيب: {e}")
        await client.send_message(chat, welcome_text, buttons=buttons)
    except Exception as e:
        logger.error(f"خطأ في حدث الترحيب: {e}")

# ============================================================
#  وداعاً
# ============================================================
@client.on(events.ChatAction(func=lambda e: e.user_left))
async def goodbye_message(event):
    try:
        user = await event.get_user()
        if user.bot:
            return
        user_id = user.id
        now = time.time()
        if user_id in _last_goodbye and now - _last_goodbye[user_id] < 10:
            return
        _last_goodbye[user_id] = now
        await asyncio.sleep(1)
        name = user.first_name or "عضو"
        await event.reply(f"👋 وداعاً يا {name}، نتمنى أن نراك قريباً! 🌟")
    except Exception as e:
        logger.error(f"خطأ في وداعاً: {e}")

# ============================================================
#  منع الإباحية
# ============================================================
@client.on(events.NewMessage())
async def anti_porn(event):
    try:
        if not event.is_group or event.chat_id not in active_groups:
            return
        settings = get_group_settings(event.chat_id)
        if not settings.get("anti_porn_enabled", True):
            return
        sender = await event.get_sender()
        if sender.id == DEVELOPER_ID or is_admin(sender):
            return
        text = event.raw_text.lower()
        for word in PORN_KEYWORDS:
            if word in text:
                await event.delete()
                await event.reply(f"🚫 **ممنوع المحتوى الإباحي!**\n👤 {sender.first_name} تم حذف رسالتك.")
                await mute_user(event.chat_id, sender.id, 3600)
                mute_status[sender.id] = {'until': time.time() + 3600, 'name': sender.first_name}
                return
    except Exception as e:
        logger.error(f"خطأ في منع الإباحية: {e}")

# ============================================================
#  البوت الحارس
# ============================================================
@client.on(events.ChatAction(func=lambda e: e.user_joined))
async def bot_hunter(event):
    try:
        chat = event.chat_id
        if chat not in active_groups:
            return
        settings = get_group_settings(chat)
        if not settings.get("bot_hunter_enabled", True):
            return
        user = await event.get_user()
        me = await client.get_me()
        if user.bot and user.id != me.id:
            await client.kick_participant(chat, user.id)
            await event.reply(f"🚫 **بوت ممنوع!**\n🤖 {user.first_name} تم طرده.")
    except Exception as e:
        logger.error(f"خطأ في البوت الحارس: {e}")

# ============================================================
#  مانع المكرر
# ============================================================
@client.on(events.NewMessage())
async def anti_duplicate(event):
    try:
        if not event.is_group or event.chat_id not in active_groups:
            return
        settings = get_group_settings(event.chat_id)
        if not settings.get("anti_duplicate_enabled", True):
            return
        sender = await event.get_sender()
        if sender.id == DEVELOPER_ID or is_admin(sender):
            return
        text = event.raw_text.strip()
        if not text:
            return
        now = time.time()
        if sender.id in user_last_msg and text in user_last_msg[sender.id]:
            if now - user_last_msg[sender.id][text] < 5:
                await event.delete()
                return
        user_last_msg[sender.id][text] = now
    except Exception as e:
        logger.error(f"خطأ في مانع المكرر: {e}")

# ============================================================
#  الكابتشا
# ============================================================
@client.on(events.ChatAction(func=lambda e: e.user_joined))
async def captcha_verification(event):
    try:
        chat = event.chat_id
        if chat not in active_groups:
            return
        settings = get_group_settings(chat)
        if not settings.get("captcha_enabled", True):
            return
        user = await event.get_user()
        if user.bot or user.id == DEVELOPER_ID:
            return
        uid = user.id
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        answer = num1 + num2
        pending_users[uid] = {'answer': answer, 'chat': chat, 'attempts': 0}
        await client.send_message(chat, f"🔐 **تحقق أمني**\n\n👋 مرحباً {user.first_name}!\nللتحقق من أنك لست بوت، أجب على السؤال التالي:\n\n❓ **{num1} + {num2} = ؟**\n\n⏳ لديك 60 ثانية للإجابة.", buttons=[
            [Button.inline("❌ أنا بوت", f"captcha_fail_{uid}")]
        ])
        await asyncio.sleep(60)
        if uid in pending_users:
            del pending_users[uid]
    except Exception as e:
        logger.error(f"خطأ في الكابتشا: {e}")

@client.on(events.NewMessage())
async def check_captcha(event):
    try:
        if event.is_private:
            return
        uid = event.sender_id
        if uid not in pending_users:
            return
        data = pending_users[uid]
        if event.raw_text.strip().isdigit() and int(event.raw_text.strip()) == data['answer']:
            del pending_users[uid]
            await event.reply("✅ **تم التحقق بنجاح!**\n🎉 أهلاً وسهلاً بك في المجموعة.")
        else:
            data['attempts'] += 1
            if data['attempts'] >= 3:
                try:
                    await client.kick_participant(data['chat'], uid)
                except:
                    pass
                del pending_users[uid]
                await event.reply("❌ **فشل التحقق!**\n🚫 تم طردك من المجموعة.")
    except Exception as e:
        logger.error(f"خطأ في التحقق من الكابتشا: {e}")

# ============================================================
#  نظام لوحة التحكم بالنجوم
# ============================================================
STARS_FILE = "stars.json"

def load_stars():
    return load_json(STARS_FILE, {})

def save_stars(stars_data):
    save_json(STARS_FILE, stars_data)

stars_data = load_stars()

def add_stars(user_id, count):
    user_id = str(user_id)
    if user_id not in stars_data:
        stars_data[user_id] = {"stars": 0, "phase": "start"}
    stars_data[user_id]["stars"] += count
    save_stars(stars_data)
    return stars_data[user_id]["stars"]

# معالج زر "لوحة التحكم"
@client.on(events.CallbackQuery(func=lambda e: e.data == b"dashboard"))
async def dashboard_start(event):
    user_id = str(event.sender_id)
    user_data = stars_data.get(user_id, {"stars": 0, "phase": "start"})
    
    if user_data.get("phase") == "done":
        await event.edit(
            "📊 **لوحة التحكم:**\n\n"
            "🔗 https://pipo-bot.onrender.com/control.html\n\n"
            "🔑 التوكن: التوكن-الجديد"
        )
        return
    
    hint = (
        "📋 **لوحة التحكم PIPO BOT**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 **ماذا توفر لك لوحة التحكم؟**\n\n"
        "• 📊 إحصائيات المجموعات\n"
        "• 🔇 إدارة المكتومين\n"
        "• 📢 الإذاعة للمجموعات\n"
        "• 🚫 القائمة السوداء\n"
        "• ⚙️ تفعيل/تعطيل الميزات\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔐 **للحصول على الرابط، أرسل 10 نجوم.**\n"
        "(اضغط الزر أدناه لإرسال نجماتك)"
    )
    
    buttons = [
        [Button.inline("⭐ أرسل 10 نجوم", "send_stars_10")],
        [Button.inline("🔙 العودة", "back_to_start")]
    ]
    await event.edit(hint, buttons=buttons)

# معالج إرسال النجوم
@client.on(events.CallbackQuery(func=lambda e: e.data.startswith("send_stars_")))
async def send_stars(event):
    user_id = str(event.sender_id)
    stars_to_send = int(event.data.decode().split("_")[2])
    
    total_stars = add_stars(user_id, stars_to_send)
    user_data = stars_data.get(user_id, {"stars": 0, "phase": "start"})
    
    if total_stars >= 10 and user_data.get("phase") != "done":
        user_data["phase"] = "done"
        save_stars(stars_data)
        await event.edit(
            "🎉 **تهانينا!**\n"
            "📊 **رابط لوحة التحكم:**\n\n"
            "🔗 https://pipo-bot.onrender.com/control.html\n\n"
            "🔑 التوكن: التوكن-الجديد\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "يمكنك الآن إدارة مجموعتك بكل سهولة!",
            buttons=[[Button.inline("🔙 العودة", "back_to_start")]]
        )
        return
    
    await event.answer("⚠️ تم إرسال 10 نجوم بنجاح!", alert=True)

# ============================================================
#  الأزرار والتفاعلات العامة
# ============================================================
@client.on(events.CallbackQuery)
async def callback_handler(event):
    try:
        data = event.data.decode('utf-8')
        
        # أزرار الترحيب
        if data.startswith("welcomesp_"):
            _, uid = data.split("_")
            await client.send_message(int(uid), "🎉 أهلاً وسهلاً! نتمنى لك أجمل الأوقات. 👋")
            await event.answer()
        elif data == "rules_btn":
            chat = event.chat_id
            rules_text = await get_rules(chat)
            if rules_text:
                await event.answer(rules_text[:200], alert=True)
            else:
                await event.answer("لا توجد قوانين بعد.", alert=True)
        elif data.startswith("myinfo_"):
            uid = int(data.split("_")[1])
            warns = len(warnings_data.get(uid, []))
            is_muted = "غير مكتوم" if uid not in mute_status or mute_status[uid]['until'] < time.time() else "مكتوم"
            await event.answer(f"تحذيرات: {warns}/3\nكتم: {is_muted}", alert=True)
        elif data == "top_btn":
            if not message_count:
                await event.answer("لا بيانات بعد.", alert=True)
            else:
                items = sorted(message_count.items(), key=lambda x: x[1], reverse=True)[:5]
                txt = ""
                for i, (uid, _) in enumerate(items, 1):
                    try:
                        name = (await client.get_entity(uid)).first_name
                    except:
                        name = str(uid)
                    txt += f"{i}. {name}\n"
                await event.answer(txt, alert=True)
        
        # أزرار /start الرئيسية
        elif data == "features":
            text = """📋 **جميع ميزات PIPO BOT**
━━━━━━━━━━━━━━━━━━━━━━
🛡️ **الحماية:**
• حماية السب 🚫
• حماية الروابط 🔗
• حماية التوجيه 📨
• منع الإباحية 🔞
• البوت الحارس 🤖
• مانع المكرر ♻️
• مانع المزعجة 📢

👑 **الإدارة:**
• نظام الكتم 🔇
• نظام الحظر 🚫
• نظام التحذيرات ⚠️
• نظام التقارير 📊
• القيود المتقدمة ⚙️

🎨 **الترحيب:**
• ترحيب فيديو 🎥
• ترحيب صورة 📸
• ترحيب نص 📝
• وداعاً 👋

📊 **لوحة التحكم:**
• إحصائيات 📈
• إدارة المجموعات 👥
• الإذاعة 📢
• القائمة السوداء 🚫
━━━━━━━━━━━━━━━━━━━━━━
👑 @amirx_xpipo"""
            await event.edit(text)
        elif data == "help":
            await event.edit("❓ **المساعدة:**\n\n📌 **للحصول على المساعدة:**\n• تواصل مع المطور @amirx_xpipo\n• قم بزيارة لوحة التحكم\n• اكتب /الاوامر لعرض جميع الأوامر")
        elif data == "commands":
            await event.edit("📜 **الأوامر:**\n\n🛡️ **المسؤول:**\n/تفعيل - /تعطيل\n/قفل_المجموعة - /فك_القفل\n/كتم - /حظر - /فك_الحظر\n/تحذير - /عرض_التحذيرات\n/مسح عدد - /تثبيت\n\n👤 **الأعضاء:**\n/ايدي - /قوانين - /معلومات\n/توب_المتفاعلين - /تقرير\n/الاوامر - /مساعدة\n\n👑 **المطور:**\n/المجموعات - /رفع_مسؤول\n/تعيين_ترحيب - /تعيين_فيديو_ترحيب\n/الخروج_من_المجموعة")
        
        # العودة للقائمة الرئيسية
        elif data == "back_to_start":
            await start(event)
        
        # أزرار إعدادات المجموعة
        elif data.startswith("config_"):
            chat_id = int(data.split("_")[1])
            text, buttons = await generate_group_controls(chat_id)
            await event.edit(text, buttons=buttons)
        
        # أزرار تبديل الميزات
        elif data.startswith("toggle_"):
            parts = data.split("_")
            chat_id = int(parts[2])
            feature = parts[1]
            settings = get_group_settings(chat_id)
            
            if feature == "swear":
                settings["swear_protection"] = not settings.get("swear_protection", True)
                label = "حماية السب"
            elif feature == "links":
                settings["link_protection"] = not settings.get("link_protection", True)
                label = "حماية الروابط"
            elif feature == "forward":
                settings["forward_protection"] = not settings.get("forward_protection", True)
                label = "حماية التوجيه"
            elif feature == "captcha":
                settings["captcha_enabled"] = not settings.get("captcha_enabled", True)
                label = "التحقق (كابتشا)"
            elif feature == "porn":
                settings["anti_porn_enabled"] = not settings.get("anti_porn_enabled", True)
                label = "منع الإباحية"
            elif feature == "hunter":
                settings["bot_hunter_enabled"] = not settings.get("bot_hunter_enabled", True)
                label = "البوت الحارس"
            elif feature == "duplicate":
                settings["anti_duplicate_enabled"] = not settings.get("anti_duplicate_enabled", True)
                label = "مانع المكرر"
            else:
                await event.answer("ميزة غير معروفة.", alert=True)
                return
            
            save_group_settings(chat_id, settings)
            await event.answer(f"✅ تم {'تفعيل' if settings.get(feature + '_enabled' if feature not in ['swear','links','forward'] else feature + '_protection', True) else 'تعطيل'} {label}")
            text, buttons = await generate_group_controls(chat_id)
            await event.edit(text, buttons=buttons)
        
        # أزرار إدارة الكتم القديمة
        elif data == "mute_dur":
            await event.reply(f"⏰ {mute_duration//60} د")
        elif data == "bot_stat":
            await event.reply(f"📊 مكتوم: {len(mute_status)}")
        elif data == "get_id":
            await event.reply(f"🆔 {event.chat_id}")
        elif data == "unmute_all_btn":
            for u in list(mute_status.keys()):
                try:
                    await unmute_user(event.chat_id, u)
                    del mute_status[u]
                except:
                    pass
            await event.reply("🔓 فك الكل")
        elif data.startswith("add_"):
            if not is_admin(await event.get_sender()):
                return
            _, uid, mins = data.split("_")
            uid = int(uid)
            mins = int(mins)
            await mute_user(event.chat_id, uid, mins*60)
            mute_status[uid] = {'until': time.time()+mins*60}
            await event.edit(f"✅ +{mins} دقائق")
            
    except Exception as e:
        logger.error(f"خطأ في الأزرار: {e}")
        await event.answer("حدث خطأ، حاول مرة أخرى.", alert=True)

# ============================================================
#  دالة إنشاء أزرار التحكم في المجموعة
# ============================================================
async def generate_group_controls(chat_id):
    settings = get_group_settings(chat_id)
    try:
        entity = await client.get_entity(chat_id)
        group_name = entity.title
    except:
        group_name = str(chat_id)
    
    text = f"📋 **إعدادات المجموعة: {group_name}**\n━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"🆔 المعرف: `{chat_id}`\n\n"
    text += "🔘 **اضغط على الزر لتفعيل/تعطيل الميزة:**\n"
    
    status_swear = "✅" if settings.get("swear_protection", True) else "❌"
    status_links = "✅" if settings.get("link_protection", True) else "❌"
    status_forward = "✅" if settings.get("forward_protection", True) else "❌"
    status_captcha = "✅" if settings.get("captcha_enabled", True) else "❌"
    status_porn = "✅" if settings.get("anti_porn_enabled", True) else "❌"
    status_hunter = "✅" if settings.get("bot_hunter_enabled", True) else "❌"
    status_duplicate = "✅" if settings.get("anti_duplicate_enabled", True) else "❌"
    
    buttons = [
        [Button.inline(f"{status_swear} حماية السب", f"toggle_swear_{chat_id}")],
        [Button.inline(f"{status_links} حماية الروابط", f"toggle_links_{chat_id}")],
        [Button.inline(f"{status_forward} حماية التوجيه", f"toggle_forward_{chat_id}")],
        [Button.inline(f"{status_captcha} التحقق (كابتشا)", f"toggle_captcha_{chat_id}")],
        [Button.inline(f"{status_porn} منع الإباحية", f"toggle_porn_{chat_id}")],
        [Button.inline(f"{status_hunter} البوت الحارس", f"toggle_hunter_{chat_id}")],
        [Button.inline(f"{status_duplicate} مانع المكرر", f"toggle_duplicate_{chat_id}")],
        [Button.inline("🔙 العودة للقائمة الرئيسية", "back_to_start")]
    ]
    return text, buttons

# ============================================================
#  أمر /start
# ============================================================
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    try:
        sender = await event.get_sender()
        user_id = str(sender.id)
        
        if event.is_group:
            await event.reply("🤖 PIPO BOT يعمل في هذه المجموعة!\nاستخدم الأوامر للتحكم.")
            return
        
        text = "🤖 **PIPO BOT** 🛡️\n━━━━━━━━━━━━━━━━━━━━━━\nبوت حماية متطور للمجموعات\n━━━━━━━━━━━━━━━━━━━━━━\n👑 **المطور:** @amirx_xpipo\n━━━━━━━━━━━━━━━━━━━━━━"
        
        buttons = [
            [Button.url("➕ أضفني إلى مجموعتك", f"https://t.me/{(await client.get_me()).username}?startgroup=start")],
            [Button.inline("📋 جميع الميزات", b"features"), Button.inline("📊 لوحة التحكم", b"dashboard")],
            [Button.inline("❓ المساعدة", b"help"), Button.inline("📜 الأوامر", b"commands")]
        ]
        
        if user_id in user_groups and user_groups[user_id]:
            text += "\n\n📌 **مجموعاتك:**"
            for chat_id in user_groups[user_id]:
                try:
                    entity = await client.get_entity(int(chat_id))
                    name = entity.title
                    text += f"\n• {name}"
                except:
                    pass
            text += "\n\n🔽 **لضبط إعدادات مجموعة، اضغط على اسمها:**"
            group_buttons = []
            for chat_id in user_groups[user_id]:
                try:
                    entity = await client.get_entity(int(chat_id))
                    name = entity.title[:20]
                    group_buttons.append([Button.inline(f"⚙️ {name}", f"config_{chat_id}")])
                except:
                    pass
            buttons = group_buttons + buttons
        
        if BOT_PHOTO:
            try:
                await client.send_file(event.chat_id, BOT_PHOTO, caption=text, buttons=buttons)
                return
            except:
                pass
        await event.reply(text, buttons=buttons)
        
    except Exception as e:
        logger.error(f"خطأ في /start: {e}")

# ============================================================
#  التفعيل التلقائي عند إضافة البوت
# ============================================================
@client.on(events.ChatAction(func=lambda e: e.user_added and e.user_id == client.loop.run_until_complete(client.get_me()).id))
async def on_bot_added(event):
    try:
        chat = event.chat_id
        adder_id = str(event.action_message.from_id.user_id)
        
        active_groups.add(chat)
        save_groups()
        
        if adder_id not in user_groups:
            user_groups[adder_id] = []
        if chat not in user_groups[adder_id]:
            user_groups[adder_id].append(chat)
        save_user_groups()
        
        await event.reply("🤖 شكراً لإضافتي! أنا بوت PIPO للحماية.\n✅ تم تفعيل الحماية تلقائياً.\n👑 يمكنك ضبط الإعدادات من الخاص عبر /start")
        
        try:
            await client.send_message(int(adder_id), f"✅ تم إضافة البوت إلى مجموعة `{chat}` بنجاح!\n📋 لضبط الإعدادات، اذهب للخاص واكتب /start")
        except:
            pass
            
    except Exception as e:
        logger.error(f"خطأ في حدث إضافة البوت: {e}")

# ============================================================
#  الأوامر الإدارية
# ============================================================
@client.on(events.NewMessage(pattern='^/تفعيل$'))
async def activate_group(event):
    if not is_admin(await event.get_sender()): return
    active_groups.add(event.chat_id)
    save_groups()
    await event.reply("✅ تم تفعيل البوت في هذه المجموعة")

@client.on(events.NewMessage(pattern='^/تعطيل$'))
async def deactivate_group(event):
    if not is_admin(await event.get_sender()): return
    active_groups.discard(event.chat_id)
    save_groups()
    await event.reply("❌ تم تعطيل البوت في هذه المجموعة")

@client.on(events.NewMessage(pattern='^/قوانين$'))
async def rules(event):
    chat = event.chat_id
    rules_text = await get_rules(chat)
    if not rules_text:
        await event.reply("❌ لم يتم تعيين قوانين لهذه المجموعة بعد.")
    else:
        await event.reply(f"📜 **قوانين المجموعة:**\n{rules_text}")

@client.on(events.NewMessage(pattern='^/تعيين_قوانين (.+)$'))
async def set_rules_cmd(event):
    if not is_admin(await event.get_sender()): return
    chat = event.chat_id
    rules_text = event.pattern_match.group(1)
    await set_rules(chat, rules_text)
    await event.reply("✅ تم تعيين القوانين بنجاح!")

@client.on(events.NewMessage(pattern='^/المجموعات$'))
async def list_groups(event):
    if not is_admin(await event.get_sender()): return
    if not active_groups:
        await event.reply("لا توجد مجموعات مفعلة.")
        return
    txt = "📋 **المجموعات المفعلة:**\n"
    for gid in active_groups:
        try:
            txt += f"• {(await client.get_entity(gid)).title} ({gid})\n"
        except:
            txt += f"• {gid}\n"
    await event.reply(txt)

@client.on(events.NewMessage(pattern='^/قفل_المجموعة$'))
async def lock_chat(event):
    if not is_admin(await event.get_sender()): return
    global chat_locked
    chat_locked = True
    await client.edit_permissions(event.chat_id, send_messages=False)
    await event.reply("🔒 تم قفل المجموعة")

@client.on(events.NewMessage(pattern='^/فك_القفل$'))
async def unlock_chat(event):
    if not is_admin(await event.get_sender()): return
    global chat_locked
    chat_locked = False
    await client.edit_permissions(event.chat_id, send_messages=True)
    await event.reply("🔓 تم فتح المجموعة")

@client.on(events.NewMessage(pattern='^/ايدي$'))
async def get_id(event):
    await event.reply(f"`{event.chat_id}`")

@client.on(events.NewMessage(pattern='^/حالة_الحماية$'))
async def prot_stat(event):
    settings = get_group_settings(event.chat_id)
    await event.reply(f"🛡️ الروابط: {'✅' if settings.get('link_protection', True) else '❌'} | التوجيه: {'✅' if settings.get('forward_protection', True) else '❌'} | السب: ✅ | الكابتشا: {'✅' if settings.get('captcha_enabled', True) else '❌'}")

@client.on(events.NewMessage(pattern=r'^/مدة_الكتم (\d+)$'))
async def set_md(event):
    if not is_admin(await event.get_sender()): return
    global mute_duration
    mute_duration = int(event.pattern_match.group(1)) * 60
    await event.reply(f"⏰ {mute_duration // 60} دقائق")

@client.on(events.NewMessage(pattern='^/مدة_الكتم$'))
async def sh_md(event):
    await event.reply(f"⏰ {mute_duration // 60} دقائق")

@client.on(events.NewMessage(pattern='^/فك_كل_الكمات$'))
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
    await event.reply(f"✅ فك {c} كتم")

@client.on(events.NewMessage(pattern='/كتم', func=lambda e: e.is_reply))
async def perm_mute(event):
    if not is_admin(await event.get_sender()): return
    target = await (await event.get_reply_message()).get_sender()
    if not target:
        return await event.reply("❌ العضو غير موجود")
    ten_years = 10*365*24*3600
    await mute_user(event.chat_id, target.id, ten_years)
    mute_status[target.id] = {'until': time.time()+ten_years, 'name': target.first_name}
    await event.reply(f"🚫 هاك الكتمة يا {target.first_name} 😂")

@client.on(events.NewMessage(pattern='^/(حظر|حضر)$', func=lambda e: e.is_reply))
async def ban_handler(event):
    if not is_admin(await event.get_sender()): return
    target = await (await event.get_reply_message()).get_sender()
    if not target:
        return await event.reply("❌ العضو غير موجود")
    if target.username == DEVELOPER_USERNAME or target.id in admins:
        return await event.reply("❌ لا يمكن حظر مسؤول")
    if await ban_user(event.chat_id, target.id):
        await event.reply(f"🚫 {target.first_name} تم حظره")
    else:
        await event.reply("❌ فشل الحظر")

@client.on(events.NewMessage(pattern='^/فك_الحظر$', func=lambda e: e.is_reply))
async def unban_handler(event):
    if not is_admin(await event.get_sender()): return
    target = await (await event.get_reply_message()).get_sender()
    if not target:
        return await event.reply("❌ العضو غير موجود")
    if await unban_user(event.chat_id, target.id):
        await event.reply(f"🔓 {target.first_name} تم فك حظره")
    else:
        await event.reply("❌ فشل فك الحظر")

@client.on(events.NewMessage(pattern='^/تحذير$'))
async def warn(event):
    if not is_admin(await event.get_sender()): return
    if not event.is_reply:
        return await event.reply("❌ يجب الرد على الشخص")
    target = await (await event.get_reply_message()).get_sender()
    if not target:
        return
    uid = target.id
    name = target.first_name or "لا اسم"
    warnings_data[uid].append(time.time())
    save_warnings()
    cur = len(warnings_data[uid])
    await event.reply(f"⚠️ {name} تحذير {cur}/3")
    if cur >= 3:
        if await mute_user(event.chat_id, uid, mute_duration):
            mute_status[uid] = {'until': time.time()+mute_duration, 'name': name}
            await event.reply(f"🚫 {name} كتم {mute_duration//60} د")
            del warnings_data[uid]
            save_warnings()

@client.on(events.NewMessage(pattern='^/عرض_التحذيرات$'))
async def show_warn(event):
    target_id = None
    target_name = ""
    if event.is_reply:
        u = await (await event.get_reply_message()).get_sender()
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
        return await event.reply("❌ استخدم الأمر مع معرف أو رد")
    c = len(warnings_data.get(target_id, []))
    await event.reply(f"📊 {target_name or target_id} لديه {c}/3 تحذيرات")

@client.on(events.NewMessage(pattern=r'^/مسح\s+(\d+)$'))
async def purge(event):
    if not is_admin(await event.get_sender()): return
    count = int(event.pattern_match.group(1))
    if count <= 0:
        return await event.reply("❌ الرجاء إدخال عدد صحيح موجب.")
    if count > 100:
        return await event.reply("❌ الحد الأقصى هو 100 رسالة.")
    await event.delete()
    msgs = await client.get_messages(event.chat_id, limit=count)
    ids = [m.id for m in msgs if m]
    if not ids:
        return
    await client.delete_messages(event.chat_id, ids)
    confirm = await event.respond(f"🧹 تم مسح {len(ids)} رسالة.")
    await asyncio.sleep(2)
    await confirm.delete()

# ============================================================
#  التشغيل الرئيسي
# ============================================================
async def main():
    global BOT_PHOTO
    try:
        await client.start(bot_token=BOT_TOKEN)
        me = await client.get_me()
        logger.info(f"✅ PIPO BOT: @{me.username}")
        
        try:
            photos = await client.get_profile_photos('me', limit=1)
            if photos:
                BOT_PHOTO = InputPhoto(id=photos[0].id, access_hash=photos[0].access_hash, file_reference=photos[0].file_reference)
        except Exception as e:
            logger.warning(f"لم يتم تحميل صورة البوت: {e}")
        
        app = web.Application()
        app.router.add_get('/', lambda r: web.Response(text="OK"))
        app.router.add_get('/control.html', lambda r: web.FileResponse('control.html'))
        
        async def api_handler(request):
            return web.json_response({"status": "ok", "groups": len(active_groups)})
        app.router.add_get('/api/stats', api_handler)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 10000)
        await site.start()
        logger.info("✅ خادم الويب يعمل على المنفذ 10000")
        
        asyncio.create_task(auto_unmute())
        asyncio.create_task(auto_lock_unlock())
        
        await client.run_until_disconnected()
    except Exception as e:
        logger.error(f"خطأ في التشغيل الرئيسي: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(main())
