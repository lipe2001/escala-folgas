import logging

from psycopg_pool import ConnectionPool
from .settings import settings

logger = logging.getLogger(__name__)

pool = ConnectionPool(settings.DATABASE_URL, min_size=1, max_size=8, kwargs={"autocommit": True})


def q(sql: str, params: tuple | dict = ()):
    try:
        with pool.connection(timeout=2) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                try:
                    return cur.fetchall()
                except Exception:
                    return []
    except Exception as exc:
        logger.warning("Falha de conexão ao consultar banco: %s", exc)
        return []


def exec_sql(sql: str, params: tuple | dict = ()):
    try:
        with pool.connection(timeout=2) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
    except Exception as exc:
        logger.warning("Falha de conexão ao executar SQL: %s", exc)