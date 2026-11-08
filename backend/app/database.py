from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Adjust database URL if necessary for SQLAlchemy (e.g. postgres:// -> postgresql://)
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine_kwargs = {}
if db_url.startswith("postgresql"):
    # Neon cloud database connection optimizations:
    # pool_pre_ping checks if connection is still alive before reusing it.
    # pool_recycle refreshes connections every 3 minutes to prevent stale pooler disconnects.
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 180
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 5
    engine_kwargs["pool_timeout"] = 15
    engine_kwargs["connect_args"] = {
        "connect_timeout": 10,
        "application_name": "sanparrilla_fastapi",
        "options": "-c statement_timeout=15000 -c idle_in_transaction_session_timeout=15000"
    }

# Create database engine
engine = create_engine(db_url, **engine_kwargs)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            db.rollback()
        except Exception:
            pass
        db.close()
