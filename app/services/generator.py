from datetime import date, timedelta
from dateutil.parser import isoparse
from ..db import q, exec_sql

PREF_ORDER = [4, 0, 3, 1, 2]  # weekday(): 0=seg ... 6=dom

def to_date(s: str) -> date:
    return isoparse(s).date()

def load_ratio_segsex(employee_id: str, ref_day: date) -> float:
    start = ref_day - timedelta(weeks=13)
    rows = q(
        """
        select d.day from dayoffs d
        where d.employee_id = %s and d.day between %s and %s
        """,
        (employee_id, start, ref_day)
    )
    if not rows:
        return 0.0
    total = len(rows)
    mon_fri = 0
    for (d,) in rows:
        d0 = d if isinstance(d, date) else to_date(str(d))
        if d0.weekday() in (0, 4):
            mon_fri += 1
    return mon_fri / total if total else 0.0

def day_caps(snapshot, day: date):
    info = snapshot.get(day, {"total": 0, "phone": 0})
    return info["total"], info["phone"]

def bump(snapshot, day: date, role: str):
    d = snapshot.setdefault(day, {"total": 0, "phone": 0})
    d["total"] += 1
    if role == "phone":
        d["phone"] += 1

def choose_f1(role: str, employee_id: str, sunday: date, snapshot):
    week_start = sunday - timedelta(days=sunday.weekday())
    week_days = [week_start + timedelta(days=i) for i in range(0, 6)]
    ratio = load_ratio_segsex(employee_id, sunday)
    order = PREF_ORDER if ratio < 0.40 else [4, 0, 3, 1, 2]
    for idx in order:
        d = week_days[idx]
        total, phone = day_caps(snapshot, d)
        if total < 3 and not (role == "phone" and phone >= 1):
            return d
    for d in week_days:
        total, phone = day_caps(snapshot, d)
        if total < 3 and not (role == "phone" and phone >= 1):
            return d
    return None

def generate_batch(weekend_id: int) -> int:
    batch_id = q("insert into generation_batches(weekend_id) values(%s) returning id", (weekend_id,))[0][0]
    rows = q(
        """
        select sa.employee_id, e.role, w.saturday
        from sunday_assignments sa
        join weekends w on w.id = sa.weekend_id
        join employees e on e.id = sa.employee_id
        where sa.weekend_id = %s
        """,
        (weekend_id,)
    )
    if not rows:
        return batch_id

    saturday = rows[0][2]
    sunday = (saturday if isinstance(saturday, date) else to_date(str(saturday))) + timedelta(days=1)

    rows_exist = q(
        """
        select d.day, e.role from dayoffs d join employees e on e.id = d.employee_id
        where d.day between %s and %s
        """,
        (sunday - timedelta(days=7), sunday + timedelta(days=13))
    )
    snap = {}
    for day, role in rows_exist:
        d0 = day if isinstance(day, date) else to_date(str(day))
        bump(snap, d0, role)

    for emp_id, role, _ in rows:
        f1 = choose_f1(role, emp_id, sunday, snap)
        if f1 is None:
            continue
        bump(snap, f1, role)
        f2 = f1 + timedelta(days=7)
        total, phone = day_caps(snap, f2)
        if total >= 3 or (role == "phone" and phone >= 1):
            week_start = f2 - timedelta(days=f2.weekday())
            for i in range(0, 6):
                d = week_start + timedelta(days=i)
                t2, p2 = day_caps(snap, d)
                if t2 < 3 and not (role == "phone" and p2 >= 1):
                    f2 = d
                    break
        bump(snap, f2, role)
        exec_sql("insert into dayoff_proposals(batch_id, employee_id, day, reason) values (%s,%s,%s,%s)",
                 (batch_id, emp_id, f1, "auto:F1"))
        exec_sql("insert into dayoff_proposals(batch_id, employee_id, day, reason) values (%s,%s,%s,%s)",
                 (batch_id, emp_id, f2, "auto:F2"))

    return batch_id
