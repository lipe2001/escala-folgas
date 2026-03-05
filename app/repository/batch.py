from ..db import q
class Batch:
    def __init__(self, id: int = None, status: str = None, created_at: str = None):
        self.id = id
        self.status = status
        self.created_at = created_at

class BatchDAO:
    def deleteFromWeekend(self, weekend_id: int):
        q("delete from generation_batches where weekend_id = %s", (weekend_id,))
        return {"success": True}
    def getByWeekendId(self, weekend_id: int):
        query = q("select id, status from generation_batches where weekend_id = %s order by id desc limit 1", (weekend_id,))
        if not query:
            return {"id": None ,"status": "no_batch"}
        return {"id": query[0][0], "status" : query[0][1]}