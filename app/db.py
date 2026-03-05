from psycopg_pool import ConnectionPool
from .settings import settings

pool = ConnectionPool(settings.DATABASE_URL, min_size=1, max_size=8, kwargs={"autocommit": True})

def q(sql: str, params: tuple | dict = ()):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            try:
                return cur.fetchall()
            except Exception:
                return []

def exec_sql(sql: str, params: tuple | dict = ()):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
