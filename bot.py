from telegram import Update, InputFile, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import json
import io
import os
import base64

# === Admin ID-lar ===
ADMIN_IDS = [1483283523, 838372282, 8053276571]  # Bu yerga o'z Telegram ID'ingizni yozing

# === Google Sheets API ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_dict = json.loads(os.environ["GOOGLE_CREDS"])
credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)

SPREADSHEET_ID = "190Sl3isWneTfx89rohDZQ1aLPm2x7LzejQ9ZywzVTAI"
SHEET_NAME = "tahlil"

# === /start komandasi ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Sizda bu botdan foydalanish huquqi yo‘q.")
        return

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("📄 Tahlilni PDF qilish")]],
        resize_keyboard=True
    )
    await update.message.reply_text("Kerakli amalni tanlang:", reply_markup=keyboard)

# === PDF tayyorlash ===
async def handle_pdf_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Ruxsat yo‘q.")
        return

    if update.message.text != "📄 Tahlilni PDF qilish":
        return

    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    data = sheet.get_all_values()
    data = [row[:5] for row in data]  # A:E ustunlar

    total = sheet.acell("F1").value

    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
    elements = []

    # Sarlavha
    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    title_style.alignment = 1
    elements.append(Paragraph("📊 Tahlil", title_style))
    elements.append(Spacer(1, 8))

    # Umumiy son (sariq fon bilan)
    from reportlab.platypus import Table
    total_text = [[f"Jami soni: {total} dona"]]
    total_table = Table(total_text, colWidths=[480])
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFF176")),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#333333")),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(total_table)
    elements.append(Spacer(1, 10))

    # Jadval
    col_widths = [100, 50, 120, 60, 60]
    table = Table(data, colWidths=col_widths, hAlign='CENTER')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#3E4E5E")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('FONTSIZE', (0, 1), (0, -1), 12),
        ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor("#222222")),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
    ]))
    elements.append(table)

    # Sana
    today = datetime.now().strftime("%d.%m.%Y %H:%M")
    info_style = ParagraphStyle("info", fontSize=8, textColor=colors.grey)
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"PDF fayli avtomatik yaratildi | Sana: {today}", info_style))

    pdf.build(elements)
    buffer.seek(0)

    filename = f"tahlil_report_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.pdf"
    await update.message.reply_document(document=InputFile(buffer, filename=filename))

# === Botni ishga tushurish ===
app = ApplicationBuilder().token("7697283410:AAHQShzs-p15e3zGpS_onXYbe4kEeGbQVyc").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pdf_request))

if __name__ == "__main__":
    app.run_polling()
