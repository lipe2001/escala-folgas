from re import S
import re
from fastapi import APIRouter, Depends, HTTPException
from ..deps import require_admin
from ..db import q, exec_sql
from ..schemas import WeekendCreate, SundayAssignmentsIn
from datetime import timedelta, date, datetime
from ..bot import bot
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/employees/team/{team}")
def get_employees_from_team(team : str,_ = Depends(require_admin)):
    query = q("select id, full_name, team, role from employees where team = %s", tuple(team))
    return [{"id" : r[0], "fullName" : r[1] ,"team": r[2], "role": r[3]} for r in query]    

@router.get("/employees")
def list_employees(_ = Depends(require_admin)):
    query = q("select id, full_name, team, role, is_active from employees")
    return [{"id" : r[0], "fullName" : r[1] ,"team": r[2], "role": r[3], "is_active": r[4]} for r in query]

@router.get("/employees/{id}")
def get_employee(id : int ,_ = Depends(require_admin)):
    query = q("select id, full_name, team, role, is_active from employees where id = %s", (id,))
    if not query:
        raise HTTPException(404, detail="Employee not found")
    return {"id" : query[0][0], "fullName" : query[0][1] ,"team": query[0][2], "role": query[0][3], "is_active": query[0][4]}
@router.get("/weekends/{id}")
def get_weekends(id : int ,_ = Depends(require_admin)):
    query = q("select * from weekends where id = %s", (id,))
    return {"id" : query[0][0], "saturday" : query[0][1] ,"team": query[0][2]}  

@router.post("/weekends")
def create_weekend(payload: WeekendCreate, _=Depends(require_admin)):
    now = datetime.strptime(payload.saturday, '%Y-%m-%d').date()
    if now.weekday() != 5:
        raise HTTPException(400, detail="The date is not a Saturday")
        return  
    rec = q("insert into weekends(saturday, on_duty_team) values (%s,%s) returning id",
            (payload.saturday, payload.on_duty_team))
    return {"id": rec[0][0]}





@router.get("/weekends")
def list_weekends(_=Depends(require_admin), from_: str | None = None, to: str | None = None):
    sql = "select w.id, w.saturday::text, w.on_duty_team::text, g.status from weekends w left join generation_batches g on g.weekend_id = w.id"
    params = []
    if from_ and to:
        sql += " where w.saturday between %s and %s"
        params = [from_, to]
    sql += " order by w.saturday desc"
    rows = q(sql, tuple(params))
    return [{"id": r[0], "saturday": r[1], "on_duty_team": r[2], "status": r[3]} for r in rows]


@router.get("/weekends/{weekend_id}/sunday-assignments")
def get_sunday_assignments(weekend_id: int, _=Depends(require_admin)):
    query = q ("select e.full_name , s.period, e.role from sunday_assignments s join employees e on s.employee_id = e.id where s.weekend_id = %s", (weekend_id,))
    return [{"fullName": r[0], "period": r[1], "role": r[2]} for r in query]


@router.get("/weekends/{weekend_id}/folgas")
def get_folgas_from_week(weekend_id: int, _=Depends(require_admin)):
    query = q("select distinct on (e.full_name) e.full_name, e.team, d.day::text   from dayoff_proposals d join employees e on d.employee_id = e.id join generation_batches g on d.batch_id = g.id where g.weekend_id = %s order by e.full_name, d.day", (weekend_id,))
    return [{"fullName": r[0], "team": r[1], "day": r[2]} for r in query]
    

@router.get("/batches/{weekend_id}/status")
def get_batch_status(weekend_id: int, _=Depends(require_admin)):
    query = q("select id, status from generation_batches where weekend_id = %s order by id desc limit 1", (weekend_id,))
    if not query:
        return {"id": None ,"status": "no_batch"}
    return {"id": query[0][0], "status" : query[0][1]}


@router.post("/weekends/{weekend_id}/sunday-assignments")
def set_sunday_assignments(weekend_id: int, payload: SundayAssignmentsIn, _=Depends(require_admin)):
    w = q("select saturday from weekends where id = %s", (weekend_id,))
    if not w:
        raise HTTPException(404, detail="weekend not found")
    saturday = w[0][0]
    sunday = saturday + timedelta(days=1)

    #exec_sql("delete from sunday_assignments where weekend_id = %s", (weekend_id,))

    for emp_id in payload.morning:
        exec_sql("insert into sunday_assignments(weekend_id, sunday, period, employee_id) values (%s,%s,'morning',%s)",
                 (weekend_id, sunday, emp_id))
    for emp_id in payload.afternoon:
        exec_sql("insert into sunday_assignments(weekend_id, sunday, period, employee_id) values (%s,%s,'afternoon',%s)",
                 (weekend_id, sunday, emp_id))

    return {"ok": True}



@router.put("/weekends/{weekend_id}/sunday-assignments")
def put_sunday_assignments(weekend_id: int, payload: SundayAssignmentsIn, _=Depends(require_admin)):
    w = q("select saturday from weekends where id = %s", (weekend_id,))
    if not w:
        raise HTTPException(404, detail="weekend not found")
    query = q("select status from generation_batches where weekend_id = %s ", (weekend_id,))
    if query and query[0][0] == "published":
        raise HTTPException(400, detail="Cannot modify sunday assignments for published batches")

    saturday = w[0][0]
    sunday = saturday + timedelta(days=1)

    exec_sql("delete from sunday_assignments where weekend_id = %s", (weekend_id,))
    for emp_id in payload.morning:
        exec_sql("insert into sunday_assignments(weekend_id, sunday, period, employee_id) values (%s,%s,'morning',%s)",
                 (weekend_id, sunday, emp_id))
    for emp_id in payload.afternoon:
        exec_sql("insert into sunday_assignments(weekend_id, sunday, period, employee_id) values (%s,%s,'afternoon',%s)",
                 (weekend_id, sunday, emp_id))

    return {"ok": True}



@router.post("/weekends/{weekend_id}/generate")
def generate(weekend_id: int, _=Depends(require_admin)):
    from ..services.generator import generate_batch
    batch_id = generate_batch(weekend_id)
    return {"batch_id": batch_id}

@router.get("/batches/{batch_id}")
def get_batch(batch_id: int, _=Depends(require_admin)):
    props = q(
        """
        select p.id, p.employee_id::text, e.full_name, e.role::text, p.day::text, p.reason
        from dayoff_proposals p join employees e on e.id = p.employee_id
        where p.batch_id = %s order by p.day, e.role, e.full_name
        """,
        (batch_id,)
    )
    return [
        {"id": r[0], "employee_id": r[1], "full_name": r[2], "role": r[3], "day": r[4], "reason": r[5]}
        for r in props
    ]

@router.post("/batches/{batch_id}/approve")
def approve_batch(batch_id: int, _=Depends(require_admin)):
    exec_sql("update generation_batches set status='approved', approved_at=now() where id=%s", (batch_id,))
    return {"ok": True}

@router.post("/batches/{batch_id}/publish")
async def publish_batch(batch_id: int, _=Depends(require_admin)):
    props = q("select employee_id, day from dayoff_proposals where batch_id = %s", (batch_id,))
    for emp_id, day in props:
        exec_sql("insert into dayoffs(employee_id, day, source, batch_id) values (%s,%s,'auto',%s)",
                 (emp_id, day, batch_id))
    exec_sql("update generation_batches set status='published', published_at=now() where id=%s", (batch_id,))
    id = q("select weekend_id from generation_batches where id = %s ", (batch_id,))
    await bot.send_folgas_by_day()
    await bot.send_week(id)


    return {"ok": True}

@router.get("/metrics/fairness")
def metrics_fairness(weeks: int = 13, end: str | None = None, _=Depends(require_admin)):
    if weeks <= 0 or weeks > 52:
        raise HTTPException(400, detail="weeks must be between 1 and 52")
    end_date = date.fromisoformat(end) if end else date.today()
    start_date = end_date - timedelta(weeks=weeks)

    rows = q(
        """
        with counts as (
          select e.id::text as employee_id, e.full_name, e.team::text as team, e.role::text as role,
                 %s::date as window_start, %s::date as window_end,
                 count(d.day) filter (where d.day between %s and %s) as total,
                 count(d.day) filter (where d.day between %s and %s and extract(dow from d.day)::int in (1,5)) as mon_fri
          from employees e
          left join dayoffs d on d.employee_id = e.id
          where e.is_active = true
          group by e.id, e.full_name, e.team, e.role
        )
        select employee_id, full_name, team, role, window_start::text, window_end::text,
               total, mon_fri,
               case when total=0 then 0::numeric else round(mon_fri::numeric/total,3) end as ratio_mon_fri,
               round(0.40 - (case when total=0 then 0::numeric else mon_fri::numeric/total end),3) as deficit_to_40
        from counts
        order by ratio_mon_fri asc, total desc, full_name
        """,
        (start_date, end_date, start_date, end_date, start_date, end_date)
    )

    return [
        {
            "employee_id": r[0],
            "full_name": r[1],
            "team": r[2],
            "role": r[3],
            "window_start": r[4],
            "window_end": r[5],
            "total_dayoffs": int(r[6] or 0),
            "mon_fri_dayoffs": int(r[7] or 0),
            "ratio_mon_fri": float(r[8]),
            "deficit_to_40": float(r[9])
        } for r in rows
    ]
