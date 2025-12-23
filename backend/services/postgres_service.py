from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config.settings import settings

engine = create_engine(settings.POSTGRES_DSN, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class PostgresService:
    def run_query(self, sql: str, params=None):
        with SessionLocal() as session:
            res = session.execute(text(sql), params or {})
            cols = res.keys()
            rows = [dict(zip(cols, row)) for row in res.fetchall()]
        return rows

postgres_service = PostgresService()
