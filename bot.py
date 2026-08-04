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

admins = []  # فقط المطور

def is_admin(sender):
    return sender.username == DEVELOPER_USERNAME or sender.id in admins

async def is_group_admin(chat_id, user_id):
    try:
        perms = await client.get_permissions(chat_id, user_id)
        return perms.is_admin or perms.is_creator
    except:
        return False

# ============================================================
#  المتغيرات العامة
# ============================================================
client = TelegramClient('bot', API_ID, API_HASH)
BOT_PHOTO = None
API_TOKEN = "pipomaster2026"
mute_status = {}
bot_locked = False
private_locked = False
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
#  إدارة الكلمات الممنوعة
# ============================================================
BAD_WORDS_FILE = "bad_words.json"

def load_bad_words():
    default = [
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
        r'\b(كسمك|كسكم|طيزك|طيزكم|زبك|زبكم|نيكك|نيككم|شرموطة|شراميط|قحبة|قحبات|منيوك|منيوكة|مصطي|مصاطي|قلب|قلبوز|قلبوزة)\b',
        r'\b(يا[\s]*ابن[\s]*القحبة|يا[\s]*بنت[\s]*القحبة|يا[\s]*ولد[\s]*القحبة)\b',
        r'\b(انعل[\s]*ابوك|انعل[\s]*امك|انعل[\s]*دينك|انعل[\s]*ربك)\b',
        r'\b(يلعن[\s]*ابوك|يلعن[\s]*امك|يلعن[\s]*دينك|يلعن[\s]*ربك)\b',
    ]
    return load_json(BAD_WORDS_FILE, default)

def save_bad_words(words):
    save_json(BAD_WORDS_FILE, words)

BAD_WORDS = load_bad_words()

def contains_swear(t):
    return any(re.search(p, t, re.I) for p in BAD_WORDS) if t else False

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
#  إغلاق الخاص
# ============================================================
@client.on(events.NewMessage(func=lambda e: e.is_private))
async def private_handler(event):
    if private_locked and event.sender_id != DEVELOPER_ID:
        await event.reply("🔒 تم قفل خاص البوت بواسطة المطور.")
        # منع البوت من معالجة أي أمر آخر
        return
    # إذا كان الخاص مفتوحاً، دع البوت يكمل المعالجة العادية
# ============================================================
#  أوامر غلق وفتح الخاص (للمطور فقط)
# ============================================================
@client.on(events.NewMessage(pattern='^/غلق_الخاص$', from_users=DEVELOPER_ID))
async def lock_private(event):
    global private_locked
    private_locked = True
    await event.reply("🔒 تم قفل خاص البوت بنجاح.")

@client.on(events.NewMessage(pattern='^/فتح_الخاص$', from_users=DEVELOPER_ID))
async def unlock_private(event):
    global private_locked
    private_locked = False
    await event.reply("🔓 تم فتح خاص البوت بنجاح.")

# ============================================================
#  الرد على كلمة "بوت" في المجموعات
# ============================================================
@client.on(events.NewMessage(func=lambda e: e.is_group and e.raw_text and ('بوت' in e.raw_text or 'bot' in e.raw_text.lower())))
async def reply_to_bot(event):
    if event.chat_id not in active_groups:
        return
    sender = await event.get_sender()
    if sender.id == DEVELOPER_ID or is_admin(sender):
        return
    await event.reply("يا خو ما دصرنيش حبب")

# ============================================================
#  معالج السب
# ============================================================
@client.on(events.NewMessage())
async def swear_handler(event):
    if not event.is_group or event.chat_id not in active_groups:
        return
    sender = await event.get_sender()
    if sender.id == DEVELOPER_ID or is_admin(sender):
        return
    text = event.raw_text
    if text and contains_swear(text):
        await event.delete()
        await mute_user(event.chat_id, sender.id, 300)
        mute_status[sender.id] = {'until': time.time() + 300, 'name': sender.first_name or 'مجهول'}
        await event.reply(f"🚫 {sender.first_name or 'مجهول'} تم كتمه 5 دقائق بسبب السب.")

# ============================================================
#  باقي الميزات (منع الإباحية، البوت الحارس، مانع المكرر، الكابتشا)
# ============================================================
LINK_PATTERNS = [r'https?://\S+', r't\.me/\S+', r'www\.\S+']
PORN_KEYWORDS = ['sex', 'porn', 'xxx', 'nsfw', 'سكس', 'اباحية', 'جنس', 'porno', 'anal', 'بورن', 'shemale', 'trans', 'gay', 'lesbian', 'cum', 'orgasm', 'clit', 'dick', 'vagina', 'penis', 'breast', 'nude', 'naked', 'fuck', 'motherfucker', 'bitch', 'slut', 'whore']

def contains_link(t):
    return any(re.search(p, t, re.I) for p in LINK_PATTERNS) if t else False

def is_forward(m):
    return bool(m.forward)

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
#  الأزرار والتفاعلات العامة
# ============================================================
@client.on(events.CallbackQuery)
async def callback_handler(event):
    try:
        data = event.data.decode('utf-8')

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
        elif data == "back_to_start":
            await start(event)
        elif data.startswith("config_"):
            chat_id = int(data.split("_")[1])
            text, buttons = await generate_group_controls(chat_id)
            await event.edit(text, buttons=buttons)
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
    if event.is_private and private_locked and event.sender_id != DEVELOPER_ID:
        await event.reply("🔒 تم قفل خاص البوت بواسطة المطور.")
        return
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

        active_groups.add(int(chat))
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
    sender = await event.get_sender()
    # السماح للمطور أو أي مشرف في المجموعة
    if not is_admin(sender) and not await is_group_admin(event.chat_id, sender.id):
        await event.reply("❌ هذا الأمر للمشرفين فقط.")
        return
    active_groups.add(int(event.chat_id))
    save_groups()
    await event.reply("✅ تم تفعيل البوت في هذه المجموعة.\n🔹 تأكد من رفع البوت كمشرف ليعمل بشكل كامل.")

@client.on(events.NewMessage(pattern='^/تعطيل$'))
async def deactivate_group(event):
    sender = await event.get_sender()
    if not is_admin(sender) and not await is_group_admin(event.chat_id, sender.id):
        await event.reply("❌ هذا الأمر للمشرفين فقط.")
        return
    active_groups.discard(int(event.chat_id))
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
    sender = await event.get_sender()
    if not is_admin(sender) and not await is_group_admin(event.chat_id, sender.id):
        await event.reply("❌ هذا الأمر للمشرفين فقط.")
        return
    chat = event.chat_id
    rules_text = event.pattern_match.group(1)
    await set_rules(chat, rules_text)
    await event.reply("✅ تم تعيين القوانين بنجاح!")

# ============================================================
#  API كاملة للوحة التحكم
# ============================================================
async def health(request):
    return web.Response(text="OK")

async def control_panel(request):
    return web.FileResponse('control.html')

async def handle_api(request):
    token = request.headers.get('X-Bot-Token', '')
    if token != API_TOKEN:
        return web.json_response({'error': 'Unauthorized'}, status=403)
    path = request.path
    data = await request.json() if request.method == 'POST' else {}

    if path == '/api/stats':
        return web.json_response({
            'totalGroups': len(active_groups),
            'totalMuted': len([u for u in mute_status if mute_status[u]['until'] > time.time()]),
            'totalBanned': 0,
            'totalWarnings': sum(len(v) for v in warnings_data.values())
        })
    if path == '/api/muted':
        muted_list = []
        now = time.time()
        for uid, d in list(mute_status.items()):
            rem = int(d['until'] - now)
            if rem > 0:
                muted_list.append({'uid': uid, 'name': d.get('name', 'مجهول'), 'remaining': rem // 60, 'group': 'المجموعة', 'chat_id': 0})
        return web.json_response({'muted': muted_list})
    if path == '/api/unmute':
        uid = data.get('uid')
        if uid:
            try:
                for gid in active_groups:
                    await unmute_user(gid, uid)
                if uid in mute_status: del mute_status[uid]
                return web.json_response({'success': True})
            except: pass
        return web.json_response({'error': 'Failed'})
    if path == '/api/extendmute':
        uid = data.get('uid')
        minutes = data.get('minutes', 10)
        if uid:
            try:
                for gid in active_groups:
                    await mute_user(gid, uid, minutes * 60)
                if uid in mute_status:
                    mute_status[uid]['until'] = time.time() + (minutes * 60)
                else:
                    mute_status[uid] = {'until': time.time() + (minutes * 60), 'name': str(uid)}
                return web.json_response({'success': True})
            except: pass
        return web.json_response({'error': 'Failed'})
    if path == '/api/groups':
        groups = []
        for gid in active_groups:
            try:
                entity = await client.get_entity(gid)
                groups.append({'id': str(gid), 'name': entity.title})
            except:
                groups.append({'id': str(gid), 'name': str(gid)})
        return web.json_response({'groups': groups})
    if path == '/api/broadcast':
        msg = data.get('message', '')
        if not msg: return web.json_response({'error': 'No message'})
        c = 0
        for gid in active_groups:
            try:
                await client.send_message(gid, f"📢 {msg}\n👑 @{DEVELOPER_USERNAME}")
                c += 1
            except: pass
        return web.json_response({'success': True, 'count': c})
    if path == '/api/globalban':
        uid = data.get('user_id')
        remove = data.get('remove', False)
        if uid:
            if remove:
                for gid in active_groups:
                    try: await unban_user(gid, uid)
                    except: pass
            else:
                for gid in active_groups:
                    try: await ban_user(gid, uid)
                    except: pass
            return web.json_response({'success': True})
        return web.json_response({'error': 'No user_id'})
    if path == '/api/inactive':
        all_dialogs = []
        async for dialog in client.iter_dialogs():
            if dialog.is_group and dialog.id not in active_groups:
                all_dialogs.append({'id': dialog.id, 'name': dialog.title, 'active': dialog.id in active_groups})
        return web.json_response({'groups': all_dialogs[:50]})
    if path == '/api/activate':
        chat_id = data.get('chat_id')
        if chat_id:
            active_groups.add(int(chat_id))
            save_groups()
            return web.json_response({'success': True})
    if path == '/api/deactivate':
        chat_id = data.get('chat_id')
        if chat_id:
            active_groups.discard(int(chat_id))
            save_groups()
            return web.json_response({'success': True})
    if path == '/api/lock_status':
        return web.json_response({'locked': bot_locked})
    if path == '/api/toggle_lock':
        action = data.get('action', '')
        if action == 'lock':
            bot_locked = True
        elif action == 'unlock':
            bot_locked = False
        return web.json_response({'success': True, 'locked': bot_locked})
    if path == '/api/private_status':
        return web.json_response({'locked': private_locked})
    if path == '/api/toggle_private':
        action = data.get('action', '')
        if action == 'lock':
            private_locked = True
        elif action == 'unlock':
            private_locked = False
        return web.json_response({'success': True, 'locked': private_locked})
    if path == '/api/bad_words':
        return web.json_response({'words': BAD_WORDS})
    if path == '/api/add_bad_word':
        word = data.get('word', '').strip()
        if word:
            new_word = r'\b(' + re.escape(word) + r')\b'
            if new_word not in BAD_WORDS:
                BAD_WORDS.append(new_word)
                save_bad_words(BAD_WORDS)
                return web.json_response({'success': True})
            return web.json_response({'error': 'الكلمة موجودة مسبقاً'})
        return web.json_response({'error': 'كلمة فارغة'})
    if path == '/api/remove_bad_word':
        word = data.get('word', '').strip()
        if word:
            to_remove = r'\b(' + re.escape(word) + r')\b'
            if to_remove in BAD_WORDS:
                BAD_WORDS.remove(to_remove)
                save_bad_words(BAD_WORDS)
                return web.json_response({'success': True})
            return web.json_response({'error': 'الكلمة غير موجودة'})
        return web.json_response({'error': 'كلمة فارغة'})

    return web.json_response({'error': 'Unknown'})

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
        app.router.add_get('/', health)
        app.router.add_get('/control.html', control_panel)
        app.router.add_get('/api/stats', handle_api)
        app.router.add_get('/api/muted', handle_api)
        app.router.add_post('/api/unmute', handle_api)
        app.router.add_post('/api/extendmute', handle_api)
        app.router.add_get('/api/groups', handle_api)
        app.router.add_post('/api/broadcast', handle_api)
        app.router.add_post('/api/globalban', handle_api)
        app.router.add_get('/api/inactive', handle_api)
        app.router.add_post('/api/activate', handle_api)
        app.router.add_post('/api/deactivate', handle_api)
        app.router.add_get('/api/lock_status', handle_api)
        app.router.add_post('/api/toggle_lock', handle_api)
        app.router.add_get('/api/private_status', handle_api)
        app.router.add_post('/api/toggle_private', handle_api)
        app.router.add_get('/api/bad_words', handle_api)
        app.router.add_post('/api/add_bad_word', handle_api)
        app.router.add_post('/api/remove_bad_word', handle_api)

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
