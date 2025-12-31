import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, 
    CallbackContext, CallbackQueryHandler, ConversationHandler
)
from db_service import (
    init_db, add_user, get_user, create_request, 
    update_request_pdf, deduct_balance, update_balance, 
    get_stats, get_all_users
)
from config import BOT_TOKEN

# إعدادات التسجيل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# الإعدادات العامة
PRICE_SAR = 10
WHATSAPP_LINK = "https://wa.me/966777314420"
ADMIN_IDS = [6777656326]
PLATFORM_NAME = "منصة عمر راجون للسكاليف الطبية"

# حالات المحادثة
(FULL_NAME, WORK_PLACE, ID_NUMBER, BIRTH_DATE, 
 JOB_TITLE, NATIONALITY, REGION, HOSPITAL, LEAVE_DATE, CONFIRM_DATA) = range(10)
ADD_BALANCE_ID, ADD_BALANCE_AMOUNT = range(10, 12)
BROADCAST_MSG = 12

def get_main_keyboard(user_id):
    keyboard = [
        [InlineKeyboardButton("طلب سكليف جديد 📝", callback_data="req_sick")],
        [InlineKeyboardButton("شحن رصيد 💳", callback_data="charge_balance")],
        [InlineKeyboardButton("مساعدة ❓", callback_data="help"), InlineKeyboardButton("عن المنصة ℹ️", callback_data="about")]
    ]
    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("لوحة تحكم المدير ⚙️", callback_data="admin_menu")])
    return InlineKeyboardMarkup(keyboard)

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    existing = get_user(user.id)
    if not existing:
        add_user(user.id, user.username, user.full_name)
        msg = f"مرحباً بك في زيارتك الأولى لـ *{PLATFORM_NAME}*! 🏥✨"
    else:
        msg = f"أهلاً بعودتك إلى *{PLATFORM_NAME}*! 🏥👋"
    
    u = get_user(user.id)
    text = (
        f"{msg}\n\n"
        f"👤 *الاسم:* {user.full_name}\n"
        f"🆔 *المعرف:* `{user.id}`\n"
        f"💰 *الرصيد الحالي:* `{u['balance'] if u else 0}` ريال\n\n"
        f"💵 *تكلفة الخدمة:* {PRICE_SAR} ريال سعودي\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اختر من القائمة أدناه للبدء 👇"
    )
    reply_markup = get_main_keyboard(user.id)
    if update.message:
        update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

def req_sick_start(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    u = get_user(query.from_user.id)
    if u and u['balance'] >= PRICE_SAR:
        query.edit_message_text(
            "✅ *رصيدك كافٍ للبدء.*\n\n"
            "يرجى تزويدنا بالبيانات التالية بدقة:\n"
            "1️⃣ أرسل *الاسم الرباعي* للمريض:\n\n"
            "💡 _يمكنك إرسال /cancel في أي وقت للإلغاء_",
            parse_mode='Markdown'
        )
        return FULL_NAME
    else:
        kb = [
            [InlineKeyboardButton("شحن عبر الواتساب 📲", url=WHATSAPP_LINK)],
            [InlineKeyboardButton("الرجوع للقائمة الرئيسية 🔙", callback_data="main_menu")]
        ]
        query.edit_message_text(
            f"❌ *عذراً، رصيدك غير كافٍ.*\n\n"
            f"💰 رصيدك الحالي: `{u['balance'] if u else 0}` ريال\n"
            f"💵 التكلفة المطلوبة: `{PRICE_SAR}` ريال\n\n"
            f"يرجى شحن رصيدك للمتابعة.",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode='Markdown'
        )
        return ConversationHandler.END

def get_full_name(update: Update, context: CallbackContext) -> int:
    context.user_data['full_name_quad'] = update.message.text
    update.message.reply_text("2️⃣ يرجى إرسال *جهة العمل*:", parse_mode='Markdown')
    return WORK_PLACE

def get_work_place(update: Update, context: CallbackContext) -> int:
    context.user_data['work_place'] = update.message.text
    update.message.reply_text("3️⃣ يرجى إرسال *رقم الهوية أو الإقامة*:", parse_mode='Markdown')
    return ID_NUMBER

def get_id_number(update: Update, context: CallbackContext) -> int:
    context.user_data['id_number'] = update.message.text
    update.message.reply_text("4️⃣ يرجى إرسال *تاريخ الميلاد* (مثال: 1990/01/01):", parse_mode='Markdown')
    return BIRTH_DATE

def get_birth_date(update: Update, context: CallbackContext) -> int:
    context.user_data['birth_date'] = update.message.text
    update.message.reply_text("5️⃣ يرجى إرسال *المسمى الوظيفي*:", parse_mode='Markdown')
    return JOB_TITLE

def get_job_title(update: Update, context: CallbackContext) -> int:
    context.user_data['job_title'] = update.message.text
    update.message.reply_text("6️⃣ يرجى إرسال *الجنسية*:", parse_mode='Markdown')
    return NATIONALITY

def get_nationality(update: Update, context: CallbackContext) -> int:
    context.user_data['nationality'] = update.message.text
    update.message.reply_text("7️⃣ يرجى إرسال *المنطقة*:", parse_mode='Markdown')
    return REGION

def get_region(update: Update, context: CallbackContext) -> int:
    context.user_data['region'] = update.message.text
    update.message.reply_text("8️⃣ يرجى إرسال *اسم المستشفى*:", parse_mode='Markdown')
    return HOSPITAL

def get_hospital(update: Update, context: CallbackContext) -> int:
    context.user_data['hospital'] = update.message.text
    update.message.reply_text("9️⃣ يرجى إرسال *تاريخ بداية الإجازة* (مثال: 2024/01/01):", parse_mode='Markdown')
    return LEAVE_DATE

def get_leave_date(update: Update, context: CallbackContext) -> int:
    context.user_data['leave_date'] = update.message.text
    
    # عرض معاينة للبيانات قبل التأكيد
    preview_text = (
        "📋 *معاينة البيانات المدخلة:*\n"
        "━━━━━━━━━━━━━━━\n"
        f"👤 *الاسم:* {context.user_data['full_name_quad']}\n"
        f"🏢 *جهة العمل:* {context.user_data['work_place']}\n"
        f"🆔 *رقم الهوية:* `{context.user_data['id_number']}`\n"
        f"📅 *تاريخ الميلاد:* {context.user_data['birth_date']}\n"
        f"💼 *الوظيفة:* {context.user_data['job_title']}\n"
        f"🌍 *الجنسية:* {context.user_data['nationality']}\n"
        f"📍 *المنطقة:* {context.user_data['region']}\n"
        f"🏥 *المستشفى:* {context.user_data['hospital']}\n"
        f"🗓 *تاريخ الإجازة:* {context.user_data['leave_date']}\n"
        "━━━━━━━━━━━━━━━\n"
        "⚠️ *هل البيانات صحيحة؟* سيتم خصم الرصيد عند التأكيد."
    )
    
    kb = [
        [InlineKeyboardButton("نعم، تأكيد وإصدار ✅", callback_data="confirm_yes")],
        [InlineKeyboardButton("إلغاء العملية ❌", callback_data="confirm_no")]
    ]
    
    update.message.reply_text(preview_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    return CONFIRM_DATA

def process_confirmation(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    
    if query.data == "confirm_yes":
        from pdf_generator import generate_medical_pdf
        user_id = update.effective_user.id
        
        if deduct_balance(user_id, PRICE_SAR):
            query.edit_message_text("⏳ *جاري معالجة الطلب وتوليد الشهادة...*", parse_mode='Markdown')
            rid = create_request(user_id, context.user_data)
            try:
                path = generate_medical_pdf(rid, context.user_data)
                update_request_pdf(rid, path)
                with open(path, 'rb') as f:
                    context.bot.send_document(
                        chat_id=user_id,
                        document=f,
                        filename=f"Medical_Leave_{rid}.pdf",
                        caption=f"✅ *تم إصدار الشهادة بنجاح!*\n\nشكراً لاستخدامك {PLATFORM_NAME}.",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("الرجوع للقائمة الرئيسية 🔙", callback_data="main_menu")]]),
                        parse_mode='Markdown'
                    )
            except Exception as e:
                logger.error(f"Error generating PDF: {e}")
                query.edit_message_text("❌ *عذراً، حدث خطأ أثناء توليد الملف.* يرجى التواصل مع الدعم.")
        else:
            query.edit_message_text("❌ *خطأ في الرصيد.* يرجى التأكد من شحن رصيدك.")
    else:
        query.edit_message_text("❌ *تم إلغاء العملية.* يمكنك البدء من جديد في أي وقت.")
    
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "🚫 *تم إلغاء العملية.*", 
        reply_markup=get_main_keyboard(update.effective_user.id),
        parse_mode='Markdown'
    )
    return ConversationHandler.END

def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    if data == "main_menu":
        start(update, context)
    elif data == "admin_menu":
        if user_id in ADMIN_IDS:
            kb = [
                [InlineKeyboardButton("إحصائيات المنصة 📊", callback_data="admin_stats")],
                [InlineKeyboardButton("شحن رصيد لمستخدم 💰", callback_data="admin_add_balance")],
                [InlineKeyboardButton("قائمة المستخدمين 👥", callback_data="admin_list_users")],
                [InlineKeyboardButton("إرسال رسالة جماعية 📢", callback_data="admin_broadcast")],
                [InlineKeyboardButton("الرجوع 🔙", callback_data="main_menu")]
            ]
            query.edit_message_text("🛠 *لوحة تحكم المدير*", reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    elif data == "admin_stats":
        u_count, r_count = get_stats()
        query.edit_message_text(
            f"📊 *إحصائيات المنصة:*\n\n"
            f"👥 عدد المستخدمين: `{u_count}`\n"
            f"📝 إجمالي الطلبات: `{r_count}`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("الرجوع 🔙", callback_data="admin_menu")]]),
            parse_mode='Markdown'
        )
    elif data == "charge_balance":
        kb = [
            [InlineKeyboardButton("تواصل عبر الواتساب 📲", url=WHATSAPP_LINK)],
            [InlineKeyboardButton("الرجوع 🔙", callback_data="main_menu")]
        ]
        query.edit_message_text(
            "💳 *شحن الرصيد*\n\n"
            "لشحن رصيدك، يرجى التواصل مع الإدارة مباشرة عبر الواتساب وتزويدهم بمعرفك الخاص.",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode='Markdown'
        )
    elif data == "help":
        query.edit_message_text(
            "❓ *المساعدة والدعم*\n\n"
            "إذا واجهت أي مشكلة أو كان لديك استفسار، نحن هنا لخدمتك.\n"
            "تواصل معنا عبر الواتساب للحصول على دعم فوري.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تواصل معنا 📲", url=WHATSAPP_LINK)], [InlineKeyboardButton("الرجوع 🔙", callback_data="main_menu")]]),
            parse_mode='Markdown'
        )
    elif data == "about":
        query.edit_message_text(
            f"ℹ️ *عن {PLATFORM_NAME}*\n\n"
            f"تعتبر منصتنا الحل الأمثل والأسرع للحصول على التقارير والسكاليف الطبية الموثقة إلكترونياً.\n\n"
            f"نحن نسعى دائماً لتقديم أفضل تجربة مستخدم بأعلى معايير الجودة.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("الرجوع 🔙", callback_data="main_menu")]]),
            parse_mode='Markdown'
        )
    elif data == "admin_list_users":
        if user_id in ADMIN_IDS:
            users = get_all_users(20)
            text = "👥 *قائمة آخر 20 مستخدم:*\n\n"
            for u in users:
                text += f"• `{u['user_id']}` | {u['full_name']} | رصيد: `{u['balance']}`\n"
            query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("الرجوع 🔙", callback_data="admin_menu")]]), parse_mode='Markdown')

def admin_add_balance_start(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text("🆔 يرجى إرسال *معرف المستخدم (User ID)* المراد شحن رصيده:\n\n(أرسل /cancel للإلغاء)", parse_mode='Markdown')
    return ADD_BALANCE_ID

def admin_get_id(update: Update, context: CallbackContext) -> int:
    context.user_data['target_id'] = update.message.text
    update.message.reply_text(f"💰 أدخل *المبلغ* المراد إضافته للمستخدم `{context.user_data['target_id']}`:", parse_mode='Markdown')
    return ADD_BALANCE_AMOUNT

def admin_get_amount(update: Update, context: CallbackContext) -> int:
    try:
        target_id = int(context.user_data['target_id'])
        amount = float(update.message.text)
        update_balance(target_id, amount)
        # إرسال إشعار للمستخدم
        try:
            context.bot.send_message(
                chat_id=target_id,
                text=f"💰 *تم شحن رصيدك بنجاح!*\n\nتم إضافة `{amount}` ريال إلى حسابك.\nرصيدك الحالي أصبح متوفراً الآن لاستخدام الخدمات.",
                parse_mode='Markdown'
            )
        except Exception as notify_error:
            logger.error(f"Failed to notify user {target_id}: {notify_error}")
            
        update.message.reply_text(
            f"✅ *تمت العملية بنجاح!*\n\nتم إضافة `{amount}` ريال لرصيد المستخدم `{target_id}`.\nتم إرسال إشعار للمستخدم أيضاً.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("الرجوع للوحة المدير 🔙", callback_data="admin_menu")]]),
            parse_mode='Markdown'
        )
    except Exception as e:
        update.message.reply_text(f"❌ *حدث خطأ:* {e}")
    return ConversationHandler.END

def admin_broadcast_start(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text("📢 يرجى إرسال *الرسالة* التي تود إرسالها لجميع المستخدمين:\n\n(أرسل /cancel للإلغاء)", parse_mode='Markdown')
    return BROADCAST_MSG

def admin_broadcast_send(update: Update, context: CallbackContext) -> int:
    msg = update.message.text
    users = get_all_users(1000) # جلب عدد كبير من المستخدمين
    count = 0
    for u in users:
        try:
            context.bot.send_message(chat_id=u['user_id'], text=f"📢 *رسالة من الإدارة:*\n\n{msg}", parse_mode='Markdown')
            count += 1
        except:
            continue
    update.message.reply_text(f"✅ تم إرسال الرسالة إلى `{count}` مستخدم.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("الرجوع للوحة المدير 🔙", callback_data="admin_menu")]]), parse_mode='Markdown')
    return ConversationHandler.END

def main():
    init_db()
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # محادثة طلب السكليف
    sick_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(req_sick_start, pattern='^req_sick$')],
        states={
            FULL_NAME: [MessageHandler(Filters.text & ~Filters.command, get_full_name)],
            WORK_PLACE: [MessageHandler(Filters.text & ~Filters.command, get_work_place)],
            ID_NUMBER: [MessageHandler(Filters.text & ~Filters.command, get_id_number)],
            BIRTH_DATE: [MessageHandler(Filters.text & ~Filters.command, get_birth_date)],
            JOB_TITLE: [MessageHandler(Filters.text & ~Filters.command, get_job_title)],
            NATIONALITY: [MessageHandler(Filters.text & ~Filters.command, get_nationality)],
            REGION: [MessageHandler(Filters.text & ~Filters.command, get_region)],
            HOSPITAL: [MessageHandler(Filters.text & ~Filters.command, get_hospital)],
            LEAVE_DATE: [MessageHandler(Filters.text & ~Filters.command, get_leave_date)],
            CONFIRM_DATA: [CallbackQueryHandler(process_confirmation, pattern='^confirm_')],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    
    # محادثة شحن الرصيد والرسائل الجماعية (للمدير)
    admin_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_add_balance_start, pattern='^admin_add_balance$'),
            CallbackQueryHandler(admin_broadcast_start, pattern='^admin_broadcast$')
        ],
        states={
            ADD_BALANCE_ID: [MessageHandler(Filters.text & ~Filters.command, admin_get_id)],
            ADD_BALANCE_AMOUNT: [MessageHandler(Filters.text & ~Filters.command, admin_get_amount)],
            BROADCAST_MSG: [MessageHandler(Filters.text & ~Filters.command, admin_broadcast_send)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(sick_conv)
    dp.add_handler(admin_conv)
    dp.add_handler(CallbackQueryHandler(button_handler))
    
    logger.info("Starting bot...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
