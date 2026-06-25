import asyncio, os, time, random, datetime, re, sys, json
from collections import defaultdict
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights

API_ID = 33938821
API_HASH = '24a5e855b4cf3ce48e054c32ea725aa4'
BOT_TOKEN = '8957362371:AAGC_GviR84bM0kl3Zmp4Ek9Okq56C9tWJM'
GROUP_ID = -1003498206246
DEVELOPER_USERNAME = 'amirx_xpipo'
DEVELOPER_ID = 8050958688

ADMINS_FILE = "admins.json"
RULES_FILE = "rules.txt"
DEFAULT_ADMINS = [6941580330]

def load_admins():
    try:
        if os.path.exists(ADMINS_FILE):
            with open(ADMINS_FILE, 'r') as f:
                return list(set(json.load(f).get('admins', DEFAULT_ADMINS)))
    except: pass
    return DEFAULT_ADMINS.copy()

def save_admins(lst):
    with open(ADMINS_FILE, 'w') as f:
        json.dump({'admins': lst}, f)

GROUP_ADMINS = load_admins()
def is_admin(sender): return sender.username == DEVELOPER_USERNAME or sender.id in GROUP_ADMINS

WARNINGS_FILE = "warnings.json"
warnings_data = defaultdict(list)
def load_warnings():
    global warnings_data
    try:
        if os.path.exists(WARNINGS_FILE):
            with open(WARNINGS_FILE, 'r') as f:
                for k,v in json.load(f).items(): warnings_data[int(k)] = v
    except: pass
def save_warnings():
    with open(WARNINGS_FILE, 'w') as f:
        json.dump({str(k):v for k,v in warnings_data.items()}, f)

MAX_WARNINGS = 3
mute_status = {}
message_count = defaultdict(int)
mute_duration = 300
link_protection = True
forward_protection = True
chat_locked = False
last_muted_user = {}
client = TelegramClient('bot', API_ID, API_HASH)

reply_requests = {}

# ========== كشف السب المتطور ==========
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
    r'ن[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*ي[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[كڪﻛﻚ6]',
    r'[كڪﻛﻚګگ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[سښصث5\$]',
    r'[ططـظظـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[يىېۍ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[زژڗژظڞ]',
    r'[زژڗژ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[ببـپپـ]',
    r'[قڨ9][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[ححـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[ببـپپـ]',
    r'f[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[uوؤ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[cكڪ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[kكڪ]',
    r'[nن][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[i1!|][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[gج][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[gج][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[e3][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[rر]',
    r'\b(زبي|زبيي|كسك|طيزك|قحبتك|قحبتي)\b',
    r'\b(يا[\s]*ود[\s]*الكبدة|يا[\s]*ولد[\s]*القحبة|ولد[\s]*الزانية)\b',
    r'\b(نعل[\s]*الدين|نعل[\s]*الوالدين|نعل[\s]*الرب)\b',
    r'\b(الله[\s]*ينعل|الله[\s]*يلعن|ينعل[\s]*دين|يلعن[\s]*دين)\b',
    r'ن\s*م\s*ي',
    r'[ننـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[مm][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[يىېۍ]',
    r'[ننـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*m[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*e[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[يىېۍ]',
]

LINK_PATTERNS = [r'https?://\S+', r't\.me/\S+', r'www\.\S+']

def contains_swear(t): return any(re.search(p, t, re.I) for p in BAD_WORDS) if t else False
def contains_link(t): return any(re.search(p, t, re.I) for p in LINK_PATTERNS) if t else False
def is_forward(m): return bool(m.forward)

async def mute_user(c, u, d):
    try: await client(EditBannedRequest(c, u, ChatBannedRights(until_date=datetime.datetime.fromtimestamp(time.time()+d), send_messages=True))); return True
    except: return False
async def unmute_user(c, u):
    try: await client(EditBannedRequest(c, u, ChatBannedRights(until_date=None, send_messages=False))); return True
    except: return False

# ========== الرد عبر التوجيه (مصحح) ==========
@client.on(events.NewMessage(func=lambda e: e.is_private and e.forward))
async def forward_handler(event):
    s = await event.get_sender()
    if not is_admin(s): return

    fwd_from = event.message.fwd_from
    if not fwd_from:
        return await event.reply("❌ الرسالة لا تحتوي على معلومات التوجيه.")

    orig_chat = None
    orig_msg = fwd_from.channel_post

    from_peer = fwd_from.from_id
    if from_peer:
        if hasattr(from_peer, 'channel_id'):
            orig_chat = from_peer.channel_id
        elif hasattr(from_peer, 'chat_id'):
            orig_chat = from_peer.chat_id

    if not orig_chat or not orig_msg:
        return await event.reply("❌ لم أتمكن من تحديد المجموعة أو الرسالة الأصلية.")

    if orig_chat != GROUP_ID:
        return await event.reply("❌ يمكنك فقط توجيه رسائل من المجموعة المخصصة.")

    reply_requests[s.id] = {"chat_id": orig_chat, "msg_id": orig_msg}
    await event.reply("✍️ اكتب الرد الذي تريد إرساله إلى هذه الرسالة في المجموعة:")

@client.on(events.NewMessage(func=lambda e: e.is_private and not e.forward and not e.raw_text.startswith('/')))
async def handle_reply_text(event):
    s = await event.get_sender()
    if s.id not in reply_requests: return
    req = reply_requests.pop(s.id)
    try:
        await client.send_message(req['chat_id'], event.raw_text, reply_to=req['msg_id'])
        await event.reply("✅ تم إرسال الرد.")
    except Exception as e:
        await event.reply(f"❌ فشل الإرسال: {str(e)}")

# ========== باقي الأوامر ==========
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    s = await event.get_sender()
    if s.username == DEVELOPER_USERNAME:
        btns = [
            [Button.inline("🔇 مدة الكتم", b"mute_dur"), Button.inline("📊 حالة", b"bot_stat")],
            [Button.inline("🆔 الآيدي", b"get_id"), Button.inline("🔓 فك الكل", b"unmute_all_btn")]
        ]
        await event.reply(f"⚡ **PIPO BOT** ⚡\n👑 @{DEVELOPER_USERNAME}", buttons=btns)
    else:
        await event.reply("ياحييي داصرتوني ثم ثم 😒💋")

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
        try: await unmute_user(GROUP_ID, u); del mute_status[u]; c += 1
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

@client.on(events.NewMessage(pattern='/زيادة_المدة'))
async def inc_mute(event):
    if not is_admin(await event.get_sender()): return
    d = last_muted_user.get(event.chat_id)
    if not d: return await event.reply("❌ لا يوجد آخر كتم.")
    btns = [[Button.inline("+10 د", f"add_{d['uid']}_10"), Button.inline("+30 د", f"add_{d['uid']}_30"), Button.inline("+1 س", f"add_{d['uid']}_60")]]
    await event.reply(f"⏰ زيادة كتم {d['name']}:", buttons=btns)

@client.on(events.NewMessage(pattern='/كتم', func=lambda e: e.is_reply))
async def permanent_mute(event):
    sender = await event.get_sender()
    if not is_admin(sender): return
    target = await (await event.get_reply_message()).get_sender()
    if not target: return await event.reply("❌ العضو غير موجود")
    ten_years = 10*365*24*3600
    await mute_user(event.chat_id, target.id, ten_years)
    mute_status[target.id] = {'until': time.time() + ten_years, 'name': target.first_name}
    last_muted_user[event.chat_id] = {'uid': target.id, 'name': target.first_name, 'username': target.username}
    await event.reply(f"🚫 هاك الكتمة يا {target.first_name} 😂")

@client.on(events.NewMessage(pattern=r'^/كتم_عن_بعد\s+(@?\w+)(?:\s+(.*))?', func=lambda e: e.is_private))
async def remote_mute(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    username = event.pattern_match.group(1).lstrip('@')
    custom_msg = event.pattern_match.group(2)
    if not custom_msg: return await event.reply("❌ اكتب رسالة بعد اليوزر")
    try: entity = await client.get_entity(f"@{username}")
    except: return await event.reply("❌ اليوزر غير موجود")
    ten_years = 10*365*24*3600
    if await mute_user(GROUP_ID, entity.id, ten_years):
        mute_status[entity.id] = {'until': time.time() + ten_years, 'name': entity.first_name}
        try: await client.send_message(entity.id, custom_msg); await event.reply(f"✅ تم كتم {entity.first_name}")
        except: await event.reply("✅ تم الكتم ولكن تعذر إرسال الرسالة")
    else: await event.reply("❌ فشل الكتم")

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
    await event.reply(f"✅ تم رفع {target_name or target_id} مسؤولاً")

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
    await event.reply("✅ تم تنزيله من المسؤولين")

@client.on(events.NewMessage(pattern='/تحذير'))
async def warn_user(event):
    if not is_admin(await event.get_sender()): return
    if not event.is_reply: return await event.reply("❌ يجب الرد على الشخص")
    target = await (await event.get_reply_message()).get_sender()
    if not target: return
    uid = target.id; name = target.first_name or "لا اسم"
    warnings_data[uid].append(time.time()); save_warnings()
    cur = len(warnings_data[uid])
    await event.reply(f"⚠️ {name} تحذير {cur}/{MAX_WARNINGS}")
    if cur >= MAX_WARNINGS:
        if await mute_user(event.chat_id, uid, mute_duration):
            mute_status[uid] = {'until': time.time() + mute_duration, 'name': name}
            await event.reply(f"🚫 {name} كتم {mute_duration//60} د")
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
    await event.reply(f"📊 {target_name or target_id} لديه {c}/{MAX_WARNINGS} تحذيرات")

@client.on(events.NewMessage(pattern=r'^/مسح\s+(\d+)$'))
async def purge(event):
    if not is_admin(await event.get_sender()): return
    count = min(int(event.pattern_match.group(1)), 100)
    if count <= 0: return
    msgs = await client.get_messages(event.chat_id, limit=count)
    ids = [m.id for m in msgs if m]
    await client.delete_messages(event.chat_id, ids)
    confirm = await event.reply(f"🧹 مسح {len(ids)} رسالة")
    await asyncio.sleep(2); await confirm.delete()

@client.on(events.NewMessage(pattern='/عرض_المكتومين'))
async def muted_list(event):
    if not mute_status: return await event.reply("✅ لا يوجد مكتومين")
    now = time.time(); txt = "📋 المكتومين:\n"
    for uid, d in mute_status.items():
        rem = int(d['until'] - now)
        if rem > 0:
            try: name = (await client.get_entity(uid)).first_name
            except: name = str(uid)
            txt += f"• {name} - ⏳ {rem//60} د\n"
    await event.reply(txt)

@client.on(events.NewMessage(pattern='/تثبيت'))
async def pin_msg(event):
    if not is_admin(await event.get_sender()): return
    if not event.is_reply: return await event.reply("❌ رد على رسالة")
    replied = await event.get_reply_message()
    try:
        await client.pin_message(event.chat_id, replied.id)
        await event.reply("📌 تم التثبيت")
    except Exception as e:
        await event.reply(f"❌ فشل: {e}")

@client.on(events.NewMessage(pattern='/تقرير', func=lambda e: e.is_reply))
async def report_msg(event):
    target_msg = await event.get_reply_message()
    reported_user = await target_msg.get_sender()
    reporter = await event.get_sender()
    if not reported_user or not reporter: return
    report_text = (
        f"📢 **تقرير جديد**\n"
        f"👤 المُبلّغ: {reporter.first_name} (@{reporter.username or 'بدون'})\n"
        f"🚫 المخالف: {reported_user.first_name} (ID: {reported_user.id})\n"
        f"💬 الرسالة: {target_msg.raw_text[:200]}"
    )
    for admin_id in GROUP_ADMINS:
        try: await client.send_message(admin_id, report_text)
        except: pass
    await event.reply("✅ تم إرسال التقرير للمسؤولين.")

@client.on(events.NewMessage(pattern='/قوانين'))
async def show_rules(event):
    if not os.path.exists(RULES_FILE):
        return await event.reply("❌ لم يقم المطور بتعيين القوانين بعد.")
    with open(RULES_FILE, 'r') as f:
        rules = f.read()
    await event.reply(f"📜 **قوانين المجموعة:**\n{rules}")

@client.on(events.NewMessage(pattern='/معلومات', func=lambda e: e.is_reply))
async def user_info(event):
    target = await (await event.get_reply_message()).get_sender()
    if not target: return await event.reply("❌ خطأ")
    uid = target.id
    warns = len(warnings_data.get(uid, []))
    is_muted = "✅ غير مكتوم"
    if uid in mute_status:
        rem = mute_status[uid]['until'] - time.time()
        if rem > 0: is_muted = f"🚫 مكتوم ({int(rem//60)} د متبقية)"
    rank = "👤 عضو"
    if target.username == DEVELOPER_USERNAME: rank = "👑 مطور"
    elif uid in GROUP_ADMINS: rank = "🛡️ مسؤول"
    info = (
        f"📋 **معلومات العضو**\n"
        f"👤 الاسم: {target.first_name}\n"
        f"🆔 الآيدي: {uid}\n"
        f"📎 اليوزر: @{target.username or 'لا يوجد'}\n"
        f"⚠️ التحذيرات: {warns}/{MAX_WARNINGS}\n"
        f"🔇 حالة الكتم: {is_muted}\n"
        f"⭐ الرتبة: {rank}"
    )
    await event.reply(info)

@client.on(events.NewMessage(pattern='/توب_المتفاعلين'))
async def top_members(event):
    if not message_count: return await event.reply("❌ لا توجد إحصائيات بعد.")
    items = sorted(message_count.items(), key=lambda x: x[1], reverse=True)[:5]
    txt = "🏆 **توب المتفاعلين:**\n"
    for i, (uid, cnt) in enumerate(items, 1):
        try: name = (await client.get_entity(uid)).first_name
        except: name = str(uid)
        txt += f"{i}. {name} - {cnt} رسالة\n"
    await event.reply(txt)

@client.on(events.NewMessage(pattern='/مساعدة'))
async def help_cmd(event):
    await event.reply("📜 اختر فئة الأوامر:", buttons=[
        [Button.inline("👤 الأعضاء", b"help_member")],
        [Button.inline("🛡️ المسؤول", b"help_admin")],
        [Button.inline("⚡ المطور", b"help_dev")],
    ])

@client.on(events.CallbackQuery)
async def on_callback(event):
    data = event.data.decode('utf-8')
    if data == "help_dev":
        txt = "⚡ أوامر المطور:\n/start /قفل /فك /كتم /كتم_عن_بعد /مدة_الكتم /فك_كل /حماية /رفع_مسؤول /تنزيل_مسؤول /تحذير /عرض_التحذيرات /مسح /عرض_المكتومين /تثبيت /مساعدة /معلومات /تقرير /توب_المتفاعلين"
    elif data == "help_admin":
        txt = "🛡️ أوامر المسؤول:\n/قفل /فك /كتم /مدة_الكتم /فك_كل /حماية /زيادة_المدة /تحذير /عرض_التحذيرات /مسح /عرض_المكتومين /تثبيت /مساعدة /معلومات /تقرير /توب_المتفاعلين"
    elif data == "help_member":
        txt = "👤 أوامر الأعضاء:\n/start /ايدي /قوانين /تقرير /توب_المتفاعلين /مساعدة"
    elif data.startswith("add_"):
        if (await event.get_sender()).username != DEVELOPER_USERNAME: return
        _, uid, mins = data.split("_"); uid = int(uid); mins = int(mins)
        await mute_user(GROUP_ID, uid, mins * 60)
        mute_status[uid] = {'until': time.time() + mins * 60}
        await event.edit(f"✅ +{mins} دقائق")
        return
    elif data == "mute_dur": await event.reply(f"⏰ {mute_duration//60} د"); return
    elif data == "bot_stat": await event.reply(f"📊 مكتوم: {len(mute_status)}"); return
    elif data == "get_id": await event.reply(f"🆔 {event.chat_id}"); return
    elif data == "unmute_all_btn":
        for u in list(mute_status.keys()):
            try: await unmute_user(GROUP_ID, u); del mute_status[u]
            except: pass
        await event.reply("🔓 فك الكل"); return
    else: return
    await event.edit(txt)

# ========== حماية المجموعة ==========
@client.on(events.NewMessage(chats=[GROUP_ID]))
async def handler(event):
    global link_protection, forward_protection, mute_duration
    if not event.raw_text or event.out: return
    s = await event.get_sender()
    if not s or s.id == client.uid: return
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
        await event.respond(f"🚫 {name} كتم {mute_duration//60} د")

async def main():
    await client.start(bot_token=BOT_TOKEN)
    me = await client.get_me()
    client.uid = me.id
    print(f"✅ PIPO BOT: @{me.username}")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
