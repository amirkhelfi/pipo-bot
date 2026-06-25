import asyncio, os, time, random, datetime, re, sys, json
from collections import defaultdict
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights, InputPhoto, InputDocument

# ---------- الإعدادات ----------
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

ADMINS_FILE = "admins.json"
DEFAULT_ADMINS = [6941580330]

def load_admins():
    try:
        if os.path.exists(ADMINS_FILE):
            with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return list(set(data.get('admins', DEFAULT_ADMINS)))
    except: pass
    return DEFAULT_ADMINS.copy()

def save_admins(lst):
    with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'admins': lst}, f, ensure_ascii=False, indent=2)

GROUP_ADMINS = load_admins()

def is_admin(sender):
    return sender.username == DEVELOPER_USERNAME or sender.id in GROUP_ADMINS

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
    except: pass

def save_warnings():
    with open(WARNINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump({str(k): v for k, v in warnings_data.items()}, f, ensure_ascii=False, indent=2)

MAX_WARNINGS = 3

# ---------- دوال الزخرفة ----------
def zakhrif(text):
    eng_map = {
        'A':'𝓐','B':'𝓑','C':'𝓒','D':'𝓓','E':'𝓔','F':'𝓕','G':'𝓖','H':'𝓗','I':'𝓘','J':'𝓙',
        'K':'𝓚','L':'𝓛','M':'𝓜','N':'𝓝','O':'𝓞','P':'𝓟','Q':'𝓠','R':'𝓡','S':'𝓢','T':'𝓣',
        'U':'𝓤','V':'𝓥','W':'𝓦','X':'𝓧','Y':'𝓨','Z':'𝓩',
        'a':'𝓪','b':'𝓫','c':'𝓬','d':'𝓭','e':'𝓮','f':'𝓯','g':'𝓰','h':'𝓱','i':'𝓲','j':'𝓳',
        'k':'𝓴','l':'𝓵','m':'𝓶','n':'𝓷','o':'𝓸','p':'𝓹','q':'𝓺','r':'𝓻','s':'𝓼','t':'𝓽',
        'u':'𝓾','v':'𝓿','w':'𝔀','x':'𝔁','y':'𝔂','z':'𝔃',
        '0':'𝟬','1':'𝟭','2':'𝟮','3':'𝟯','4':'𝟰','5':'𝟱','6':'𝟲','7':'𝟳','8':'𝟴','9':'𝟵'
    }
    arab_map = {
        'ا':'𑇟','ب':'𑇡','ت':'𑇥','ث':'𑇧','ج':'𑇨','ح':'𑇩','خ':'𑇪',
        'د':'𑇫','ذ':'𑇬','ر':'𑇭','ز':'𑇮','س':'𑇯','ش':'𑇰','ص':'𑇱',
        'ض':'𑇲','ط':'𑇳','ظ':'𑇴','ع':'𑇵','غ':'𑇶','ف':'𑇷','ق':'𑇸',
        'ك':'𑇹','ل':'𑇺','م':'𑇻','ن':'𑇼','ه':'𑇽','و':'𑇾','ي':'𑇿'
    }
    result = []
    for ch in text:
        if ch in eng_map:
            result.append(eng_map[ch])
        elif ch in arab_map:
            result.append(arab_map[ch])
        else:
            result.append(ch)
    return f"『 {''.join(result)} 』"

async def reply_decorated(event, text, emoji="🌟"):
    await event.reply(f"{emoji} {zakhrif(text)} {emoji}")

# ---------- المتغيرات العامة ----------
client = TelegramClient('bot', API_ID, API_HASH)
BOT_ID = None
mute_status = {}
message_count = defaultdict(int)
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

def get_mute_message(name, username, duration):
    violator = f"@{username}" if username else name
    return f"🚫 {violator} | ⏰ {duration} د"

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

# ---------- الأوامر ----------
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    s = await event.get_sender()
    if s.username == DEVELOPER_USERNAME:
        btns = [[Button.inline("🔇 مدة الكتم", b"mute_dur"), Button.inline("📊 حالة", b"bot_stat")],
                [Button.inline("🆔 الآيدي", b"get_id"), Button.inline("🔓 فك الكل", b"unmute_all_btn")]]
        await event.reply(f"🌟 {zakhrif(f'⚡ PIPO BOT ⚡ 👑 @{DEVELOPER_USERNAME}')} 🌟", buttons=btns)
    else:
        await reply_decorated(event, "ياحييي داصرتوني ثم ثم", "💋")

@client.on(events.NewMessage(pattern='/قفل_المجموعة'))
async def lock_chat(event):
    if not is_admin(await event.get_sender()): return
    global chat_locked; chat_locked = True
    await client.edit_permissions(GROUP_ID, send_messages=False)
    await reply_decorated(event, "🔒 تم قفل المجموعة", "🔐")

@client.on(events.NewMessage(pattern='/فك_القفل'))
async def unlock_chat(event):
    if not is_admin(await event.get_sender()): return
    global chat_locked; chat_locked = False
    await client.edit_permissions(GROUP_ID, send_messages=True)
    await reply_decorated(event, "🔓 تم فتح المجموعة", "🔓")

@client.on(events.NewMessage(pattern='/المطور'))
async def dev_info(event):
    await event.reply(zakhrif(f"Dev @{DEVELOPER_USERNAME} 👑ℙ𝕚𝕡𝕠 ¹⁹ 📍 Sétif"))

@client.on(events.NewMessage(pattern='/ايدي'))
async def get_id(event): await event.reply(zakhrif(f"`{event.chat_id}`"))

@client.on(events.NewMessage(pattern='/حالة_الحماية'))
async def prot_stat(event):
    await reply_decorated(event, f"🛡️ الروابط: {'✅' if link_protection else '❌'} | التوجيه: {'✅' if forward_protection else '❌'} | السب: ✅ | القفل: {'🔒' if chat_locked else '🔓'}", "📊")

@client.on(events.NewMessage(pattern=r'/مدة_الكتم (\d+)'))
async def set_md(event):
    if not is_admin(await event.get_sender()): return
    global mute_duration; mute_duration = int(event.pattern_match.group(1)) * 60
    await reply_decorated(event, f"⏰ {mute_duration // 60} دقائق", "⏳")

@client.on(events.NewMessage(pattern='/مدة_الكتم'))
async def sh_md(event): await reply_decorated(event, f"⏰ {mute_duration // 60} دقائق", "⏳")

@client.on(events.NewMessage(pattern='/فك_كل_الكمات'))
async def unm_all(event):
    if not is_admin(await event.get_sender()): return
    c = 0
    for u in list(mute_status.keys()):
        try: await unmute_user(GROUP_ID, u); del mute_status[u]; c += 1
        except: pass
    await reply_decorated(event, f"✅ فك {c} كتم", "🔊")

@client.on(events.NewMessage(pattern='/تفعيل_حماية_الروابط'))
async def en_l(event):
    if not is_admin(await event.get_sender()): return
    global link_protection; link_protection = True
    await reply_decorated(event, "✅ تم تفعيل حماية الروابط", "🛡️")

@client.on(events.NewMessage(pattern='/تعطيل_حماية_الروابط'))
async def dis_l(event):
    if not is_admin(await event.get_sender()): return
    global link_protection; link_protection = False
    await reply_decorated(event, "❌ تم تعطيل حماية الروابط", "⚠️")

@client.on(events.NewMessage(pattern='/تفعيل_حماية_التوجيه'))
async def en_f(event):
    if not is_admin(await event.get_sender()): return
    global forward_protection; forward_protection = True
    await reply_decorated(event, "✅ تم تفعيل حماية التوجيه", "🛡️")

@client.on(events.NewMessage(pattern='/تعطيل_حماية_التوجيه'))
async def dis_f(event):
    if not is_admin(await event.get_sender()): return
    global forward_protection; forward_protection = False
    await reply_decorated(event, "❌ تم تعطيل حماية التوجيه", "⚠️")

@client.on(events.NewMessage(pattern='/زيادة_المدة'))
async def inc_mute(event):
    if not is_admin(await event.get_sender()): return
    d = last_muted_user.get(event.chat_id)
    if not d: return
    btns = [[Button.inline("+10 د", f"add_{d['uid']}_10"), Button.inline("+30 د", f"add_{d['uid']}_30"), Button.inline("+1 س", f"add_{d['uid']}_60")]]
    await event.reply(zakhrif(f"⏰ زيادة كتم {d['name']}:"), buttons=btns)

@client.on(events.NewMessage(pattern='/كتم', func=lambda e: e.is_reply))
async def permanent_mute(event):
    if not is_admin(await event.get_sender()): return
    target = await (await event.get_reply_message()).get_sender()
    if not target: return await event.reply("❌ العضو غير موجود")
    ten_years = 10*365*24*3600
    await mute_user(event.chat_id, target.id, ten_years)
    mute_status[target.id] = {'until': time.time() + ten_years, 'name': target.first_name}
    last_muted_user[event.chat_id] = {'uid': target.id, 'name': target.first_name, 'username': target.username}
    await reply_decorated(event, f"هاك الكتمة يا {target.first_name} 😂❤️\nسكّر فمك و خلّي تسمع غير صوت الهواء\nحتّى تعقل و نرجع نفتحلك 👑 @{DEVELOPER_USERNAME}", "🚫")

@client.on(events.NewMessage(pattern=r'^/كتم_عن_بعد\s+(@?\w+)(?:\s+(.*))?', func=lambda e: e.is_private))
async def remote_mute(event):
    sender = await event.get_sender()
    if sender.username != DEVELOPER_USERNAME: return
    username = event.pattern_match.group(1).lstrip('@')
    custom_msg = event.pattern_match.group(2)
    if not custom_msg:
        await event.reply("❌ أكتب رسالة بعد اليوزر")
        return
    try:
        entity = await client.get_entity(f"@{username}")
    except:
        await event.reply("❌ اليوزر غير موجود"); return
    ten_years = 10*365*24*3600
    if await mute_user(GROUP_ID, entity.id, ten_years):
        mute_status[entity.id] = {'until': time.time() + ten_years, 'name': entity.first_name}
        try:
            await client.send_message(entity.id, custom_msg)
            await event.reply(f"✅ تم كتم {entity.first_name} وإرسال الرسالة.")
        except:
            await event.reply(f"✅ تم الكتم لكن تعذر إرسال الرسالة.")
    else:
        await event.reply("❌ فشل الكتم")

@client.on(events.NewMessage(pattern='/رفع_مسؤول'))
async def promote_admin(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    target_id = None; target_name = ""
    if event.is_reply:
        u = await (await event.get_reply_message()).get_sender()
        if u: target_id = u.id; target_name = u.first_name
    else:
        args = event.raw_text.split()
        if len(args) >= 2:
            try: target_id = int(args[1])
            except: pass
    if not target_id: return await event.reply("❌ أرسل الأمر مع معرف العضو")
    if target_id in GROUP_ADMINS: return await event.reply("⚠️ مسؤول بالفعل")
    GROUP_ADMINS.append(target_id); save_admins(GROUP_ADMINS)
    await reply_decorated(event, f"✅ تم رفع {target_name or target_id} مسؤولاً", "👑")

@client.on(events.NewMessage(pattern='/تنزيل_مسؤول'))
async def demote_admin(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    target_id = None
    if event.is_reply:
        u = await (await event.get_reply_message()).get_sender()
        if u: target_id = u.id
    else:
        args = event.raw_text.split()
        if len(args) >= 2:
            try: target_id = int(args[1])
            except: pass
    if not target_id: return await event.reply("❌ أرسل الأمر مع معرف العضو")
    if target_id not in GROUP_ADMINS: return await event.reply("⚠️ ليس مسؤولاً")
    GROUP_ADMINS.remove(target_id); save_admins(GROUP_ADMINS)
    await reply_decorated(event, "✅ تم تنزيله من المسؤولين", "👋")

@client.on(events.NewMessage(pattern='/تحذير'))
async def warn_user(event):
    if not is_admin(await event.get_sender()): return
    if not event.is_reply: return await event.reply("❌ يجب الرد على الشخص")
    target = await (await event.get_reply_message()).get_sender()
    if not target: return
    uid = target.id; name = target.first_name or "لا اسم"
    now_ts = time.time()
    warnings_data[uid].append(now_ts); save_warnings()
    cur = len(warnings_data[uid])
    await reply_decorated(event, f"⚠️ {name} تحذير {cur}/{MAX_WARNINGS}", "⚠️")
    if cur >= MAX_WARNINGS:
        if await mute_user(event.chat_id, uid, mute_duration):
            mute_status[uid] = {'until': now_ts + mute_duration, 'name': name}
            await reply_decorated(event, f"🚫 {name} كتم {mute_duration//60} د", "🚫")
            try: await client.send_message(uid, f"⚠️ تم كتمك بعد {MAX_WARNINGS} تحذيرات")
            except: pass
        del warnings_data[uid]; save_warnings()

@client.on(events.NewMessage(pattern='/عرض_التحذيرات'))
async def show_warn(event):
    target_id = None; target_name = ""
    if event.is_reply:
        u = await (await event.get_reply_message()).get_sender()
        if u: target_id = u.id; target_name = u.first_name
    else:
        args = event.raw_text.split()
        if len(args) >= 2:
            try: target_id = int(args[1])
            except: pass
    if not target_id: return await event.reply("❌ استخدم الأمر مع معرف أو رد")
    c = len(warnings_data.get(target_id, []))
    await reply_decorated(event, f"📊 {target_name or target_id} لديه {c}/{MAX_WARNINGS} تحذيرات", "📋")

@client.on(events.NewMessage(pattern=r'^/مسح\s+(\d+)$'))
async def purge(event):
    if not is_admin(await event.get_sender()): return
    count = min(int(event.pattern_match.group(1)), 100)
    if count <= 0: return
    msgs = await client.get_messages(event.chat_id, limit=count)
    ids = [m.id for m in msgs if m]
    await client.delete_messages(event.chat_id, ids)
    confirm = await event.reply(f"🧹 {zakhrif(f'مسح {len(ids)} رسالة')}")
    await asyncio.sleep(2); await confirm.delete()

@client.on(events.NewMessage(pattern='/عرض_المكتومين'))
async def muted_list(event):
    if not mute_status: return await reply_decorated(event, "✅ لا يوجد مكتومين", "🔊")
    now = time.time(); txt = "📋 المكتومين:\n"
    for uid, d in mute_status.items():
        rem = int(d['until'] - now)
        if rem > 0:
            try: name = (await client.get_entity(uid)).first_name
            except: name = str(uid)
            txt += f"• {name} - ⏳ {rem//60} د\n"
    await event.reply(zakhrif(txt))

@client.on(events.NewMessage(pattern='/تثبيت'))
async def pin_msg(event):
    if not is_admin(await event.get_sender()): return
    if not event.is_reply: return await event.reply("❌ رد على رسالة")
    replied = await event.get_reply_message()
    try:
        await client.pin_message(event.chat_id, replied.id)
        await reply_decorated(event, "📌 تم التثبيت", "📌")
    except Exception as e:
        await event.reply(f"❌ فشل: {e}")

@client.on(events.NewMessage(pattern='/توب_المتفاعلين'))
async def top_members(event):
    if not message_count: return await reply_decorated(event, "لا توجد إحصائيات بعد", "📊")
    sorted_items = sorted(message_count.items(), key=lambda x: x[1], reverse=True)[:5]
    if not sorted_items: return
    txt = "🏆 توب المتفاعلين:\n"
    for i, (uid, cnt) in enumerate(sorted_items, 1):
        try: name = (await client.get_entity(uid)).first_name
        except: name = str(uid)
        txt += f"{i}. {name} - {cnt} رسالة\n"
    await event.reply(zakhrif(txt))

@client.on(events.NewMessage(pattern='/مساعدة'))
async def help_cmd(event):
    buttons = [
        [Button.inline("👤 الأعضاء", b"help_member")],
        [Button.inline("🛡️ المسؤول", b"help_admin")],
        [Button.inline("⚡ المطور", b"help_dev")],
    ]
    await event.reply("📜 اختر فئة الأوامر:", buttons=buttons)

@client.on(events.CallbackQuery)
async def on_callback(event):
    data = event.data.decode('utf-8')
    if data == "help_dev":
        txt = "⚡ أوامر المطور:\n/start /قفل /فك /كتم /كتم_عن_بعد /مدة_الكتم /فك_كل /حماية /رفع_مسؤول /تنزيل_مسؤول /تحذير /مسح /عرض_المكتومين /تثبيت /مساعدة /المطور /فيديو_المطور /فيديو_ترحيب /احذف"
    elif data == "help_admin":
        txt = "🛡️ أوامر المسؤول:\n/قفل /فك /كتم /مدة_الكتم /فك_كل /حماية /زيادة_المدة /تحذير /مسح /عرض_المكتومين /تثبيت /مساعدة"
    elif data == "help_member":
        txt = "👤 أوامر الأعضاء:\n/start /ايدي /توب_المتفاعلين /مساعدة"
    elif data.startswith("add_"):
        if (await event.get_sender()).username != DEVELOPER_USERNAME: return
        _, uid, mins = data.split("_"); uid = int(uid); mins = int(mins)
        await mute_user(GROUP_ID, uid, mins * 60)
        mute_status[uid] = {'until': time.time() + mins * 60}
        await event.edit(zakhrif(f"✅ +{mins} دقائق"))
        return
    elif data == "mute_dur":
        await event.reply(zakhrif(f"⏰ {mute_duration//60} د"))
        return
    elif data == "bot_stat":
        await event.reply(zakhrif(f"📊 مكتوم: {len(mute_status)}"))
        return
    elif data == "get_id":
        await event.reply(zakhrif(f"🆔 {event.chat_id}"))
        return
    elif data == "unmute_all_btn":
        for u in list(mute_status.keys()):
            try: await unmute_user(GROUP_ID, u); del mute_status[u]
            except: pass
        await event.reply(zakhrif("🔓 فك الكل"))
        return
    else:
        return
    await event.edit(zakhrif(txt))

# ---------- حماية المجموعة ----------
@client.on(events.NewMessage(chats=[GROUP_ID]))
async def handler(event):
    global link_protection, forward_protection, mute_duration
    if not event.raw_text or event.out: return
    s = await event.get_sender()
    if not s or s.id == BOT_ID: return
    if s.username == DEVELOPER_USERNAME: return
    message_count[s.id] += 1
    t = event.raw_text.strip()
    if link_protection and contains_link(t): await event.delete(); return
    if forward_protection and is_forward(event.message): await event.delete(); return
    if contains_swear(t.lower()):
        now = time.time(); uid = s.id; name = s.first_name or "مجهول"
        if uid in mute_status and mute_status[uid]['until'] > now: return
        await event.delete()
        await mute_user(GROUP_ID, uid, mute_duration)
        mute_status[uid] = {'until': now + mute_duration, 'name': name}
        await event.respond(f"🚫 {zakhrif(f'{name} كتم {mute_duration//60} د')}")

# ---------- الترحيب والأتمتة ----------
@client.on(events.ChatAction())
async def welcome(event):
    if event.user_joined:
        u = await event.get_user()
        if not u.bot:
            await asyncio.sleep(3)
            try: t = (await event.get_chat()).title
            except: t = "SUICIDE SQUAD"
            msg = f"—————— {t} —————\nنورت قروبنا يا {u.first_name}!\nايديك: {u.id}\nيوزرك: @{u.username or 'لايوجد'}\nتاريخ: {datetime.datetime.now().strftime('%Y/%m/%d %I:%M %p')}\n—————— {t} —————"
            await client.send_message(event.chat_id, zakhrif(msg))

async def auto_lock_unlock():
    global chat_locked, reminder_sent
    while True:
        now = datetime.datetime.now(); h, m = now.hour, now.minute
        if h == 22 and m == 30 and not reminder_sent and not chat_locked:
            reminder_sent = True
            try: await client.send_message(GROUP_ID, zakhrif(f"⚠️ باقي 30 دقيقة على القفل\n👑 @{DEVELOPER_USERNAME}"))
            except: pass
        if h == 23 and m == 0 and not chat_locked:
            chat_locked = True; reminder_sent = False
            try:
                await client.edit_permissions(GROUP_ID, send_messages=False)
                await client.send_message(GROUP_ID, zakhrif(f"🔒 تم إغلاق المحادثة - 12:00 ليلاً\n🔓 الفتح: 10:00 صباحاً\n👑 @{DEVELOPER_USERNAME}"))
            except: pass
        if h == 9 and m == 0 and chat_locked:
            chat_locked = False
            try:
                await client.edit_permissions(GROUP_ID, send_messages=True)
                await client.send_message(GROUP_ID, zakhrif(f"🔓 تم فتح المحادثة - 10:00 صباحاً\n👑 @{DEVELOPER_USERNAME}"))
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
