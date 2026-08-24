from colorama import Fore

from pyrogram import Client, filters, idle, errors

from pyrogram.types import *

from functools import wraps

from apscheduler.schedulers.asyncio import AsyncIOScheduler

import asyncio

import subprocess

import html

import zipfile

import pymysql

import shutil

import signal

import re

import os

#==================== Config =====================#

Admin = 0  # آیدی عددی مالک سلف ساز

Token = ""  # توکن ربات سلف ساز

API_ID = 0  # ایپی ایدی اکانت مالک سلف ساز

API_HASH = ""  # ایپی هش اکانت مالک سلف ساز

Channel_ID = "" # چنل سلف ساز بدون @

Helper_ID = "" # ایدی ربات هلپر بدون @

DBName = "" # نام دیتابیس اول

DBUser = "" # یوزر دیتابیس اول

DBPass = "" # پسورد دیتابیس اول

HelperDBName = "" # نام دیتابیس هلپر

HelperDBUser = "" # یوزر دیتابیس هلپر

HelperDBPass = "" # پسورد دیتابیس هلپر

CardNumber = "" # شماره کارت برای فروش

CardName = "" # نام صاحب شماره کارت 

#==================== Create =====================#

if not os.path.isdir("sessions"):

    os.mkdir("sessions")

if not os.path.isdir("selfs"):

    os.mkdir("selfs")

#===================== App =======================#

app = Client("Bot", api_id=API_ID, api_hash=API_HASH, bot_token=Token)



scheduler = AsyncIOScheduler()

scheduler.start()



temp_Client = {}

lock = asyncio.Lock()



def get_data(query):

    with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass, cursorclass=pymysql.cursors.DictCursor) as connect:

        db = connect.cursor()

        db.execute(query)

        result = db.fetchone()

        return result



def get_datas(query):

    with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass) as connect:

        db = connect.cursor()

        db.execute(query)

        result = db.fetchall()

        return result



def update_data(query):

    with pymysql.connect(host="localhost", database=DBName, user=DBUser, password=DBPass) as connect:

        db = connect.cursor()

        db.execute(query)

        connect.commit()



def helper_getdata(query):

    with pymysql.connect(host="localhost", database=HelperDBName, user=HelperDBUser, password=HelperDBPass) as connect:

        db = connect.cursor()

        db.execute(query)

        result = db.fetchone()

        return result



def helper_updata(query):

    with pymysql.connect(host="localhost", database=HelperDBName, user=HelperDBUser, password=HelperDBPass) as connect:

        db = connect.cursor()

        db.execute(query)

        connect.commit()



update_data("""

CREATE TABLE IF NOT EXISTS bot(

status varchar(10) DEFAULT 'ON'

) default charset=utf8mb4;

""")

update_data("""

CREATE TABLE IF NOT EXISTS user(

id bigint PRIMARY KEY,

step varchar(150) DEFAULT 'none',

phone varchar(150) DEFAULT NULL,

amount bigint DEFAULT '0',

expir bigint DEFAULT '0',

account varchar(50) DEFAULT 'unverified',

self varchar(50) DEFAULT 'inactive',

pid bigint DEFAULT NULL

) default charset=utf8mb4;

""")

update_data("""

CREATE TABLE IF NOT EXISTS block(

id bigint PRIMARY KEY

) default charset=utf8mb4;

""")

helper_updata("""

CREATE TABLE IF NOT EXISTS ownerlist(

id bigint PRIMARY KEY

) default charset=utf8mb4;

""")

helper_updata("""

CREATE TABLE IF NOT EXISTS adminlist(

id bigint PRIMARY KEY

) default charset=utf8mb4;

""")



bot = get_data("SELECT * FROM bot")

if bot is None:

    update_data("INSERT INTO bot() VALUES()")



OwnerUser = helper_getdata(f"SELECT * FROM ownerlist WHERE id = '{Admin}' LIMIT 1")

if OwnerUser is None:

    helper_updata(f"INSERT INTO ownerlist(id) VALUES({Admin})")



AdminUser = helper_getdata(f"SELECT * FROM adminlist WHERE id = '{Admin}' LIMIT 1")

if AdminUser is None:

    helper_updata(f"INSERT INTO adminlist(id) VALUES({Admin})")



def add_admin(user_id):

    if helper_getdata(f"SELECT * FROM adminlist WHERE id = '{user_id}' LIMIT 1") is None:

        helper_updata(f"INSERT INTO adminlist(id) VALUES({user_id})")



def delete_admin(user_id):

    if helper_getdata(f"SELECT * FROM adminlist WHERE id = '{user_id}' LIMIT 1") is not None:

        helper_updata(f"DELETE FROM adminlist WHERE id = '{user_id}' LIMIT 1")



def checker(func):

    @wraps(func)

    async def wrapper(c, m, *args, **kwargs):

        chat_id = m.chat.id if hasattr(m, "chat") else m.from_user.id

        bot = get_data("SELECT * FROM bot")

        block = get_data(f"SELECT * FROM block WHERE id = '{chat_id}' LIMIT 1")



        if block is not None and chat_id != Admin:

            return

        

        try:

            await app.get_chat_member(Channel_ID, chat_id)

        except errors.UserNotParticipant:

            await app.send_message(chat_id, """**• برای استفاده از خدمات ما باید ابتدا در کانال ما عضو باشید ، بعد از اینکه عضو شدید ربات را مجدد استارت کنید.
/start**""", reply_markup=InlineKeyboardMarkup(

                [

                    [

                        InlineKeyboardButton(text="عضویت", url=f"https://t.me/{Channel_ID}")

                    ]

                ]

            ))

            return

        except errors.ChatAdminRequired:

            if chat_id == Admin:

                await app.send_message(Admin, "ربات برای فعال شدن جوین اجباری در کانال مورد نظر ادمین نمی باشد!\nلطفا ربات را با دسترسی های لازم در کانال مورد نظر ادمین کنید")

            return



        if bot["status"] == "OFF" and chat_id != Admin:

            await app.send_message(chat_id, "**ربات خاموش میباشد!**")

            return

        

        return await func(c, m, *args, **kwargs)

    return wrapper



async def expirdec(user_id):

    user = get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1")

    user_expir = user["expir"]

    if user_expir > 0:

        user_upexpir = user_expir - 1

        update_data(f"UPDATE user SET expir = '{user_upexpir}' WHERE id = '{user_id}' LIMIT 1")

    else:

        job = scheduler.get_job(str(user_id))

        if job:

            scheduler.remove_job(str(user_id))

        if user_id != Admin:

            delete_admin(user_id)

        if os.path.isdir(f"selfs/self-{user_id}"):

            pid = user["pid"]

            os.kill(pid, signal.SIGKILL)

            await asyncio.sleep(1)

            shutil.rmtree(f"selfs/self-{user_id}")

        if os.path.isfile(f"sessions/{user_id}.session"):

            async with Client(f"sessions/{user_id}") as user_client:

                await user_client.log_out()

            if os.path.isfile(f"sessions/{user_id}.session"):

                os.remove(f"sessions/{user_id}.session")

        if os.path.isfile(f"sessions/{user_id}.session-journal"):

            os.remove(f"sessions/{user_id}.session-journal")

        await app.send_message(user_id, "کاربر گرامی اشتراک سلف شما به پایان رسید. برای خرید مجدد اشتراک به قسمت خرید اشتراک مراجعه کنید")

        update_data(f"UPDATE user SET self = 'inactive' WHERE id = '{user_id}' LIMIT 1")

        update_data(f"UPDATE user SET pid = NULL WHERE id = '{user_id}' LIMIT 1")



async def setscheduler(user_id):

    job = scheduler.get_job(str(user_id))

    if not job:

        scheduler.add_job(expirdec, "interval", hours=24, args=[user_id], id=str(user_id))



Main = InlineKeyboardMarkup(

    [

        [

            InlineKeyboardButton(text="👤 حساب کاربری", callback_data="MyAccount")

        ],

        [

            InlineKeyboardButton(text="💰 خرید سلف", callback_data="BuySub")

        ],

        [

            InlineKeyboardButton(text="💎 قیمت ها", callback_data="Price"),

            InlineKeyboardButton(text="💳 کیف پول", callback_data="Wallet")

        ],

        [

            InlineKeyboardButton(text="✅ احراز هویت", callback_data="AccVerify"),

            InlineKeyboardButton(text="🔰 اطلاعات سلف", callback_data="Subinfo")

        ],

        [

            InlineKeyboardButton(text="📢 کانال ما", url="https://t.me/DisVpn"),

            InlineKeyboardButton(text="❓ سلف چیست؟", callback_data="WhatSelf")

        ],

        [

            InlineKeyboardButton(text="🎧 پشتیبانی", callback_data="Support")

        ]

    ]

)



@app.on_message(filters.private, group=-1)

async def update(c, m):

    user = get_data(f"SELECT * FROM user WHERE id = '{m.chat.id}' LIMIT 1")

    if user is None:

        update_data(f"INSERT INTO user(id) VALUES({m.chat.id})")



@app.on_message(filters.private&filters.command("start"))

@checker

async def update(c, m):

    await app.send_message(m.chat.id, f"""**╭─────────────────────╮
│   🌟 سلام عزیز {html.escape(m.chat.first_name)} 🌟   │
│ 🎉 به Wenos Self خوش آمدید 🎉 │
╰─────────────────────╯

🤖 من دستیار هوشمند شما هستم
💡 بهترین تجربه مدیریت اکانت را برایتان فراهم می‌کنم

🔹━━━━━━━━━━━━━━━━━━━━━━━🔹
       ✨ ویژگی‌های برتر ما ✨
🔹━━━━━━━━━━━━━━━━━━━━━━━🔹

⚡ سرعت بی‌نظیر
🚀 امکانات پیشرفته
🔄 بدون قطعی
🚫 بدون تبلیغات مزاحم

🎯 یک خرید، تجربه‌ای بی‌نقص! 🎯**""", reply_markup=Main)

    update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")

    async with lock:

        if m.chat.id in temp_Client:

            del temp_Client[m.chat.id]

    if os.path.isfile(f"sessions/{m.chat.id}.session") and not os.path.isfile(f"sessions/{m.chat.id}.session-journal"):

        os.remove(f"sessions/{m.chat.id}.session")



@app.on_callback_query()

@checker

async def call(c, call):

    global temp_Client

    user = get_data(f"SELECT * FROM user WHERE id = '{call.from_user.id}' LIMIT 1")

    phone_number = user["phone"]

    account_status = "تایید شده" if user["account"] == "verified" else "تایید نشده"

    expir = user["expir"]

    amount = user["amount"]

    chat_id = call.from_user.id

    m_id = call.message.id

    data = call.data

    username = f"@{call.from_user.username}" if call.from_user.username else "وجود ندارد"



    if data == "MyAccount":

        await app.edit_message_text(chat_id, m_id, "**╭─────────────────────────╮\n│     👤 حساب کاربری شما     │\n╰─────────────────────────╯\n\n📊 اطلاعات کامل حساب شما:**", reply_markup=InlineKeyboardMarkup(

            [

                [

                    InlineKeyboardButton(text="نام شما", callback_data="text"),

                    InlineKeyboardButton(text=f"{call.from_user.first_name}", callback_data="text")

                ],

                [

                    InlineKeyboardButton(text="آیدی شما", callback_data="text"),

                    InlineKeyboardButton(text=f"{call.from_user.id}", callback_data="text")

                ],

                [

                    InlineKeyboardButton(text="یوزرنیم شما", callback_data="text"),

                    InlineKeyboardButton(text=f"{username}", callback_data="text")

                ],

                [

                    InlineKeyboardButton(text="موجودی شما", callback_data="text"),

                    InlineKeyboardButton(text=f"{amount} تومان", callback_data="text")

                ],

                [

                    InlineKeyboardButton(text="وضعیت حساب شما", callback_data="text"),

                    InlineKeyboardButton(text=f"{account_status}", callback_data="text")

                ],

                [

                    InlineKeyboardButton(text="----------------", callback_data="text")

                ],

                [

                    InlineKeyboardButton(text=f"انقضای شما ({expir}) روز", callback_data="text")

                ],

                [

                    InlineKeyboardButton(text="برگشت", callback_data="Back")

                ]

            ]

        ))

        update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")



    elif data == "BuySub" or data == "Back2":

        if user["phone"] is None:

            await app.delete_messages(chat_id, m_id)

            await app.send_message(chat_id, "**لطفا با استفاده از دکمه زیر شماره خود را به اشتراک بگذارید**", reply_markup=ReplyKeyboardMarkup(

                [

                    [

                        KeyboardButton(text="اشتراک گذاری شماره", request_contact=True)

                    ]

                ],resize_keyboard=True

            ))

            update_data(f"UPDATE user SET step = 'contact' WHERE id = '{call.from_user.id}' LIMIT 1")

        else:

            if user["account"] == "verified":

                if not os.path.isfile(f"sessions/{chat_id}.session-journal"):

                    await app.edit_message_text(chat_id, m_id, "**🛒 انتخاب پلن اشتراک**\n\n💰 لطفاً پلن مورد نظر خود را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(

                        [

                            [

                                InlineKeyboardButton(text="⏰ یک هفته  •  💰 20 تومان", callback_data="Login-7-20")

                            ],

                            [

                                InlineKeyboardButton(text="📅 یک ماهه  •  💰 50 تومان", callback_data="Login-30-50")

                            ],

                            [

                                InlineKeyboardButton(text="📅 دو ماهه  •  💰 100 تومان", callback_data="Login-60-100")

                            ],

                            [

                                InlineKeyboardButton(text="📅 سه ماهه  •  💰 150 تومان", callback_data="Login-90-150")

                            ],

                            [

                                InlineKeyboardButton(text="📅 چهار ماهه  •  💰 200 تومان", callback_data="Login-120-200")

                            ],

                            [

                                InlineKeyboardButton(text="📅 پنج ماهه  •  💰 250 تومان", callback_data="Login-150-250")

                            ],

                            [

                                InlineKeyboardButton(text="برگشت", callback_data="Back")

                            ]

                        ]

                    ))

                    update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")

                    async with lock:

                        if chat_id in temp_Client:

                            del temp_Client[chat_id]

                    if os.path.isfile(f"sessions/{chat_id}.session") and not os.path.isfile(f"sessions/{chat_id}.session-journal"):

                        os.remove(f"sessions/{chat_id}.session")

                else:

                    await app.answer_callback_query(call.id, text="اشتراک سلف برای شما فعال است!", show_alert=True)

            else:

                await app.edit_message_text(chat_id, m_id, "برای خرید اشتراک ابتدا باید احراز هویت کنید", reply_markup=InlineKeyboardMarkup(

                    [

                        [

                            InlineKeyboardButton(text="احراز هویت", callback_data="AccVerify")

                        ],

                        [

                            InlineKeyboardButton(text="برگشت", callback_data="Back")

                        ]

                    ]

                ))

                update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")



    elif data.split("-")[0] == "Login":

        expir_count = data.split("-")[1]

        cost = data.split("-")[2]

        if int(amount) >= int(cost):

            mess = await app.edit_message_text(chat_id, m_id, "در حال پردازش...")

            async with lock:

                if chat_id not in temp_Client:

                    temp_Client[chat_id] = {}

                temp_Client[chat_id]["client"] = Client(f"sessions/{chat_id}", api_id=API_ID, api_hash=API_HASH, device_model="Wenos-Self", system_version="Linux")

                temp_Client[chat_id]["number"] = phone_number

                await temp_Client[chat_id]["client"].connect()

            try:

                await app.edit_message_text(chat_id, mess.id, "کد تایید 5 رقمی را با فرمت زیر ارسال کنید:\n1.2.3.4.5", reply_markup=InlineKeyboardMarkup(

                    [

                        [

                            InlineKeyboardButton(text="برگشت", callback_data="Back2")

                        ]

                    ]

                ))

                async with lock:

                    temp_Client[chat_id]["response"] = await temp_Client[chat_id]["client"].send_code(temp_Client[chat_id]["number"])

                update_data(f"UPDATE user SET step = 'login1-{expir_count}-{cost}' WHERE id = '{call.from_user.id}' LIMIT 1")



            except errors.BadRequest:

                await app.edit_message_text(chat_id, mess.id, "اتصال ناموفق بود! لطفا دوباره تلاش کنید", reply_markup=InlineKeyboardMarkup(

                    [

                        [

                            InlineKeyboardButton(text="برگشت", callback_data="Back2")

                        ]

                    ]

                ))

                update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")

                async with lock:

                    await temp_Client[chat_id]["client"].disconnect()

                    if chat_id in temp_Client:

                        del temp_Client[chat_id]

                if os.path.isfile(f"sessions/{chat_id}.session"):

                    os.remove(f"sessions/{chat_id}.session")



            except errors.PhoneNumberInvalid:

                await app.edit_message_text(chat_id, mess.id, "این شماره نامعتبر است!", reply_markup=InlineKeyboardMarkup(

                    [

                        [

                            InlineKeyboardButton(text="برگشت", callback_data="Back2")

                        ]

                    ]

                ))

                update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")

                async with lock:

                    await temp_Client[chat_id]["client"].disconnect()

                    if chat_id in temp_Client:

                        del temp_Client[chat_id]

                if os.path.isfile(f"sessions/{chat_id}.session"):

                    os.remove(f"sessions/{chat_id}.session")



            except errors.PhoneNumberBanned:

                await app.edit_message_text(chat_id, mess.id, "این اکانت محدود است!", reply_markup=InlineKeyboardMarkup(

                    [

                        [

                            InlineKeyboardButton(text="برگشت", callback_data="Back2")

                        ]

                    ]

                ))

                update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")

                async with lock:

                    await temp_Client[chat_id]["client"].disconnect()

                    if chat_id in temp_Client:

                        del temp_Client[chat_id]

                if os.path.isfile(f"sessions/{chat_id}.session"):

                    os.remove(f"sessions/{chat.id}.session")



            except Exception:

                async with lock:

                    await temp_Client[chat_id]["client"].disconnect()

                    if chat_id in temp_Client:

                        del temp_Client[chat_id]

                if os.path.isfile(f"sessions/{chat_id}.session"):

                    os.remove(f"sessions/{chat_id}.session")

        else:

            await app.edit_message_text(chat_id, m_id, "موجودی حساب شما برای خرید این اشتراک کافی نیست", reply_markup=InlineKeyboardMarkup(

                [

                    [

                        InlineKeyboardButton(text="افزایش موجودی", callback_data="Wallet")

                    ],

                    [

                        InlineKeyboardButton(text="برگشت", callback_data="Back2")

                    ]

                ]

            ))

            update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")



    elif data == "Price":

        await app.edit_message_text(chat_id, m_id, """**💎 جدول قیمت اشتراک سلف 💎

╭─────────────────────────╮
│        📋 تعرفه ها         │
╰