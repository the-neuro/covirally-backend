import databases
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base

from app.config import settings

db_options = settings.db_options

Base = declarative_base()

metadata = sqlalchemy.MetaData()
database = databases.Database(settings.database_url, **db_options)
