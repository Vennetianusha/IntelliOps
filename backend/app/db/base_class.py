from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Declarative Base class for SQLAlchemy ORM models.
    All database models inherit from this Base.
    """
    pass
