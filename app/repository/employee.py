from ..db import q

class Employee:
    def __init__(self, id: int = None, full_name: str = None, team: str = None, role: str =None, is_active: bool = None):
        self.id = id
        self.full_name = full_name
        self.team = team
        self.role = role
        self.is_active = is_active
    

class EmployeeDAO:

    def getEmployeesFromTeam(self, team: str):
        query = q("select id, full_name, team, role, is_active from employees where team = %s", (team,))
        return [Employee(r[0], r[1], r[2], r[3], r[4]) for r in query]
    def getActivesFromTeam(self, team : str):
        query = q("select id, full_name, team, role from employees where team = %s and is_active = 'true'", tuple(team))
        return [Employee(r[0],r[1],r[2],r[3] ) for r in query]      
    def isAssigned(self, employee_id: str):
        query = q("select count(*) from  dayoff_proposals d join employees e on d.employee_id = e.id join generation_batches g on g.id = d.batch_id where g.status <> 'published' and e.id = %s", (employee_id,))
        query_l = q("select count(*) from  sunday_assignments s join employees e on s.employee_id = e.id join generation_batches g on g.weekend_id = s.weekend_id where g.status <> 'published' and e.id = %s", (employee_id,))
        return query[0][0] > 0 or query_l[0][0] > 0
    def getSundayAssignments(self, weekend_id: int):
        query = q ("select e.full_name , s.period, e.role from sunday_assignments s join employees e on s.employee_id = e.id where s.weekend_id = %s", (weekend_id,))
        return [ {"fullName": r[0], "period": r[1], "role": r[2]} for r in query]
    def getAll(self):
        query = q("select id, full_name, team, role, is_active from employees")
        return [Employee(r[0], r[1], r[2], r[3], r[4]) for r in query]
    def getById(self, id: str):
        query = q("select id, full_name, team, role, is_active from employees where id = %s", (id,))
        if not query:
            return None
        r = query[0]
        return Employee(r[0], r[1], r[2], r[3], r[4])
    def create(self, employee: Employee):
        rec = q("insert into employees(full_name, team, role, is_active) values (%s, %s, %s, %s) returning id",
                (employee.full_name, employee.team, employee.role, employee.is_active))
        employee.id = rec[0][0]
        return employee
    def update(self, employee: Employee):
        q("update employees set full_name = %s, team = %s, role = %s, is_active = %s where id = %s",
          (employee.full_name, employee.team, employee.role, employee.is_active, employee.id))
        return employee
    def delete(self, id: str):
        q("delete from employees where id = %s", (id,))
        return {"success": True}
  
