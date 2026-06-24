import asyncio, os, time, random, datetime, re, sys, json
from collections import defaultdict
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights, InputPhoto, InputDocument

API_ID = 33938821
API_HASH = '24a5e855b4cf3ce48e054c32ea725aa4'
BOT_TOKEN = '8957362371:AAGC_GviR84bM0kl3Zmp4Ek9Okq56C9tWJM'
GROUP_ID = -1003498206246
CHANNEL_1 = -1003878407748
CHANNEL_2 = -1003008879375
CHANNEL_3 = -1003498206246
DEVELOPER_USERNAME = 'amirx_xpipo'
DEVELOPER_ID = 8050958688
PROTECTED_CHANNELS = [CHANNEL_1, CHANNEL_2, CHANNEL_3]

# ---- إعدادات المسؤولين ----
ADMINS_FILE = "admins.json"
DEFAULT_ADMINS = [6941580330]

def load_admins():
    try:
        if os.path.exists(ADMINS_FILE):
            with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return list(set(data.get('admins', DEFAULT_ADMINS)))
    except:
        pass
    return DEFAULT_ADMINS.copy()

def save_admins(admins_list):
    with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'admins': admins_list}, f, ensure_ascii=False, indent=2)

GROUP_ADMINS = load_admins()

def is_admin(sender):
    return sender.username == DEVELOPER_USERNAME or sender.id in GROUP_ADMINS

# ---- نظام التحذيرات ----
WARNINGS_FILE = "warnings.json"
warnings_data = defaultdict(list)

def load_warnings():
    global warnings_data
    try:
        if os.path.exists(WARNINGS_FILE):
            with open(WARNINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                warnings_data.clear()
                for k, v in data.items():
                    warnings_data[int(k)] = v
    except:
        pass

def save_warnings():
    with open(WARNINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump({str(k): v for k, v in warnings_data.items()}, f, ensure_ascii=False, indent=2)

MAX_WARNINGS = 3

# ---------------------------------

mute_status = {}
violation_count = defaultdict(int)
mute_duration = 300
link_protection = True
forward_protection = True
chat_locked = False
reminder_sent = False
last_muted_user = {}

WELCOME_MEDIA_DATA = None
WELCOME_MEDIA_TYPE = None
WELCOME_MEDIA_FILE = "welcome_media.json"
dev_media_mode = {}
DEV_VIDEO_DATA = None
DEV_VIDEO_FILE = "dev_video.json"

# ⭐⭐ كشف سب متطور (عربي + أرقام + رموز + إنجليزي معرب) ⭐⭐
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
    r'(ن[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*ي[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[كڪﻛﻚ6])',
    r'([كڪﻛﻚګگ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[سښصث5\$])',
    r'([ططـظظـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[يىېۍ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[زژڗژظڞ])',
    r'([زژڗژ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[ببـپپـ])',
    r'([قڨ9][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[ححـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[ببـپپـ])',
    r'(f[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[uوؤ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[cكڪ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[kكڪ])',
    r'([nن][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[i1!|][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[gج][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[gج][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[e3][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[rر])',
    r'\b(زبي|زبيي|كسك|طيزك|قحبتك|قحبتي)\b',
    r'\b(يا[\s]*ود[\s]*الكبدة|يا[\s]*ولد[\s]*القحبة|ولد[\s]*الزانية)\b',
    r'\b(نعل[\s]*الدين|نعل[\s]*الوالدين|نعل[\s]*الرب)\b',
    r'\b(الله[\s]*ينعل|الله[\s]*يلعن|ينعل[\s]*دين|يلعن[\s]*دين)\b',
    r'\b(ك\s*س|ك\s*ص|ط\s*ي\s*ز|ز\s*ب|ن\s*ي\s*ك|ق\s*ح\s*ب)\b',
    r'[كڪﻛﻚ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]?[سښصث]',
    r'[زژڗژ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]?[ببـپ]',
    r'[ننـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]?[يىېۍ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]?[كڪﻛﻚ]',
    r'[ننـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[مm][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[يىېۍ]',
    r'[ننـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*m[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*e[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[يىېۍ]',
    r'ن\s*م\s*ي',
]

LINK_PATTERNS = [
    r'https?://\S+', r't\.me/\S+', r'www\.\S+',
    r'\S+\.com\b', r'\S+\.net\b', r'\S+\.org\b',
]

def get_mute_message(name, username, duration):
    violator = f"@{username}" if username else name
    return f"""
╔══════════════════════════╗
║   🚫 تـم كـتـم عـضـو 🚫   ║
╠══════════════════════════╣
║ 👤 {violator}
║ ⏰ {duration} دقـائـق
║ 🤬 كـلـمـات مـمـنـوعـة
╠══════════════════════════╣
║ 👑 @{DEVELOPER_USERNAME}
╚══════════════════════════╝
"""

def get_welcome_message(name, user_id, username, group_title):
    now = datetime.datetime.now()
    return f"—————— {group_title} —————\nنورت قروبنا يا {name}!\nاسمك: {name}\nايديك: {user_id}\nيوزرك: @{username}\nتاريخ: {now.strftime('%Y/%m/%d %I:%M %p')}\n—————— {group_title} —————"

client = TelegramClient('bot', API_ID, API_HASH)
BOT_ID = None

def load_welcome_media():
    global WELCOME_MEDIA_DATA, WELCOME_MEDIA_TYPE
    try:
        if os.path.exists(WELCOME_MEDIA_FILE):
            with open(WELCOME_MEDIA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                WELCOME_MEDIA_TYPE = data.get('type')
                WELCOME_MEDIA_DATA = {'media_id': int(data.get('media_id', 0)), 'access_hash': int(data.get('access_hash', 0)), 'file_reference': data.get('file_reference', b'')}
                if WELCOME_MEDIA_DATA['media_id'] and WELCOME_MEDIA_DATA['access_hash']: return True
    except: pass
    return False

def load_dev_video():
    global DEV_VIDEO_DATA
    try:
        if os.path.exists(DEV_VIDEO_FILE):
            with open(DEV_VIDEO_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                DEV_VIDEO_DATA = {'media_id': int(data.get('media_id', 0)), 'access_hash': int(data.get('access_hash', 0)), 'file_reference': data.get('file_reference', b'')}
                if DEV_VIDEO_DATA['media_id'] and DEV_VIDEO_DATA['access_hash']: return True
    except: pass
    return False

async def save_dev_video(media):
    global DEV_VIDEO_DATA
    try:
        mid = media.document.id; ah = media.document.access_hash; fr = media.document.file_reference or b''
        DEV_VIDEO_DATA = {'media_id': str(mid), 'access_hash': str(ah), 'file_reference': fr.hex() if fr else ''}
        with open(DEV_VIDEO_FILE, 'w') as f: json.dump({'media_id': str(mid), 'access_hash': str(ah), 'file_reference': fr.hex() if fr else ''}, f)
        load_dev_video(); return True
    except: return False

async def send_dev_video(chat_id):
    try:
        fr = bytes.fromhex(DEV_VIDEO_DATA.get('file_reference', '')) if DEV_VIDEO_DATA.get('file_reference') else b''
        m = InputDocument(id=int(DEV_VIDEO_DATA['media_id']), access_hash=int(DEV_VIDEO_DATA['access_hash']), file_reference=fr)
        await client.send_file(chat_id, m, caption=f"Dev @{DEVELOPER_USERNAME}\n👑ℙ𝕚𝕡𝕠 ¹⁹\n📍 Sétif")
        return True
    except: return False

async def save_welcome_media(media, media_type):
    global WELCOME_MEDIA_DATA, WELCOME_MEDIA_TYPE
    try:
        WELCOME_MEDIA_TYPE = media_type
        if media_type == 'photo': mid = media.id; ah = media.access_hash; fr = media.file_reference or b''
        else: mid = media.document.id; ah = media.document.access_hash; fr = media.document.file_reference or b''
        WELCOME_MEDIA_DATA = {'media_id': str(mid), 'access_hash': str(ah), 'file_reference': fr.hex() if fr else ''}
        with open(WELCOME_MEDIA_FILE, 'w') as f: json.dump({'type': media_type, 'media_id': str(mid), 'access_hash': str(ah), 'file_reference': fr.hex() if fr else ''}, f)
        load_welcome_media(); return True
    except: return False

async def send_welcome_media(chat_id, caption):
    try:
        fr = bytes.fromhex(WELCOME_MEDIA_DATA.get('file_reference', '')) if WELCOME_MEDIA_DATA.get('file_reference') else b''
        if WELCOME_MEDIA_TYPE == 'photo': m = InputPhoto(id=int(WELCOME_MEDIA_DATA['media_id']), access_hash=int(WELCOME_MEDIA_DATA['access_hash']), file_reference=fr)
        else: m = InputDocument(id=int(WELCOME_MEDIA_DATA['media_id']), access_hash=int(WELCOME_MEDIA_DATA['access_hash']), file_reference=fr)
        await client.send_file(chat_id, m, caption=caption); return True
    except: return False

load_welcome_media()
load_dev_video()
load_warnings()

async def mute_user(chat_id, user_id, dur):
    try:
        r = ChatBannedRights(until_date=datetime.datetime.fromtimestamp(time.time() + dur), send_messages=True)
        await client(EditBannedRequest(chat_id, user_id, r)); return True
    except: return False

async def unmute_user(chat_id, user_id):
    try:
        r = ChatBannedRights(until_date=None, send_messages=False)
        await client(EditBannedRequest(chat_id, user_id, r)); return True
    except: return False

def contains_swear(text):
    if not text: return False
    for p in BAD_WORDS:
        if re.search(p, text, re.IGNORECASE): return True
    return False

def contains_link(text):
    if not text: return False
    for p in LINK_PATTERNS:
        if re.search(p, text, re.IGNORECASE): return True
    return False

def is_forward(msg): return bool(msg.forward)

# ======== الأوامر ========
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    s = await event.get_sender()
    if s.username == DEVELOPER_USERNAME:
        btns = [[Button.inline("🔇 مدة الكتم", b"mute_dur"), Button.inline("📊 حالة", b"bot_stat")],
                [Button.inline("🆔 الآيدي", b"get_id"), Button.inline("🔓 فك الكل", b"unmute_all_btn")]]
        try:
            photos = await client.get_profile_photos('me', limit=1)
            if photos: await client.send_file(event.chat_id, photos[0], caption=f"⚡ **PIPO BOT** ⚡\n👑 @{DEVELOPER_USERNAME}", buttons=btns); return
        except: pass
        await event.respond(f"⚡ **PIPO BOT** ⚡\n👑 @{DEVELOPER_USERNAME}", buttons=btns)
    else:
        await event.reply("ياحييي داصرتوني ثم ثم 😒")
        try: await client.send_reaction(event.chat_id, event.id, '💋')
        except: pass

@client.on(events.NewMessage(pattern='/قفل_المجموعة'))
async def lock_chat(event):
    if not is_admin(await event.get_sender()): return
    global chat_locked; chat_locked = True
    await client.edit_permissions(GROUP_ID, send_messages=False)
    await event.reply("🔒 تم قفل المجموعة")

@client.on(events.NewMessage(pattern='/فك_القفل'))
async def unlock_chat(event):
    if not is_admin(await event.get_sender()): return
    global chat_locked; chat_locked = False
    await client.edit_permissions(GROUP_ID, send_messages=True)
    await event.reply("🔓 تم فتح المجموعة")

@client.on(events.NewMessage(pattern='/المطور'))
async def dev_info(event):
    if DEV_VIDEO_DATA and await send_dev_video(event.chat_id): return
    await event.reply(f"Dev @{DEVELOPER_USERNAME}\n👑ℙ𝕚𝕡𝕠 ¹⁹\n📍 Sétif")

@client.on(events.NewMessage(pattern='/ايدي'))
async def get_id(event): await event.reply(f"`{event.chat_id}`")

@client.on(events.NewMessage(pattern='/حالة_الحماية'))
async def prot_stat(event):
    await event.reply(f"🛡️ الروابط: {'✅' if link_protection else '❌'} | التوجيه: {'✅' if forward_protection else '❌'} | السب: ✅ | القفل: {'🔒' if chat_locked else '🔓'}")

@client.on(events.NewMessage(pattern=r'/مدة_الكتم (\d+)'))
async def set_md(event):
    if not is_admin(await event.get_sender()): return
    global mute_duration; mute_duration = int(event.pattern_match.group(1)) * 60
    await event.reply(f"⏰ {mute_duration // 60} دقائق")

@client.on(events.NewMessage(pattern='/مدة_الكتم'))
async def sh_md(event): await event.reply(f"⏰ {mute_duration // 60} دقائق")

@client.on(events.NewMessage(pattern='/فك_كل_الكمات'))
async def unm_all(event):
    if not is_admin(await event.get_sender()): return
    c = 0
    for u in list(mute_status.keys()):
        try: await unmute_user(mute_status[u].get('chat', GROUP_ID), u); del mute_status[u]; c += 1
        except: pass
    await event.reply(f"✅ فك {c} كتم")

@client.on(events.NewMessage(pattern='/تفعيل_حماية_الروابط'))
async def en_l(event):
    if not is_admin(await event.get_sender()): return
    global link_protection; link_protection = True; await event.reply("✅ تم تفعيل حماية الروابط")

@client.on(events.NewMessage(pattern='/تعطيل_حماية_الروابط'))
async def dis_l(event):
    if not is_admin(await event.get_sender()): return
    global link_protection; link_protection = False; await event.reply("❌ تم تعطيل حماية الروابط")

@client.on(events.NewMessage(pattern='/تفعيل_حماية_التوجيه'))
async def en_f(event):
    if not is_admin(await event.get_sender()): return
    global forward_protection; forward_protection = True; await event.reply("✅ تم تفعيل حماية التوجيه")

@client.on(events.NewMessage(pattern='/تعطيل_حماية_التوجيه'))
async def dis_f(event):
    if not is_admin(await event.get_sender()): return
    global forward_protection; forward_protection = False; await event.reply("❌ تم تعطيل حماية التوجيه")

@client.on(events.NewMessage(pattern='/فيديو_المطور'))
async def sv_dev(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    dev_media_mode[(await event.get_sender()).id] = 'dev_video'
    await event.reply("📹 ارسل الفيديو في الخاص!")

@client.on(events.NewMessage(pattern='/فيديو_ترحيب'))
async def sv_wel(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    dev_media_mode[(await event.get_sender()).id] = 'welcome'
    await event.reply("ارسل الفيديو او الصورة في الخاص!")

@client.on(events.NewMessage(pattern='/احذف_كامل_الرسائل'))
async def del_all(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    if not event.is_private: return
    c = 0
    for ch in [GROUP_ID] + PROTECTED_CHANNELS:
        try:
            async for m in client.iter_messages(ch, from_user='me', limit=None):
                try: await m.delete(); c += 1
                except: pass
        except: pass
    await event.reply(f"✅ حذف {c} رسالة")

@client.on(events.NewMessage(pattern='/زيادة_المدة'))
async def inc_mute(event):
    if not is_admin(await event.get_sender()): return
    d = last_muted_user.get(event.chat_id)
    if not d: return
    btns = [[Button.inline("+10 د", f"add_{d['uid']}_10")],
            [Button.inline("+30 د", f"add_{d['uid']}_30")],
            [Button.inline("+1 س", f"add_{d['uid']}_60")]]
    await event.reply(f"⏰ زيادة كتم {d['name']}:", buttons=btns)

# ========== أمر /كتم (كتم دائم) ==========
@client.on(events.NewMessage(pattern='/كتم', func=lambda e: e.is_reply))
async def permanent_mute(event):
    sender = await event.get_sender()
    if not is_admin(sender):
        return

    replied = await event.get_reply_message()
    target = await replied.get_sender()
    if not target:
        await event.reply("❌ ما قدرتش نلقى العضو.")
        return

    ten_years = 10 * 365 * 24 * 3600
    await mute_user(event.chat_id, target.id, ten_years)

    name = target.first_name or "مجهول"
    username = target.username or "لا يوجد"
    mute_status[target.id] = {
        'until': time.time() + ten_years,
        'name': name,
        'chat': event.chat_id
    }
    last_muted_user[event.chat_id] = {
        'uid': target.id,
        'name': name,
        'username': username
    }

    msg = (
        f"هاك الكتمة يا {name} 😂❤️\n"
        f"سكّر فمك و خلّي تسمع غير صوت الهواء\n"
        f"حتّى تعقل و نرجع نفتحلك 👑 @{DEVELOPER_USERNAME}"
    )
    await event.reply(msg)

# ========== أمر /كتم_عن_بعد (خاص بالمطور في الخاص) ==========
@client.on(events.NewMessage(pattern=r'^/كتم_عن_بعد\s+(@?\w+)(?:\s+(.*))?', func=lambda e: e.is_private))
async def remote_mute(event):
    sender = await event.get_sender()
    if sender.username != DEVELOPER_USERNAME:
        return

    username = event.pattern_match.group(1).lstrip('@')
    custom_msg = event.pattern_match.group(2)
    if not custom_msg:
        await event.reply("❌ أكتب رسالة بعد اليوزر، مثال:\n/كتم_عن_بعد @username الرسالة")
        return

    try:
        entity = await client.get_entity(f"@{username}")
    except:
        await event.reply("❌ اليوزر غير موجود أو لا يمكن الوصول إليه.")
        return

    user_id = entity.id
    name = entity.first_name or username
    ten_years = 10 * 365 * 24 * 3600

    if await mute_user(GROUP_ID, user_id, ten_years):
        mute_status[user_id] = {
            'until': time.time() + ten_years,
            'name': name,
            'chat': GROUP_ID
        }
        last_muted_user[GROUP_ID] = {
            'uid': user_id,
            'name': name,
            'username': username
        }

        try:
            await client.send_message(user_id, custom_msg)
            await event.reply(f"✅ تم كتم {name} وإرسال الرسالة له.")
        except:
            await event.reply(f"✅ تم كتم {name} ولكن تعذر إرسال الرسالة (ربما حظر البوت).")
    else:
        await event.reply("❌ فشل كتم العضو، تأكد من صلاحيات البوت في المجموعة.")

# ========== أوامر المسؤولين (رفع / تنزيل) ==========
@client.on(events.NewMessage(pattern='/رفع_مسؤول'))
async def promote_admin(event):
    sender = await event.get_sender()
    if sender.username != DEVELOPER_USERNAME:
        return await event.reply("❌ هذا الأمر للمطور فقط.")

    target_id = None
    target_name = "مجهول"

    if event.is_reply:
        replied = await event.get_reply_message()
        target_user = await replied.get_sender()
        if target_user:
            target_id = target_user.id
            target_name = target_user.first_name or "لا اسم"
    else:
        args = event.raw_text.strip().split()
        if len(args) >= 2:
            try:
                target_id = int(args[1])
            except:
                return await event.reply("❌ استخدم: /رفع_مسؤول <id> أو بالرد على الشخص.")

    if not target_id:
        return await event.reply("❌ الرجاء الرد على رسالة الشخص أو كتابة الآيدي.")

    if target_id in GROUP_ADMINS:
        return await event.reply(f"⚠️ العضو {target_name} مسؤول بالفعل.")

    GROUP_ADMINS.append(target_id)
    save_admins(GROUP_ADMINS)
    await event.reply(f"✅ تم رفع {target_name} (ID: {target_id}) مسؤولاً في المجموعة.")

@client.on(events.NewMessage(pattern='/تنزيل_مسؤول'))
async def demote_admin(event):
    sender = await event.get_sender()
    if sender.username != DEVELOPER_USERNAME:
        return await event.reply("❌ هذا الأمر للمطور فقط.")

    target_id = None
    target_name = "مجهول"

    if event.is_reply:
        replied = await event.get_reply_message()
        target_user = await replied.get_sender()
        if target_user:
            target_id = target_user.id
            target_name = target_user.first_name or "لا اسم"
    else:
        args = event.raw_text.strip().split()
        if len(args) >= 2:
            try:
                target_id = int(args[1])
            except:
                return await event.reply("❌ استخدم: /تنزيل_مسؤول <id> أو بالرد على الشخص.")

    if not target_id:
        return await event.reply("❌ الرجاء الرد على رسالة الشخص أو كتابة الآيدي.")

    if target_id not in GROUP_ADMINS:
        return await event.reply(f"⚠️ العضو غير موجود في قائمة المسؤولين.")

    GROUP_ADMINS.remove(target_id)
    save_admins(GROUP_ADMINS)
    await event.reply(f"✅ تم تنزيل {target_name} (ID: {target_id}) من قائمة المسؤولين.")

# ----------- نظام التحذيرات -----------
@client.on(events.NewMessage(pattern='/تحذير'))
async def warn_user(event):
    if not is_admin(await event.get_sender()): return
    if not event.is_reply:
        return await event.reply("❌ يجب الرد على رسالة الشخص لتحذيره.")

    replied = await event.get_reply_message()
    target = await replied.get_sender()
    if not target:
        return await event.reply("❌ لا يمكن العثور على العضو.")

    uid = target.id
    name = target.first_name or "لا اسم"
    now_ts = time.time()
    warnings_data[uid].append(now_ts)
    save_warnings()
    current_warns = len(warnings_data[uid])

    await event.reply(f"⚠️ تم تحذير {name} - تحذير {current_warns}/{MAX_WARNINGS}")

    if current_warns >= MAX_WARNINGS:
        if await mute_user(event.chat_id, uid, mute_duration):
            mute_status[uid] = {'until': now_ts + mute_duration, 'name': name}
            await event.reply(f"🚫 {name} وصل لـ {MAX_WARNINGS} تحذيرات وتم كتمه {mute_duration//60} دقائق.")
            try:
                await client.send_message(uid, f"⚠️ لقد تم كتمك في المجموعة بسبب وصولك {MAX_WARNINGS} تحذيرات.\n👑 @{DEVELOPER_USERNAME}")
            except: pass
        else:
            await event.reply("❌ فشل كتم العضو.")
        del warnings_data[uid]
        save_warnings()

@client.on(events.NewMessage(pattern='/عرض_التحذيرات'))
async def show_warnings(event):
    target_id = None
    target_name = "مجهول"
    if event.is_reply:
        replied = await event.get_reply_message()
        u = await replied.get_sender()
        if u:
            target_id = u.id
            target_name = u.first_name or "لا اسم"
    else:
        args = event.raw_text.strip().split()
        if len(args) >= 2:
            try:
                target_id = int(args[1])
            except:
                return await event.reply("❌ استخدم /عرض_التحذيرات بالايدي أو بالرد.")

    if not target_id:
        return await event.reply("❌ الرجاء الرد على الشخص أو كتابة الآيدي.")

    warns = len(warnings_data.get(target_id, []))
    await event.reply(f"📊 {target_name} لديه {warns}/{MAX_WARNINGS} تحذيرات.")

# ----------- أوامر جديدة -----------
@client.on(events.NewMessage(pattern=r'^/مسح\s+(\d+)$'))
async def purge(event):
    if not is_admin(await event.get_sender()): return
    count = int(event.pattern_match.group(1))
    if count <= 0:
        return await event.reply("❌ العدد يجب أن يكون أكبر من صفر.")
    count = min(count, 100)
    try:
        messages = await client.get_messages(event.chat_id, limit=count)
        to_delete = [m.id for m in messages if m]
        await client.delete_messages(event.chat_id, to_delete)
        await asyncio.sleep(1)
        confirm = await event.reply(f"🧹 تم مسح {len(to_delete)} رسالة.")
        await asyncio.sleep(2)
        await confirm.delete()
    except Exception as e:
        await event.reply(f"❌ حدث خطأ: {str(e)}")

@client.on(events.NewMessage(pattern='/عرض_المكتومين'))
async def show_muted(event):
    if not mute_status:
        return await event.reply("✅ لا يوجد مكتومين حاليًا.")

    now = time.time()
    txt = "📋 **قائمة المكتومين:**\n\n"
    for uid, data in list(mute_status.items()):
        remaining = int(data['until'] - now)
        if remaining > 0:
            mins = remaining // 60
            try:
                entity = await client.get_entity(uid)
                name = entity.first_name or f"ID:{uid}"
            except:
                name = f"ID:{uid}"
            txt += f"• {name} - ⏳ {mins} دقيقة\n"

    await event.reply(txt if txt != "📋 **قائمة المكتومين:**\n\n" else "✅ لا يوجد مكتومين حاليًا.")

@client.on(events.NewMessage(pattern='/تثبيت'))
async def pin_msg(event):
    if not is_admin(await event.get_sender()): return
    if not event.is_reply:
        return await event.reply("❌ يجب الرد على رسالة لتثبيتها.")

    replied = await event.get_reply_message()
    try:
        await client.pin_message(event.chat_id, replied.id)
        await event.reply("📌 تم تثبيت الرسالة.")
    except Exception as e:
        await event.reply(f"❌ فشل التثبيت: {e}")

@client.on(events.NewMessage(pattern='/مساعدة'))
async def help_cmd(event):
    s = await event.get_sender()
    is_dev = s.username == DEVELOPER_USERNAME
    is_adm = is_admin(s)

    help_text = "**📜 قائمة الأوامر:**\n\n"
    if is_dev:
        help_text += """**⚡ أوامر المطور:**
/start - لوحة التحكم
/قفل_المجموعة - قفل المجموعة
/فك_القفل - فتح المجموعة
/كتم (بالرد) - كتم دائم
/كتم_عن_بعد (خاص) - كتم شخص عن بعد مع رسالة
/مدة_الكتم <دقائق> - تعيين مدة الكتم
/فك_كل_الكمات - فك كتم الجميع
/تفعيل_حماية_الروابط / تعطيل_حماية_الروابط
/تفعيل_حماية_التوجيه / تعطيل_حماية_التوجيه
/رفع_مسؤول / تنزيل_مسؤول
/زيادة_المدة - زيادة مدة آخر كتم
/تحذير (بالرد) - تحذير شخص
/عرض_التحذيرات - عرض التحذيرات
/مسح <عدد> - مسح الرسائل
/عرض_المكتومين - قائمة المكتومين
/تثبيت (بالرد) - تثبيت رسالة
/حالة_الحماية - عرض حالة الحماية
/المطور - معلومات المطور
/فيديو_المطور - تغيير فيديو المطور
/فيديو_ترحيب - تغيير وسائط الترحيب
/احذف_كامل_الرسائل - حذف كل رسائل البوت
"""
    elif is_adm:
        help_text += """**🛡️ أوامر المسؤولين:**
/قفل_المجموعة - قفل المجموعة
/فك_القفل - فتح المجموعة
/كتم (بالرد) - كتم دائم
/مدة_الكتم <دقائق> - تعيين مدة الكتم
/فك_كل_الكمات - فك كتم الجميع
/تفعيل_حماية_الروابط / تعطيل_حماية_الروابط
/تفعيل_حماية_التوجيه / تعطيل_حماية_التوجيه
/زيادة_المدة - زيادة مدة آخر كتم
/تحذير (بالرد) - تحذير شخص
/عرض_التحذيرات - عرض التحذيرات
/مسح <عدد> - مسح الرسائل
/عرض_المكتومين - قائمة المكتومين
/تثبيت (بالرد) - تثبيت رسالة
/حالة_الحماية - عرض حالة الحماية
"""
    else:
        help_text += """**👤 أوامر الأعضاء:**
/start - رسالة ترحيبية
/ايدي - معرف المجموعة
/مساعدة - هذه القائمة
"""
    await event.reply(help_text)

# ========== أزرار المطور ==========
@client.on(events.CallbackQuery)
async def all_btns(event):
    data = event.data.decode('utf-8')
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    if data.startswith("add_"):
        _, uid, mins = data.split("_"); uid = int(uid); mins = int(mins)
        await mute_user(GROUP_ID, uid, mins * 60)
        nm = last_muted_user.get(GROUP_ID, {}).get('name', 'مجهول')
        mute_status[uid] = {'until': time.time() + mins * 60, 'name': nm}
        await event.edit(f"✅ +{mins} دقائق لـ {nm}"); return
    if data == "mute_dur": await event.reply(f"⏰ {mute_duration // 60} دقائق")
    elif data == "bot_stat": await event.reply(f"📊 مكتوم: {len(mute_status)}")
    elif data == "get_id": await event.reply(f"🆔 {event.chat_id}")
    elif data == "unmute_all_btn":
        c = 0
        for u in list(mute_status.keys()):
            try: await unmute_user(mute_status[u].get('chat', GROUP_ID), u); del mute_status[u]; c += 1
            except: pass
        await event.reply(f"🔓 فك {c} كتم")

# ========== حماية المجموعة ==========
@client.on(events.NewMessage(chats=[GROUP_ID]))
async def handler(event):
    global link_protection, forward_protection, mute_duration
    if not event.raw_text or event.out: return
    s = await event.get_sender()
    if not s or s.id == BOT_ID: return
    if s.username == DEVELOPER_USERNAME: return
    t = event.raw_text.strip()
    if link_protection and contains_link(t): await event.delete(); return
    if forward_protection and is_forward(event.message): await event.delete(); return
    if contains_swear(t.lower()):
        now = time.time(); uid = s.id; name = s.first_name or "مجهول"
        if uid in mute_status and mute_status[uid]['until'] > now: return
        await event.delete()
        await mute_user(GROUP_ID, uid, mute_duration)
        mute_status[uid] = {'until': now + mute_duration, 'name': name}
        last_muted_user[GROUP_ID] = {'uid': uid, 'name': name, 'username': s.username}
        await event.respond(get_mute_message(name, s.username, mute_duration // 60))
        try: await client.send_message(uid, f"⚠️ تم كتمك {mute_duration // 60} دقائق\n🤬 الكلمة: `{t}`\n👑 @{DEVELOPER_USERNAME}")
        except: pass

@client.on(events.NewMessage(func=lambda e: e.is_private and e.media))
async def media_handler(event):
    s = await event.get_sender()
    if s.username != DEVELOPER_USERNAME: return
    m = event.media; mode = dev_media_mode.get(s.id, 'welcome')
    if mode == 'dev_video':
        if hasattr(m, 'document') and 'video' in m.document.mime_type.lower():
            if await save_dev_video(m): await event.reply("✅ تم الحفظ!")
        if s.id in dev_media_mode: del dev_media_mode[s.id]; return
    mt = None
    if hasattr(m, 'photo') and m.photo: mt = 'photo'
    elif hasattr(m, 'document') and 'video' in m.document.mime_type.lower(): mt = 'video'
    if mt and await save_welcome_media(m, mt): await event.reply(f"✅ تم حفظ {mt}!")
    if s.id in dev_media_mode: del dev_media_mode[s.id]

@client.on(events.NewMessage(func=lambda e: e.is_private))
async def pv(event): pass

@client.on(events.ChatAction())
async def welcome(event):
    if event.user_joined:
        u = await event.get_user()
        if not u.bot:
            await asyncio.sleep(3)
            try: c = await event.get_chat(); t = c.title
            except: t = "SUICIDE SQUAD"
            msg = get_welcome_message(u.first_name or "لاعب", u.id, u.username or "لايوجد", t)
            if WELCOME_MEDIA_DATA and WELCOME_MEDIA_TYPE:
                if await send_welcome_media(event.chat_id, msg): return
            await client.send_message(event.chat_id, msg)

async def auto_lock_unlock():
    global chat_locked, reminder_sent
    while True:
        now = datetime.datetime.now(); h, m = now.hour, now.minute
        if h == 22 and m == 30 and not reminder_sent and not chat_locked:
            reminder_sent = True
            try: await client.send_message(GROUP_ID, f"⚠️ باقي 30 دقيقة على القفل\n👑 @{DEVELOPER_USERNAME}")
            except: pass
        if h == 23 and m == 0 and not chat_locked:
            chat_locked = True; reminder_sent = False
            try:
                await client.edit_permissions(GROUP_ID, send_messages=False)
                await client.send_message(GROUP_ID, f"🔒 تم إغلاق المحادثة - 12:00 ليلاً\n🔓 الفتح: 10:00 صباحاً\n👑 @{DEVELOPER_USERNAME}")
            except: pass
        if h == 9 and m == 0 and chat_locked:
            chat_locked = False
            try:
                await client.edit_permissions(GROUP_ID, send_messages=True)
                await client.send_message(GROUP_ID, f"🔓 تم فتح المحادثة - 10:00 صباحاً\n👑 @{DEVELOPER_USERNAME}")
            except: pass
        await asyncio.sleep(30)

async def auto_unmute():
    while True:
        now = time.time()
        for uid in list(mute_status.keys()):
            if mute_status[uid]['until'] < now:
                try: await unmute_user(GROUP_ID, uid); del mute_status[uid]
                except: pass
        await asyncio.sleep(30)

async def main():
    global BOT_ID
    await client.start(bot_token=BOT_TOKEN)
    me = await client.get_me()
    BOT_ID = me.id
    global chat_locked
    try:
        await client.edit_permissions(GROUP_ID, send_messages=True)
        chat_locked = False
    except: pass
    print(f"✅ PIPO BOT: @{me.username}")
    asyncio.create_task(auto_unmute())
    asyncio.create_task(auto_lock_unlock())
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
