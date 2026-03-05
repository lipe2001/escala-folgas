from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from ..settings import settings
import csv
from ..repository import weekend, employee
from ..routers import public
from pathlib import Path
from collections import defaultdict
import datetime

BASE_DIR = Path(__file__).resolve().parent


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Olá {update.effective_user.first_name}! Você deseja ser notificado? \n Se sim, envie /subscribe.')

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        with open(Path(BASE_DIR,"./data.csv"), 'r') as file:
            read = csv.reader(file)
            users = []
            for user in read:
                users.append(user)
    except:
        users = []
    user_id = update.effective_user.id
    if [str(user_id)] not in users:
        users.append([str(user_id)])
        with open(Path(BASE_DIR,"./data.csv"), 'w', newline='') as json_file:
            writer = csv.writer(json_file)
            writer.writerows(users)
        await update.message.reply_text('Você foi inscrito para receber as notificações!')
    else:
        await update.message.reply_text('Você já está inscrito!')

async def send_message( text: str):
    with open(Path(BASE_DIR,"./data.csv"), 'r') as file:
        users = csv.reader(file)
        for chat_id in users:

            await app.bot.send_message(chat_id=chat_id[0], text=text)


async def send_folgas_by_day():

    msg = "Bom Dia! A escala de férias da semana foi publicada. Por favor, verifique seu calendário.\n\n"
    ferias = public.folgas_week(0)
    grouped = defaultdict(list)

    for emp in ferias:
        date_str = emp['day']  
        grouped[date_str].append(emp['full_name'].title())

    weekday_map = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

    def format_date_label(date_str: str) -> str:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        weekday = weekday_map[dt.weekday()]
        return f"{weekday}, dia {dt.day:02d}"

    for date_str in sorted(grouped.keys(), key=lambda d: datetime.datetime.strptime(d, "%Y-%m-%d")):
        label = format_date_label(date_str)
        msg += f"{label}: {', '.join(grouped[date_str])}\n"

    await send_message(text=msg)
async def send_status():
    dias = defaultdict(list)
    semana = ["Segunda","Terça","Quarta", "Quinta","Sexta"]
    msg = "Bom Dia! A escala de folgas da semana foi publicado. Por favor, verifique seu calendário. \n\n\n"
    ferias = public.folgas_week(0)
    for emp in ferias:
        dia = emp['day'].split('-')[-1]
        msg += f"Dia {dia}: {emp['full_name'].title()} \n"
    await send_message(text=msg)
app = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()



async def send_week(id:int):
    weekend_dao = weekend.WeekendDAO()

    employee_dao = employee.EmployeeDAO()
    week = weekend_dao.getById(id)
    msg = "Olá! A escala do plantão do fim de semana foi publicada. Por favor, verifique seu calendário. \n\n"
    msg += f"Sábado - Equipe {week.on_duty_team}: \n"
    list_activ = employee_dao.getActivesFromTeam(week.on_duty_team)
    for emp in list_activ:
        msg += emp.full_name.title() + "\n"
    msg += "\n Domingo:\n -> Manha: \n"
    manha = ""
    tarde = ""
    
    employeer = employee_dao.getSundayAssignments(int(id))
    for emp in employeer:
        if emp["role"] == "phone":
            emp["role"] = "Telefone"
        else:
            emp["role"] = "Huggy"

        if emp["period"] == "morning":
            manha += f" {emp['fullName'].title()} ({emp['role']}) \n"
        elif emp["period"] == "afternoon":
            tarde += f" {emp['fullName'].title()} ({emp['role']}) \n"

    msg += manha + "\n -> Tarde: \n" + tarde
    await send_message(text=msg)

app.add_handler(CommandHandler("start", hello))
app.add_handler(CommandHandler("subscribe", subscribe))



