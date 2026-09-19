# main.py
# Self-bot "Ignis" - text-based /help + all features + SOCKS5 proxy

import asyncio
import re
import os
import json
import random
import datetime
import pytz
from collections import Counter
from pyrogram import Client, filters
from pyrogram.types import Message

# ==================== CONFIG ====================
API_ID = 31334798
API_HASH = "a606bb53467af6a86c158714be3c3083"
SESSION_NAME = "my_selfbot"
SAVED_MESSAGES_ID = "@ThatEvill"
TIMEZONE = "Asia/Tehran"
BOT_NAME = "Ignis"


# ==================== GLOBAL STATE ====================
auto_save_enabled = True
original_last_name = None
original_first_name = None
clock_task = None
nameclock_task = None
autoreply_rules = {}
mirror_enabled = False
timer_tasks = []
tracked_users = {}
monitored_chats = {}
keyword_alerts = []

RANDOM_NAMES = ["Ghost", "Phantom", "Shadow", "Void", "Null", "Zero", "Nova", "Echo", "Cipher", "Anon"]
RANDOM_LOVE = ["تو بهترینی 💖", "دلم برات تنگ شده 🥺", "عاشقتم ❤️", "قلبم واسه تو می‌تپه 💓"]
RANDOM_ROAST = ["یه کم فکر کن 🧠", "بیشعور نباش 🐴", "برو گم شو 🚪", "استعداد داری، ولی نه این یکی 🎭"]

# ==================== CLIENT ====================
app = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH, proxy=PROXY)


# ==================== HELP DATA ====================
HELP_CATEGORIES = {
    "save": (
        "📥 Save",
        [
            ("/saven on|off", "روشن/خاموش کردن ذخیره‌ی خودکار مدیای تایم‌دار"),
            ("/savepost <link>", "ذخیره‌ی یه پست از لینک به سیو مسیج‌ها"),
        ],
    ),
    "clock": (
        "⏰ Clock",
        [
            ("/timen", "ساعت رو توی اسم خانوادگی ست می‌کنه"),
        ],
    ),
    "evil1": (
        "😈 Evil 1 – Basic",
        [
            ("/spam <n> <text>", "یه متن رو n بار می‌فرسته"),
            ("/typing <sec>", "به مدت n ثانیه نشون می‌ده داره تایپ می‌کنه"),
            ("/ghost <sec> <text>", "پیام می‌فرسته و بعد از n ثانیه پاکش می‌کنه"),
            ("/fakename <name>", "اسمت رو ۳۰ ثانیه عوض می‌کنه"),
            ("/react <emoji>", "به آخرین پیام ری‌اکشن می‌زنه"),
            ("/autoreply <trigger> <reply>", "جواب خودکار به پیام‌های حاوی trigger"),
            ("/stopautoreply", "پاک کردن همه‌ی جواب‌های خودکار"),
            ("/echo <text>", "متن رو دوباره می‌فرسته"),
            ("/flood <n> <text>", "مثل spam ولی سریع‌تر"),
            ("/vanish", "۵۰ پیام آخر خودت رو پاک می‌کنه"),
            ("/mirror", "هر پیامی که بفرستی رو دوباره کپی می‌کنه"),
        ],
    ),
    "evil2": (
        "😈 Evil 2 – Advanced",
        [
            ("/silent <text>", "پیام بدون نوتیفیکیشن"),
            ("/spoiler <text>", "متن توی اسپویلر"),
            ("/pinall <n>", "n پیام آخر رو پین می‌کنه (فقط ادمین)"),
            ("/unpinall", "همه‌ی پین‌ها رو برمی‌داره"),
            ("/fakereply <msg_id> <text>", "ریپلای به یه پیام قدیمی"),
            ("/chain <text>", "زنجیره‌ی ۵ پیام ریپلای‌دار"),
            ("/nameclock <sec>", "هر n ثانیه اسمت رو عوض می‌کنه"),
            ("/nick <name>", "اسمت رو عوض می‌کنه"),
            ("/forwardlast <n>", "n پیام آخر رو به سیو مسیج‌ها کپی می‌کنه"),
            ("/cleanchat <n>", "n پیام آخر خودت رو پاک می‌کنه"),
            ("/delall", "همه‌ی پیام‌های خودت توی این چت رو پاک می‌کنه"),
        ],
    ),
    "evil3": (
        "😈 Evil 3 – Social",
        [
            ("/readall", "همه‌ی چت‌های خونده‌نشده رو خونده می‌کنه"),
            ("/unread <n>", "n چت آخر رو خونده‌نشده می‌کنه"),
            ("/block <user>", "بلاک کردن کاربر"),
            ("/unblock <user>", "آنبلاک کردن کاربر"),
            ("/kiss <user>", "پیام عاشقانه"),
            ("/roast <user>", "توهین ملایم"),
        ],
    ),
    "games": (
        "🎲 Games",
        [
            ("/dice", "تاس 🎲"),
            ("/slot", "اسلات 🎰"),
            ("/dart", "دارت 🎯"),
            ("/basket", "بسکتبال 🏀"),
            ("/bowl", "بولینگ 🎳"),
            ("/football", "فوتبال ⚽"),
        ],
    ),
    "advanced": (
        "🧠 Advanced (Legal)",
        [
            ("/export <n>", "خروجی JSON از n پیام آخر چت"),
            ("/search <word>", "جست‌وجو توی تاریخچه‌ی چت"),
            ("/stats", "آمار چت (تعداد پیام هر نفر، ساعت فعال، کلمات)"),
            ("/wordcloud", "ابر کلمات چت"),
            ("/track <user>", "خبر دادن وقتی کاربر آنلاین شد"),
            ("/untrack <user>", "لغو ردیابی"),
            ("/tracks", "لیست ردیابی‌ها"),
            ("/backup <n>", "بکاپ چت به JSON"),
            ("/monitor <chat_id>", "لاگ کردن پیام‌های جدید یه چت"),
            ("/unmonitor <chat_id>", "لغو مانیتور"),
            ("/monitors", "لیست مانیتورها"),
            ("/keyword <word>", "هشدار وقتی کلمه توی هر چتی اومد"),
            ("/unkeyword <word>", "لغو کلمه"),
            ("/keywords", "لیست کلمات"),
            ("/timeline <user>", "تایم‌لاین فعالیت کاربر توی چت"),
            ("/extract", "استخراج لینک/عکس/فایل‌های چت"),
            ("/whois <user>", "اطلاعات عمومی کاربر"),
        ],
    ),
    "misc": (
        "🕵️ Misc",
        [
            ("/leak <text>", "متن با افکت لیک"),
            ("/timer <sec> <text>", "ارسال پیام بعد از n ثانیه"),
            ("/help", "لیست بخش‌ها"),
            ("/help <بخش>", "توضیحات یه بخش خاص"),
        ],
    ),
}


def build_help_main():
    out = (
        f"🤖 **{BOT_NAME} Help**\n\n"
        "برای دیدن دستورات هر بخش، بنویس:\n"
        "`/help <بخش>`\n\n"
        "**بخش‌ها:**\n"
    )
    for key, (title, _) in HELP_CATEGORIES.items():
        out += f"• `{key}` → {title}\n"
    out += "\n**مثال:** `/help evil1`"
    return out


def build_help_category(key: str):
    title, items = HELP_CATEGORIES[key]
    out = f"{title}\n\n"
    for cmd, desc in items:
        out += f"`{cmd}`\n  └ {desc}\n\n"
    out += f"\n🔙 برگرد به لیست: `/help`"
    return out


# ==================== /help ====================
@app.on_message(filters.command("help", prefixes="/") & filters.me)
async def cmd_help(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit(build_help_main())
        return
    key = message.command[1].lower()
    if key in HELP_CATEGORIES:
        await message.edit(build_help_category(key))
    else:
        await message.edit(
            f"❌ بخش `{key}` پیدا نشد.\n\n" + build_help_main()
        )


# ==================== FEATURE 1: AUTO-SAVE ====================
# ==================== FEATURE 1: AUTO-SAVE ====================
@app.on_message(filters.photo | filters.video, group=1)
async def save_self_destructing_media(client: Client, message: Message):
    global auto_save_enabled
    if not auto_save_enabled:
        return

    ttl = None
    media_type = None

    if message.photo and message.photo.ttl_seconds:
        ttl = message.photo.ttl_seconds
        media_type = "photo"
    elif message.video and message.video.ttl_seconds:
        ttl = message.video.ttl_seconds
        media_type = "video"

    if not ttl:
        return

    print(f"📥 [DEBUG] Timed {media_type} detected! TTL={ttl}s from "
          f"{message.from_user.first_name if message.from_user else '?'}")

    try:
        fp = await message.download()
        cap = (
            f"📥 **Timed {media_type.title()}** (TTL: {ttl}s)\n"
            f"👤 {message.from_user.first_name if message.from_user else '?'}\n"
            f"🆔 `{message.from_user.id if message.from_user else 'N/A'}`\n"
            f"🕐 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        if media_type == "photo":
            await client.send_photo(SAVED_MESSAGES_ID, fp, caption=cap)
        else:
            await client.send_video(SAVED_MESSAGES_ID, fp, caption=cap)
        if os.path.exists(fp):
            os.remove(fp)
        print(f"✅ Timed {media_type} saved ({ttl}s)")
    except Exception as e:
        print(f"❌ Error saving timed media: {e}")
    
    # بعد از ذخیره، اجازه بده هندلرهای دیگه هم پیام رو ببینن
    message.continue_propagation()

@app.on_message(filters.command("saven", prefixes="/") & filters.me)
async def toggle_auto_save(client: Client, message: Message):
    global auto_save_enabled
    if len(message.command) > 1:
        a = message.command[1].lower()
        if a in ["on", "1", "true"]:
            auto_save_enabled = True
        elif a in ["off", "0", "false"]:
            auto_save_enabled = False
        else:
            # اگه آرگومان اشتباه بود، فقط توی ترمینال چاپ کن
            print(f"❌ [SAVEN] Invalid arg: {a}")
            try:
                await message.delete()
            except:
                pass
            return
    else:
        auto_save_enabled = not auto_save_enabled

    # چاپ توی ترمینال، نه توی چت
    status = "ON" if auto_save_enabled else "OFF"
    print(f"✅ [SAVEN] Auto-Save is now {status}")

    # پاک کردن پیام کامند از چت
    try:
        await message.delete()
    except Exception as e:
        print(f"⚠️ [SAVEN] Could not delete command message: {e}")


# ==================== FEATURE 2: SAVEPOST ====================
def parse_telegram_link(link: str):
    link = link.strip()
    link = re.sub(r"^https?://", "", link).rstrip("/")
    thread_id = None
    tm = re.search(r"[?&]thread=(\d+)", link)
    if tm:
        thread_id = int(tm.group(1))
        link = link.split("?")[0].split("&")[0]
    m = re.match(r"t\.me/c/(\d+)/(\d+)", link)
    if m:
        return int(f"-100{m.group(1)}"), int(m.group(2)), thread_id
    m = re.match(r"t\.me/([A-Za-z0-9_]+)/(\d+)", link)
    if m:
        return m.group(1), int(m.group(2)), thread_id
    return None, None, None


@app.on_message(filters.command("savepost", prefixes="/") & filters.me)
async def save_post(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/savepost <link>`")
        return
    cid, mid, _ = parse_telegram_link(message.command[1])
    if cid is None:
        await message.edit("❌ Invalid link.")
        return
    try:
        t = await client.get_messages(cid, mid)
        if not t or t.empty:
            await message.edit("❌ Not found.")
            return
        await t.copy(SAVED_MESSAGES_ID)
        await message.edit(f"✅ Saved `{cid}` / `{mid}`")
    except Exception as e:
        await message.edit(f"❌ `{e}`")


# ==================== FEATURE 3: /timen ====================
@app.on_message(filters.command("timen", prefixes="/") & filters.me)
async def toggle_clock_name(client: Client, message: Message):
    global clock_task, original_last_name
    if clock_task and not clock_task.done():
        clock_task.cancel()
        clock_task = None
        if original_last_name is not None:
            await client.update_profile(last_name=original_last_name)
            await message.edit(f"🛑 Restored: `{original_last_name}`")
        else:
            await message.edit("🛑 Stopped.")
    else:
        me = await client.get_me()
        original_last_name = me.last_name or ""
        clock_task = asyncio.create_task(update_clock_name(client))
        await message.edit("⏰ Clock started.")


async def update_clock_name(client: Client):
    global original_last_name
    while True:
        try:
            now = datetime.datetime.now(pytz.timezone(TIMEZONE))
            t = now.strftime("%H:%M")
            new = f"{original_last_name} | {t}" if original_last_name else f"🕐 {t}"
            await client.update_profile(last_name=new)
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"❌ {e}")
            await asyncio.sleep(60)


# ==================== 😈 EVIL (batch 1) ====================
@app.on_message(filters.command("spam", prefixes="/") & filters.me)
async def cmd_spam(client: Client, message: Message):
    if len(message.command) < 3:
        await message.edit("❌ `/spam <count> <text>`")
        return
    try:
        n = min(int(message.command[1]), 50)
    except ValueError:
        await message.edit("❌ number.")
        return
    text = " ".join(message.command[2:])
    cid = message.chat.id
    await message.delete()
    for i in range(n):
        try:
            await client.send_message(cid, f"{text} [{i+1}/{n}]")
            await asyncio.sleep(1.2)
        except Exception as e:
            print(f"❌ {e}")
            break


@app.on_message(filters.command("typing", prefixes="/") & filters.me)
async def cmd_typing(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/typing <sec>`")
        return
    try:
        s = min(int(message.command[1]), 120)
    except ValueError:
        await message.edit("❌ number.")
        return
    cid = message.chat.id
    await message.delete()
    try:
        async with client.action(cid, "typing"):
            await asyncio.sleep(s)
    except Exception as e:
        print(f"❌ {e}")


@app.on_message(filters.command("ghost", prefixes="/") & filters.me)
async def cmd_ghost(client: Client, message: Message):
    if len(message.command) < 3:
        await message.edit("❌ `/ghost <sec> <text>`")
        return
    try:
        s = int(message.command[1])
    except ValueError:
        await message.edit("❌ number.")
        return
    text = " ".join(message.command[2:])
    cid = message.chat.id
    await message.delete()
    sent = await client.send_message(cid, text)
    await asyncio.sleep(s)
    try:
        await sent.delete()
    except:
        pass


@app.on_message(filters.command("fakename", prefixes="/") & filters.me)
async def cmd_fakename(client: Client, message: Message):
    global original_first_name
    if len(message.command) < 2:
        await message.edit("❌ `/fakename <name>`")
        return
    name = " ".join(message.command[1:])[:64]
    me = await client.get_me()
    if original_first_name is None:
        original_first_name = me.first_name
    await client.update_profile(first_name=name)
    await message.edit(f"🎭 `{name}` for 30s...")
    await asyncio.sleep(30)
    await client.update_profile(first_name=original_first_name)
    original_first_name = None


@app.on_message(filters.command("react", prefixes="/") & filters.me)
async def cmd_react(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/react <emoji>`")
        return
    emoji = message.command[1]
    cid = message.chat.id
    await message.delete()
    try:
        async for m in client.get_chat_history(cid, limit=10):
            if m.id != message.id and not (m.text and m.text.startswith("/")):
                await client.send_reaction(cid, m.id, emoji)
                return
    except Exception as e:
        print(f"❌ {e}")


@app.on_message(filters.command("autoreply", prefixes="/") & filters.me)
async def cmd_autoreply(client: Client, message: Message):
    if len(message.command) < 3:
        await message.edit("❌ `/autoreply <trigger> <reply>`")
        return
    trigger = message.command[1].lower()
    reply = " ".join(message.command[2:])
    autoreply_rules[trigger] = reply
    await message.edit(f"✅ `{trigger}` → `{reply}`")


@app.on_message(filters.command("stopautoreply", prefixes="/") & filters.me)
async def cmd_stop_autoreply(client: Client, message: Message):
    autoreply_rules.clear()
    await message.edit("🛑 Cleared.")


@app.on_message(filters.private & ~filters.me)
async def autoreply_listener(client: Client, message: Message):
    if not message.text:
        return
    low = message.text.lower()
    for t, r in autoreply_rules.items():
        if t in low:
            try:
                await message.reply(r)
            except Exception as e:
                print(f"❌ {e}")
            break


@app.on_message(filters.command("echo", prefixes="/") & filters.me)
async def cmd_echo(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/echo <text>`")
        return
    text = " ".join(message.command[1:])
    cid = message.chat.id
    await message.delete()
    await client.send_message(cid, text)


@app.on_message(filters.command("flood", prefixes="/") & filters.me)
async def cmd_flood(client: Client, message: Message):
    if len(message.command) < 3:
        await message.edit("❌ `/flood <count> <text>`")
        return
    try:
        n = min(int(message.command[1]), 30)
    except ValueError:
        await message.edit("❌ number.")
        return
    text = " ".join(message.command[2:])
    cid = message.chat.id
    await message.delete()
    for i in range(n):
        try:
            await client.send_message(cid, text)
            await asyncio.sleep(0.6)
        except Exception as e:
            print(f"❌ {e}")
            break


@app.on_message(filters.command("vanish", prefixes="/") & filters.me)
async def cmd_vanish(client: Client, message: Message):
    cid = message.chat.id
    await message.delete()
    count = 0
    try:
        async for m in client.get_chat_history(cid, limit=200):
            if m.from_user and m.from_user.is_self:
                try:
                    await m.delete()
                    count += 1
                    if count >= 50:
                        break
                    await asyncio.sleep(0.4)
                except:
                    pass
    except Exception as e:
        print(f"❌ {e}")


@app.on_message(filters.command("mirror", prefixes="/") & filters.me)
async def cmd_mirror(client: Client, message: Message):
    global mirror_enabled
    mirror_enabled = not mirror_enabled
    await message.edit(f"🪞 Mirror: {'✅ ON' if mirror_enabled else '❌ OFF'}")


@app.on_message(filters.me & ~filters.command([], prefixes="/"))
async def mirror_listener(client: Client, message: Message):
    if not mirror_enabled:
        return
    if message.text and message.text.startswith("/"):
        return
    try:
        await client.send_message(message.chat.id, message.text or "[media]")
    except Exception as e:
        print(f"❌ {e}")


# ==================== 😈 EVIL (batch 2) ====================
@app.on_message(filters.command("silent", prefixes="/") & filters.me)
async def cmd_silent(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/silent <text>`")
        return
    text = " ".join(message.command[1:])
    cid = message.chat.id
    await message.delete()
    await client.send_message(cid, text, disable_notification=True)


@app.on_message(filters.command("spoiler", prefixes="/") & filters.me)
async def cmd_spoiler(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/spoiler <text>`")
        return
    text = " ".join(message.command[1:])
    cid = message.chat.id
    await message.delete()
    await client.send_message(cid, f"<spoiler>{text}</spoiler>")


@app.on_message(filters.command("pinall", prefixes="/") & filters.me)
async def cmd_pinall(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/pinall <n>`")
        return
    try:
        n = min(int(message.command[1]), 10)
    except ValueError:
        await message.edit("❌ number.")
        return
    cid = message.chat.id
    await message.delete()
    count = 0
    try:
        async for m in client.get_chat_history(cid, limit=n + 5):
            if m.id == message.id:
                continue
            try:
                await client.pin_chat_message(cid, m.id, disable_notification=True)
                count += 1
                if count >= n:
                    break
                await asyncio.sleep(1)
            except:
                pass
    except Exception as e:
        print(f"❌ {e}")


@app.on_message(filters.command("unpinall", prefixes="/") & filters.me)
async def cmd_unpinall(client: Client, message: Message):
    cid = message.chat.id
    await message.delete()
    try:
        await client.unpin_all_chat_messages(cid)
    except Exception as e:
        print(f"❌ {e}")


@app.on_message(filters.command("fakereply", prefixes="/") & filters.me)
async def cmd_fakereply(client: Client, message: Message):
    if len(message.command) < 3:
        await message.edit("❌ `/fakereply <msg_id> <text>`")
        return
    try:
        mid = int(message.command[1])
    except ValueError:
        await message.edit("❌ msg_id number.")
        return
    text = " ".join(message.command[2:])
    cid = message.chat.id
    await message.delete()
    try:
        await client.send_message(cid, text, reply_to_message_id=mid)
    except Exception as e:
        print(f"❌ {e}")


@app.on_message(filters.command("chain", prefixes="/") & filters.me)
async def cmd_chain(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/chain <text>`")
        return
    text = " ".join(message.command[1:])
    cid = message.chat.id
    await message.delete()
    prev = None
    for i in range(5):
        try:
            if prev is None:
                prev = await client.send_message(cid, f"{text} [{i+1}]")
            else:
                prev = await client.send_message(cid, f"{text} [{i+1}]", reply_to_message_id=prev.id)
            await asyncio.sleep(1)
        except Exception as e:
            print(f"❌ {e}")
            break


@app.on_message(filters.command("nameclock", prefixes="/") & filters.me)
async def cmd_nameclock(client: Client, message: Message):
    global nameclock_task
    if nameclock_task and not nameclock_task.done():
        nameclock_task.cancel()
        nameclock_task = None
        await message.edit("🛑 Name-clock stopped.")
        return
    if len(message.command) < 2:
        await message.edit("❌ `/nameclock <sec>`")
        return
    try:
        s = max(int(message.command[1]), 10)
    except ValueError:
        await message.edit("❌ number.")
        return
    nameclock_task = asyncio.create_task(nameclock_worker(client, s))
    await message.edit(f"🎭 Name-clock every {s}s. Send again to stop.")


async def nameclock_worker(client: Client, interval: int):
    me = await client.get_me()
    orig = me.first_name
    while True:
        try:
            new = random.choice(RANDOM_NAMES)
            await client.update_profile(first_name=new)
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            await client.update_profile(first_name=orig)
            break
        except Exception as e:
            print(f"❌ {e}")
            await asyncio.sleep(interval)


@app.on_message(filters.command("nick", prefixes="/") & filters.me)
async def cmd_nick(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/nick <name>`")
        return
    name = " ".join(message.command[1:])[:64]
    await client.update_profile(first_name=name)
    await message.edit(f"✅ Name set: `{name}`")


@app.on_message(filters.command("forwardlast", prefixes="/") & filters.me)
async def cmd_forwardlast(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/forwardlast <n>`")
        return
    try:
        n = min(int(message.command[1]), 20)
    except ValueError:
        await message.edit("❌ number.")
        return
    cid = message.chat.id
    await message.delete()
    count = 0
    try:
        async for m in client.get_chat_history(cid, limit=n + 5):
            if m.id == message.id:
                continue
            try:
                await m.copy(SAVED_MESSAGES_ID)
                count += 1
                if count >= n:
                    break
                await asyncio.sleep(0.8)
            except:
                pass
    except Exception as e:
        print(f"❌ {e}")


@app.on_message(filters.command("cleanchat", prefixes="/") & filters.me)
async def cmd_cleanchat(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/cleanchat <n>`")
        return
    try:
        n = min(int(message.command[1]), 100)
    except ValueError:
        await message.edit("❌ number.")
        return
    cid = message.chat.id
    await message.delete()
    count = 0
    try:
        async for m in client.get_chat_history(cid, limit=n + 10):
            if m.from_user and m.from_user.is_self:
                try:
                    await m.delete()
                    count += 1
                    if count >= n:
                        break
                    await asyncio.sleep(0.4)
                except:
                    pass
    except Exception as e:
        print(f"❌ {e}")


@app.on_message(filters.command("delall", prefixes="/") & filters.me)
async def cmd_delall(client: Client, message: Message):
    cid = message.chat.id
    await message.delete()
    count = 0
    try:
        async for m in client.get_chat_history(cid):
            if m.from_user and m.from_user.is_self:
                try:
                    await m.delete()
                    count += 1
                    await asyncio.sleep(0.3)
                except:
                    pass
    except Exception as e:
        print(f"❌ {e}")
    print(f"🗑️ Deleted {count} messages")


# ==================== 😈 EVIL (batch 3 - social) ====================
@app.on_message(filters.command("readall", prefixes="/") & filters.me)
async def cmd_readall(client: Client, message: Message):
    await message.delete()
    count = 0
    async for dialog in client.get_dialogs():
        try:
            if dialog.unread_messages_count > 0:
                await client.read_chat_history(dialog.chat.id)
                count += 1
                await asyncio.sleep(0.3)
        except:
            pass
    print(f"📖 Read {count} chats")


@app.on_message(filters.command("unread", prefixes="/") & filters.me)
async def cmd_unread(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/unread <n>`")
        return
    try:
        n = min(int(message.command[1]), 20)
    except ValueError:
        await message.edit("❌ number.")
        return
    await message.delete()
    count = 0
    async for dialog in client.get_dialogs():
        if count >= n:
            break
        try:
            await client.mark_chat_unread(dialog.chat.id)
            count += 1
            await asyncio.sleep(0.3)
        except:
            pass


@app.on_message(filters.command("block", prefixes="/") & filters.me)
async def cmd_block(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/block <user>`")
        return
    try:
        await client.block_user(message.command[1])
        await message.edit(f"🚫 Blocked `{message.command[1]}`")
    except Exception as e:
        await message.edit(f"❌ `{e}`")


@app.on_message(filters.command("unblock", prefixes="/") & filters.me)
async def cmd_unblock(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/unblock <user>`")
        return
    try:
        await client.unblock_user(message.command[1])
        await message.edit(f"✅ Unblocked `{message.command[1]}`")
    except Exception as e:
        await message.edit(f"❌ `{e}`")


@app.on_message(filters.command("kiss", prefixes="/") & filters.me)
async def cmd_kiss(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/kiss <user>`")
        return
    target = message.command[1]
    text = random.choice(RANDOM_LOVE)
    await message.delete()
    try:
        await client.send_message(target, text)
    except Exception as e:
        print(f"❌ {e}")


@app.on_message(filters.command("roast", prefixes="/") & filters.me)
async def cmd_roast(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/roast <user>`")
        return
    target = message.command[1]
    text = random.choice(RANDOM_ROAST)
    await message.delete()
    try:
        await client.send_message(target, text)
    except Exception as e:
        print(f"❌ {e}")


# ==================== 🎲 GAMES ====================
@app.on_message(filters.command("dice", prefixes="/") & filters.me)
async def cmd_dice(client: Client, message: Message):
    cid = message.chat.id
    await message.delete()
    await client.send_dice(cid, emoji="🎲")


@app.on_message(filters.command("slot", prefixes="/") & filters.me)
async def cmd_slot(client: Client, message: Message):
    cid = message.chat.id
    await message.delete()
    await client.send_dice(cid, emoji="🎰")


@app.on_message(filters.command("dart", prefixes="/") & filters.me)
async def cmd_dart(client: Client, message: Message):
    cid = message.chat.id
    await message.delete()
    await client.send_dice(cid, emoji="🎯")


@app.on_message(filters.command("basket", prefixes="/") & filters.me)
async def cmd_basket(client: Client, message: Message):
    cid = message.chat.id
    await message.delete()
    await client.send_dice(cid, emoji="🏀")


@app.on_message(filters.command("bowl", prefixes="/") & filters.me)
async def cmd_bowl(client: Client, message: Message):
    cid = message.chat.id
    await message.delete()
    await client.send_dice(cid, emoji="🎳")


@app.on_message(filters.command("football", prefixes="/") & filters.me)
async def cmd_football(client: Client, message: Message):
    cid = message.chat.id
    await message.delete()
    await client.send_dice(cid, emoji="⚽")


# ==================== 🕵️ MISC ====================
@app.on_message(filters.command("leak", prefixes="/") & filters.me)
async def cmd_leak(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/leak <text>`")
        return
    text = " ".join(message.command[1:])
    cid = message.chat.id
    await message.delete()
    await client.send_message(cid, f"🤫 leaked: <spoiler>{text}</spoiler>")


@app.on_message(filters.command("timer", prefixes="/") & filters.me)
async def cmd_timer(client: Client, message: Message):
    if len(message.command) < 3:
        await message.edit("❌ `/timer <sec> <text>`")
        return
    try:
        s = int(message.command[1])
    except ValueError:
        await message.edit("❌ number.")
        return
    text = " ".join(message.command[2:])
    cid = message.chat.id
    await message.delete()

    async def _send_later():
        await asyncio.sleep(s)
        try:
            await client.send_message(cid, text)
        except Exception as e:
            print(f"❌ {e}")

    t = asyncio.create_task(_send_later())
    timer_tasks.append(t)


# ==================== 🧠 ADVANCED ====================
@app.on_message(filters.command("export", prefixes="/") & filters.me)
async def cmd_export(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/export <n>`")
        return
    try:
        n = min(int(message.command[1]), 500)
    except ValueError:
        await message.edit("❌ number.")
        return
    cid = message.chat.id
    await message.delete()
    data = []
    try:
        async for m in client.get_chat_history(cid, limit=n):
            if m.id == message.id:
                continue
            data.append({
                "id": m.id,
                "date": str(m.date),
                "from": m.from_user.id if m.from_user else None,
                "from_name": m.from_user.first_name if m.from_user else None,
                "text": m.text or m.caption or "",
                "media": m.media.value if m.media else None,
            })
        fp = f"export_{cid}_{int(datetime.datetime.now().timestamp())}.json"
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        await client.send_document(SAVED_MESSAGES_ID, fp, caption=f"📤 Export of {len(data)} messages")
        os.remove(fp)
    except Exception as e:
        print(f"❌ {e}")


@app.on_message(filters.command("search", prefixes="/") & filters.me)
async def cmd_search(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/search <word>`")
        return
    word = " ".join(message.command[1:]).lower()
    cid = message.chat.id
    await message.delete()
    results = []
    try:
        async for m in client.get_chat_history(cid, limit=2000):
            txt = (m.text or m.caption or "").lower()
            if word in txt:
                results.append(m)
                if len(results) >= 10:
                    break
        if not results:
            await client.send_message(cid, f"🔍 No results for `{word}`")
            return
        out = f"🔍 **Results for `{word}`** ({len(results)}):\n\n"
        for m in results:
            snippet = (m.text or m.caption or "")[:80]
            out += f"• [msg {m.id}] {snippet}\n"
        await client.send_message(SAVED_MESSAGES_ID, out)
    except Exception as e:
        print(f"❌ {e}")


@app.on_message(filters.command("stats", prefixes="/") & filters.me)
async def cmd_stats(client: Client, message: Message):
    cid = message.chat.id
    await message.delete()
    users = Counter()
    hours = Counter()
    words = Counter()
    total = 0
    try:
        async for m in client.get_chat_history(cid, limit=1000):
            total += 1
            if m.from_user:
                users[m.from_user.first_name or str(m.from_user.id)] += 1
            if m.date:
                hours[m.date.hour] += 1
            txt = (m.text or m.caption or "").lower()
            for w in re.findall(r"\w{3,}", txt):
                words[w] += 1
        out = f"📊 **Chat Stats** (last {total} msgs)\n\n"
        out += "**Top users:**\n"
        for u, c in users.most_common(5):
            out += f"• {u}: {c}\n"
        out += "\n**Busiest hours:**\n"
        for h, c in hours.most_common(5):
            out += f"• {h:02d}:00 → {c}\n"
        out += "\n**Top words:**\n"
        for w, c in words.most_common(10):
            out += f"• {w}: {c}\n"
        await client.send_message(SAVED_MESSAGES_ID, out)
    except Exception as e:
        print(f"❌ {e}")


@app.on_message(filters.command("wordcloud", prefixes="/") & filters.me)
async def cmd_wordcloud(client: Client, message: Message):
    cid = message.chat.id
    await message.delete()
    words = Counter()
    try:
        async for m in client.get_chat_history(cid, limit=1000):
            txt = (m.text or m.caption or "").lower()
            for w in re.findall(r"\w{3,}", txt):
                words[w] += 1
        top = words.most_common(30)
        out = "☁️ **Word Cloud** (top 30)\n\n"
        for w, c in top:
            out += f"{w} ({c})  "
        await client.send_message(SAVED_MESSAGES_ID, out)
    except Exception as e:
        print(f"❌ {e}")


@app.on_message(filters.command("track", prefixes="/") & filters.me)
async def cmd_track(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/track <user>`")
        return
    try:
        u = await client.get_users(message.command[1])
        tracked_users[u.id] = {"name": u.first_name, "last_seen_online": False}
        await message.edit(f"👁️ Tracking `{u.first_name}` (`{u.id}`)")
    except Exception as e:
        await message.edit(f"❌ `{e}`")


@app.on_message(filters.command("untrack", prefixes="/") & filters.me)
async def cmd_untrack(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/untrack <user>`")
        return
    try:
        u = await client.get_users(message.command[1])
        tracked_users.pop(u.id, None)
        await message.edit(f"🛑 Untracked `{u.first_name}`")
    except Exception as e:
        await message.edit(f"❌ `{e}`")


@app.on_message(filters.command("tracks", prefixes="/") & filters.me)
async def cmd_tracks(client: Client, message: Message):
    if not tracked_users:
        await message.edit("📭 No tracked users.")
        return
    out = "👁️ **Tracked Users**\n\n"
    for uid, info in tracked_users.items():
        out += f"• {info['name']} (`{uid}`)\n"
    await message.edit(out)


@app.on_message(filters.command("backup", prefixes="/") & filters.me)
async def cmd_backup(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/backup <n>`")
        return
    try:
        n = min(int(message.command[1]), 1000)
    except ValueError:
        await message.edit("❌ number.")
        return
    cid = message.chat.id
    await message.delete()
    data = []
    try:
        async for m in client.get_chat_history(cid, limit=n):
            data.append({
                "id": m.id,
                "date": str(m.date),
                "from_id": m.from_user.id if m.from_user else None,
                "text": m.text or m.caption or "",
            })
        fp = f"backup_{cid}_{int(datetime.datetime.now().timestamp())}.json"
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        await client.send_document(SAVED_MESSAGES_ID, fp, caption=f"💾 Backup of {len(data)} messages")
        os.remove(fp)
    except Exception as e:
        print(f"❌ {e}")


@app.on_message(filters.command("monitor", prefixes="/") & filters.me)
async def cmd_monitor(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/monitor <chat_id>`")
        return
    try:
        cid = int(message.command[1])
    except ValueError:
        await message.edit("❌ chat_id must be number.")
        return
    monitored_chats[cid] = True
    await message.edit(f"👀 Monitoring `{cid}`")


@app.on_message(filters.command("unmonitor", prefixes="/") & filters.me)
async def cmd_unmonitor(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/unmonitor <chat_id>`")
        return
    try:
        cid = int(message.command[1])
    except ValueError:
        await message.edit("❌ number.")
        return
    monitored_chats.pop(cid, None)
    await message.edit(f"🛑 Unmonitored `{cid}`")


@app.on_message(filters.command("monitors", prefixes="/") & filters.me)
async def cmd_monitors(client: Client, message: Message):
    if not monitored_chats:
        await message.edit("📭 No monitors.")
        return
    out = "👀 **Monitors**\n\n" + "\n".join(f"• `{c}`" for c in monitored_chats)
    await message.edit(out)


@app.on_message(filters.command("keyword", prefixes="/") & filters.me)
async def cmd_keyword(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/keyword <word>`")
        return
    word = message.command[1].lower()
    if word not in keyword_alerts:
        keyword_alerts.append(word)
    await message.edit(f"🔔 Keyword added: `{word}`")


@app.on_message(filters.command("unkeyword", prefixes="/") & filters.me)
async def cmd_unkeyword(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/unkeyword <word>`")
        return
    word = message.command[1].lower()
    if word in keyword_alerts:
        keyword_alerts.remove(word)
    await message.edit(f"🛑 Keyword removed: `{word}`")


@app.on_message(filters.command("keywords", prefixes="/") & filters.me)
async def cmd_keywords(client: Client, message: Message):
    if not keyword_alerts:
        await message.edit("📭 No keywords.")
        return
    await message.edit("🔔 **Keywords:**\n\n" + "\n".join(f"• `{w}`" for w in keyword_alerts))


# Generic listener for monitors + keywords
@app.on_message(filters.all & ~filters.me)
async def global_listener(client: Client, message: Message):
    if message.chat and message.chat.id in monitored_chats:
        try:
            txt = message.text or message.caption or "[media]"
            await client.send_message(
                SAVED_MESSAGES_ID,
                f"👀 **Monitor** `{message.chat.id}`\n"
                f"👤 {message.from_user.first_name if message.from_user else '?'}\n"
                f"💬 {txt[:500]}"
            )
        except:
            pass
    txt = (message.text or message.caption or "").lower()
    if txt:
        for w in keyword_alerts:
            if w in txt:
                try:
                    await client.send_message(
                        SAVED_MESSAGES_ID,
                        f"🔔 **Keyword** `{w}`\n"
                        f"📍 Chat: `{message.chat.id if message.chat else '?'}`\n"
                        f"👤 {message.from_user.first_name if message.from_user else '?'}\n"
                        f"💬 {txt[:500]}"
                    )
                except:
                    pass
                break


@app.on_message(filters.command("timeline", prefixes="/") & filters.me)
async def cmd_timeline(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/timeline <user>`")
        return
    try:
        u = await client.get_users(message.command[1])
    except Exception as e:
        await message.edit(f"❌ `{e}`")
        return
    cid = message.chat.id
    await message.delete()
    entries = []
    try:
        async for m in client.get_chat_history(cid, limit=2000):
            if m.from_user and m.from_user.id == u.id:
                entries.append(m)
                if len(entries) >= 30:
                    break
        if not entries:
            await client.send_message(cid, f"📭 No activity for `{u.first_name}`")
            return
        out = f"📅 **Timeline of {u.first_name}** (last {len(entries)})\n\n"
        for m in entries:
            txt = (m.text or m.caption or "[media]")[:60]
            out += f"• {m.date.strftime('%Y-%m-%d %H:%M')} → {txt}\n"
        await client.send_message(SAVED_MESSAGES_ID, out)
    except Exception as e:
        print(f"❌ {e}")


@app.on_message(filters.command("extract", prefixes="/") & filters.me)
async def cmd_extract(client: Client, message: Message):
    cid = message.chat.id
    await message.delete()
    links = []
    photos = 0
    files = 0
    try:
        async for m in client.get_chat_history(cid, limit=1000):
            txt = m.text or m.caption or ""
            for url in re.findall(r"https?://\S+", txt):
                links.append(url)
            if m.photo:
                photos += 1
            elif m.document:
                files += 1
        out = (
            f"📦 **Extract from chat**\n\n"
            f"🔗 Links: {len(links)}\n"
            f"🖼️ Photos: {photos}\n"
            f"📎 Files: {files}\n\n"
        )
        if links:
            out += "**Last 20 links:**\n"
            for l in links[:20]:
                out += f"• {l}\n"
        await client.send_message(SAVED_MESSAGES_ID, out)
    except Exception as e:
        print(f"❌ {e}")


@app.on_message(filters.command("whois", prefixes="/") & filters.me)
async def cmd_whois(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("❌ `/whois <user>`")
        return
    try:
        u = await client.get_users(message.command[1])
    except Exception as e:
        await message.edit(f"❌ `{e}`")
        return
    bio = ""
    last = None
    try:
        full = await client.get_chat(u.id)
        bio = full.bio or ""
        last = full.last_online_date
    except:
        pass
    out = (
        f"👤 **Whois: {u.first_name}**\n\n"
        f"🆔 ID: `{u.id}`\n"
        f"📛 Username: @{u.username or 'None'}\n"
        f"🤖 Bot: {'Yes' if u.is_bot else 'No'}\n"
        f"✅ Verified: {'Yes' if u.is_verified else 'No'}\n"
        f"💎 Premium: {'Yes' if getattr(u, 'is_premium', False) else 'No'}\n"
        f"📝 Bio: {bio[:200] if bio else '-'}\n"
        f"🕐 Last seen: {last if last else 'Hidden'}\n"
    )
    await message.edit(out)


# ==================== MAIN ====================
if __name__ == "__main__":
    print(f"🚀 {BOT_NAME} self-bot starting...")
    print(f"🔌 Proxy: {PROXY['scheme']}://{PROXY['hostname']}:{PROXY['port']}")
    app.run()