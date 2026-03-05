from collections import defaultdict
from math import e
from pathlib import Path
from app.repository import employee
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from collections import defaultdict
from datetime import timedelta, date
from app.routers import public
from . import admin
from ..db import q
from ..repository import employee, weekend, batch
from ..auth_handler import encodeJWT
router = APIRouter(prefix="", tags=["frontend"])
BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(Path(BASE_DIR, '../frontend')))

router.mount("/static", StaticFiles(directory=str(Path(BASE_DIR, '../frontend/static'))), name="static")

batch_dao = batch.BatchDAO()
weekend_dao = weekend.WeekendDAO()
employee_dao = employee.EmployeeDAO()

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, position : int = 0):
    dias = defaultdict(list)
    ferias = public.folgas_week(position)
    if not ferias:
        if position < 0:
            url = "/?position=" + str(position + 1)  
        else:
            url = "/?position=" + str(position - 1)  
        return RedirectResponse(url=url, status_code=303)
    semana = [{"week" : "Segunda"},{"week" : "Terça"},{"week" : "Quarta"},{"week" : "Quinta"},{"week" : "Sexta"}]
    mesF = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]    
    for f in ferias:
        dias[f["day"]].append({"name":f["full_name"].capitalize(), "team": f["team"]})
    for idx, x in enumerate(dias.keys()):
        semana[idx]["day"] = x.split("-")[-1]
    try:  
      list_key = list(dias.keys())
      mes_number = list_key[2].split('-')
      mes_nome = mesF[int(mes_number[1]) -1].capitalize()
      mes = f"{mes_nome} - {mes_number[0]}"
    except:
      mes = ""
    data = list(dias.values())
    return templates.TemplateResponse(
        request=request, name="index.html", context = {"data":data, "week" : semana, "month": mes, "position": int(position)}
    )
    
@router.get("/weekend", response_class=HTMLResponse)
async def weekend(request: Request):

    wkend = weekend_dao.listWeekends()
    for week in wkend:
        sabado_formatado = date.fromisoformat(week.saturday)
        week.saturday = date.strftime(sabado_formatado, "%d/%m/%Y")
    return templates.TemplateResponse(
        request=request, name="pages/weekend.html", context = { "weekend": wkend }
    )
    
@router.get("/weekend/create", response_class=HTMLResponse)
async def create_weekend(request: Request, last : str = None):
    last_weekend = weekend_dao.getLastWeekend()
    if last_weekend:
        default_new_weekend = last_weekend["saturday"] + timedelta(weeks=1)
    else:
        default_new_weekend = ""


    return templates.TemplateResponse(
        request=request, name="pages/create-weekend.html", context={"new_weekend": default_new_weekend}
    )
    
@router.get("/sunday/create/{id}", response_class=HTMLResponse)
async def sundays(request: Request, id : str):
    team = weekend_dao.getById(id)
    emp  = employee_dao.getActivesFromTeam(team.on_duty_team)
    phone_assigned = weekend_dao.getCountPhoneWeekend(int(id))
    
    for employeer in emp:
        if employeer.role == "phone":
            employeer.role = "Telefone"
        else:
            employeer.role = "Huggy"
        
    return templates.TemplateResponse(
        request=request, name="pages/create-sunday.html", context={"employeer" : emp, "id": id, "phone": phone_assigned}
    )

@router.get("/sunday/edit/{id}", response_class=HTMLResponse)
async def edit_employeer(request: Request, id : str):
    team = weekend_dao.getById(id)
    employeers = [ {"id": e.id,"fullName": e.full_name,"team": e.team, "role": e.role} for e in employee_dao.getActivesFromTeam(team.on_duty_team)]
    employeers_signed  = employee_dao.getSundayAssignments(id)
    for employeer in employeers:


        for e_signed in employeers_signed:
            if employeer["fullName"] == e_signed["fullName"]:
                employeer["assigned"] = True
                employeer["period"] = e_signed["period"]



        if employeer["role"] == "phone":
            employeer["role"] = "Telefone"
        else:
            employeer["role"] = "Huggy"
        
    return templates.TemplateResponse(
        request=request, name="pages/edit-employeer.html", context={"employeer" : employeers, "id": id}
    )
    
@router.get("/sunday/{id}", response_class=HTMLResponse)
async def sundays(id : int,request: Request):
    diasFerias = defaultdict(list)
    semana = ["Segunda","Terça","Quarta","Quinta", "Sexta"]
    phone_assigned = weekend_dao.getCountPhoneWeekend(int(id))
    print(phone_assigned)
    data = weekend_dao.getDayoffsFromWeekend(int(id))
    data = sorted(data, key=lambda d: d['day'])
    for dt in data:
        try:
            today_day = date.fromisoformat(dt["day"]).weekday()
            str_day = semana[today_day]
            diasFerias[str_day].append([dt["fullName"].capitalize(), dt["team"]])
        except:
            print('error in date format')
    
    employeer = employee_dao.getSundayAssignments(int(id))
    
    for emp in employeer:
        if emp["role"] == "phone":
            emp["role"] = "Telefone"
        else:
            emp["role"] = "Huggy"

    status = batch_dao.getByWeekendId(int(id))
    saturday = date.fromisoformat(weekend_dao.getById(int(id)).saturday)
    date_sunday = saturday + timedelta(days=1)
    last_saturday = saturday - timedelta(weeks=1)
    last_week = q("select b.status from generation_batches b join weekends w  on w.id = b.weekend_id where w.saturday = %s", (last_saturday.isoformat(),) )
    if not last_week:
        last_week = "no_batch"
    else:
        last_week = last_week[0][0]

    return templates.TemplateResponse(
        request=request, name="pages/sunday-details.html",  context= {"id": id,"data": diasFerias ,"employeer": employeer, "days": date_sunday.day , "month" : date_sunday.month, "status": status["status"], "last_week" : last_week, "id_batch" : status["id"]}

    )
    
    
   


@router.get("/dayoffs/{id}", response_class=HTMLResponse)
async def dayoffs(request: Request, id : str):
    diasFerias = defaultdict(list)
    semana = ["Segunda","Terça","Quarta","Quinta", "Sexta"]

    data = weekend_dao.getDayoffsFromWeekend(int(id))
    data = sorted(data, key=lambda d: d['day'])

    for dt in data:
        try:
            today_day = date.fromisoformat(dt["day"]).weekday()
            str_day = semana[today_day]
            diasFerias[str_day].append([dt["fullName"].capitalize(), dt["team"]])
        except:
            print('error in date format')
    
    employeer = weekend_dao.getSundayAssignments(int(id))
    
    for emp in employeer:
        if emp["role"] == "phone":
            emp["role"] = "Telefone"
        else:
            emp["role"] = "Huggy"

    status = batch_dao.getByWeekendId(int(id))
    saturday = weekend_dao.getById(int(id)).saturday
    date_sunday = saturday + timedelta(days=1)
    last_saturday = saturday - timedelta(weeks=1)
    last_week = q("select b.status from generation_batches b join weekends w  on w.id = b.weekend_id where w.saturday = %s", (last_saturday.isoformat(),) )
    if not last_week:
        last_week = "no_batch"
    else:
        last_week = last_week[0][0]
    return templates.TemplateResponse(
        request=request, name="pages/edit-dayoffs.html", context={"data" : diasFerias}
    )






@router.get("/employees", response_class=HTMLResponse)
async def get_employees(request: Request):
    employees = employee_dao.getAll()
    for emp in employees:
        if emp.role == "phone":
            emp.role = "Telefone"
        else:
            emp.role = "Huggy"
    return templates.TemplateResponse(
        request=request, name="pages/employees/employees.html", context={"employees": employees}
    )

@router.get("/employees/create", response_class=HTMLResponse)
async def create_employee(request: Request):
    return templates.TemplateResponse(
        request=request, name="pages/employees/create-employee.html"
    )

@router.post("/employees/create", response_class=HTMLResponse)
async def create_employee_post(request: Request):
    form = await request.form()
    new_employee = employee.Employee()
    new_employee.full_name = form.get("full_name")
    new_employee.team = form.get("team")
    new_employee.role = form.get("role")
    new_employee.is_active = True
    employee_dao.create(new_employee)

   
    return RedirectResponse(url="/employees", status_code=303)

@router.get("/employees/edit/{id}", response_class=HTMLResponse)
async def edit_employee(request: Request, id : str):
    employee = employee_dao.getById(id)
    if employee.role == "phone":
        employee.role = "Telefone"
    else:
        employee.role = "Huggy"
    return templates.TemplateResponse(
        request=request, name="pages/employees/edit-employee.html", context={"employee" : employee}
    )

@router.post("/employees/edit/{id}", response_class=HTMLResponse)
async def edit_employee_post(request: Request, id : str):
    form = await request.form()
    emp = employee_dao.getById(id)
    emp.full_name = form.get("full_name")
    emp.team = form.get("team")
    emp.role = form.get("role")
    is_active_str = form.get("is_active")
    emp.is_active = True if is_active_str == "on" else False
    employee_dao.update(emp)

    return RedirectResponse(url="/employees", status_code=303)

@router.post("/employees/delete/{id}", response_class=HTMLResponse)
async def delete_employee_post(request: Request, id : str):
    employee_dao.delete(id)
    return RedirectResponse(url="/employees", status_code=303)


@router.get("/employees/status/{id}")
async def employee_status(request: Request, id : str):
    emp = employee_dao.isAssigned(id)
    return {"assigned": emp}

@router.post("/batch/delete/{weekend_id}", response_class=HTMLResponse)
async def delete_batch_post(request: Request, weekend_id : int):
    batch_dao.deleteFromWeekend(weekend_id)
    return RedirectResponse(url="/weekend", status_code=303)

@router.post("/assign/delete/{weekend_id}", response_class=HTMLResponse)
async def delete_batch_post(request: Request, weekend_id : int):

    weekend_dao.deleteSundayAssignments(weekend_id)
    return RedirectResponse(url="/weekend", status_code=303)

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):

    return templates.TemplateResponse(
        request=request, name="pages/login.html"
    )

@router.post("/login")
async def login_submit(request: Request):
    form = await request.json()
    username = form.get("username")
    password = form.get("password")
    from app.settings import settings
    USERNAME = settings.ADMIN
    PASSWORD = settings.ADMIN_PASSWORD
    if username != USERNAME or password != PASSWORD:
        return HTMLResponse(status_code=401, content="Credentials are incorrect")
    return encodeJWT()
    
