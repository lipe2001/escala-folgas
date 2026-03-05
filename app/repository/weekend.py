


from ..db import q

class Weekend:

    
    def __init__(self, id: int, saturday: str, on_duty_team: str, status: str = None):
        self.id = id
        self.saturday = saturday
        self.on_duty_team = on_duty_team
        self.status = status

class WeekendDAO:

    def getById(self, id: int):
        query = q("select id, saturday::text, on_duty_team::text  from weekends where id = %s", (id,))
        if not query:
            return None
        r = query[0]
        return Weekend(r[0], r[1], r[2])
    def getLastWeekend(self):
        query = q("select saturday from weekends order by saturday desc limit 1")
        return {"saturday": query[0][0]} if query else None
    
    def deleteWeekend(self, weekend_id: int):
        q("delete from weekends where id = %s", (weekend_id,))
        return {"success": True}
    def deleteSundayAssignments(self, weekend_id: int):
        q("delete from sunday_assignments where weekend_id = %s", (weekend_id,))
        return {"success": True}
    def getCountPhoneWeekend(self, weekend_id: int):
        query = q("select count(distinct e.full_name) from employees e join dayoffs d on d.employee_id = e.id join generation_batches b on d.batch_id = b.id where e.role = 'phone' and b.weekend_id = %s", (weekend_id,))
        return query[0][0] if query else 0
    def listWeekends(self):
        rows = q("select w.id, w.saturday::text, w.on_duty_team::text, g.status from weekends w left join generation_batches g on g.weekend_id = w.id order by w.saturday desc")
        return [Weekend(r[0], r[1], r[2], r[3]) for r in rows]
    def getDayoffsFromWeekend(self, weekend_id: int):
        query = q("select distinct on (e.full_name) e.full_name, e.team, d.day::text   from dayoff_proposals d join employees e on d.employee_id = e.id join generation_batches g on d.batch_id = g.id where g.weekend_id = %s order by e.full_name, d.day", (weekend_id,))
        return [{"fullName": r[0], "team": r[1], "day": r[2]} for r in query]
