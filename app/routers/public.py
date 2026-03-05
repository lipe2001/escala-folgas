from fastapi import APIRouter, Response
from ..db import q
from datetime import date, datetime, timedelta
import uuid

router = APIRouter(prefix="/public", tags=["public"])

@router.get("/folgas")
def list_folgas(start: str, end: str):
    rows = q(
        """
        select d.day::text, e.id::text as employee_id, e.full_name, e.team::text, e.role::text
        from dayoffs d join employees e on e.id = d.employee_id
        where d.day between %s and %s
        order by d.day, e.role, e.full_name
        """,
        (start, end)
    )
    return [
        {"day": r[0], "employee_id": r[1], "full_name": r[2], "team": r[3], "role": r[4]}
        for r in rows
    ]
    

@router.get("/folgas/week")
def folgas_week(position: int):
    
    now = date.today()
    first = now - timedelta(days=now.weekday()) + timedelta(weeks=int(position))
    last = first + timedelta(days=4)
    return list_folgas(first, last) 

@router.get("/folgas.ics")
def folgas_ics(start: str, end: str, team: str | None = None, role: str | None = None):
    sql = (
        "select d.day::date, e.full_name, e.team::text, e.role::text "
        "from dayoffs d join employees e on e.id = d.employee_id "
        "where d.day between %s and %s"
    )
    params = [start, end]
    if team:
        sql += " and e.team = %s"; params.append(team)
    if role:
        sql += " and e.role = %s"; params.append(role)
    sql += " order by d.day, e.role, e.full_name"

    rows = q(sql, tuple(params))

    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

    now_utc = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Micks NOC//Escalas//PT-BR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "NAME:Folgas NOC",
        "X-WR-CALNAME:Folgas NOC",
        "X-WR-TIMEZONE:America/Bahia",
    ]

    for day, full_name, team_v, role_v in rows:
        dtstart = day.strftime('%Y%m%d')
        dtend = (day + timedelta(days=1)).strftime('%Y%m%d')
        uid = f"{uuid.uuid4()}@escalas-noc"
        summary = f"Folga — {full_name}"
        desc = f"Equipe: {team_v}\nFunção: {role_v}"
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now_utc}",
            f"DTSTART;VALUE=DATE:{dtstart}",
            f"DTEND;VALUE=DATE:{dtend}",
            f"SUMMARY:{esc(summary)}",
            f"DESCRIPTION:{esc(desc)}",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")
    body = "\r\n".join(lines) + "\r\n"
    return Response(content=body, media_type="text/calendar; charset=utf-8")
