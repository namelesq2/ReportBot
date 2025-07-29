import re
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config import TOKEN, GROUP_CHAT_ID
from datetime import datetime, timedelta
import pytz

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()
user_reports = {}
def parse_report_line(line):
    match = re.match(r"^([А-Яа-яЁёA-Za-z\s\-]+) - (\d+)/(\d+)/(\d+)$", line.strip())
    if not match:
        return None
    name = match.group(1).strip()
    try:
        sales = int(match.group(2))
        calls = int(match.group(3))
        percent = int(match.group(4))
        return name, sales, calls, percent
    except ValueError:
        return None

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот для сбора отчётов.\n\n"
        "📩 Отправьте отчёт в формате:\n"
        "`Фамилия И - X/Y/Z`\n"
        "где X — оплаты, Y — звонки, Z — % выполнения плана\n\n"
        "Пример:\n"
        "`Иванов И - 3/20/80`\n\n"
        "✅ Отчёт будет отправлен в группу в 18:30 по МСК.",
        parse_mode="Markdown"
    )

@dp.message_handler(lambda message: '-' in message.text and '/' in message.text)
async def collect_report(message: types.Message):
    user_id = message.from_user.id
    lines = message.text.strip().split("\n")
    entries = []

    for line in lines:
        parsed = parse_report_line(line)
        if not parsed:
            await message.reply(f"❌ Неверный формат строки:\n`{line}`\n\nФормат должен быть: `Фамилия И - X/Y/Z`", parse_mode="Markdown")
            return
        entries.append(parsed)

    user_reports[user_id] = entries
    await message.answer("✅ Отчёт принят. В 18:30 он будет обработан и отправлен в группу.")

async def send_scheduled_report():
    if not user_reports:
        return

    all_entries = []
    total_sales = total_calls = total_percent = 0

    report_lines = ["📊 *Отчёт за день:*", ""]

    for entries in user_reports.values():
        for name, sales, calls, percent in entries:
            sales_eff = min(sales / 4, 1)
            calls_eff = min(calls / 60, 1)
            efficiency = round((sales_eff + calls_eff) / 2 * 100)
            report_lines.append(f"{name} — {efficiency}%")
            total_sales += sales
            total_calls += calls
            total_percent += percent
            all_entries.append(1)

    if all_entries:
        avg_sales = total_sales
        avg_calls = total_calls
        avg_percent = round(total_percent / len(all_entries))
        avg_efficiency = round(((avg_sales / 4) + (avg_calls / 60)) / 2 / len(all_entries) * 100, 2)

        report_lines.append("")
        report_lines.append(f"*ИТОГ ФИЛИАЛА:* {avg_sales}/{avg_calls}/{avg_percent}%")
        report_lines.append(f"*Средняя эффективность:* {avg_efficiency}%")

        await bot.send_message(GROUP_CHAT_ID, "\n".join(report_lines), parse_mode="Markdown")

    user_reports.clear()

moscow_tz = pytz.timezone("Europe/Moscow")
scheduler.add_job(send_scheduled_report, CronTrigger(hour=18, minute=30, timezone=moscow_tz))
scheduler.start()

if __name__ == "__main__":
    print("✅ Бот запущен.")
    executor.start_polling(dp, skip_updates=True)