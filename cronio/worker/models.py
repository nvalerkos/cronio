from __future__ import absolute_import
### Database - SQLite
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy import Column, ForeignKey, Integer, String, LargeBinary
from sqlalchemy.dialects.sqlite import BLOB, BOOLEAN, CHAR, DATE, DATETIME, DECIMAL, FLOAT, INTEGER, NUMERIC, SMALLINT, TEXT, TIME, TIMESTAMP, VARCHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import datetime 

Base = declarative_base()
class Commands(Base):
	__tablename__ = 'command'
	pk = Column(INTEGER, nullable=False, primary_key=True)
	cmd_id = Column(VARCHAR(64), nullable=True)
	cmd = Column(BLOB,nullable=False)
	is_type = Column(VARCHAR(10), default='os', nullable=False)
	sender = Column(VARCHAR(64), default='sender1', nullable=False)
	created_date = Column(DATETIME,default=datetime.datetime.now, nullable=False)
	dependencies = Column(VARCHAR(320), default='', nullable=False)
	api_log = Column(VARCHAR(64), default='', nullable=False)

class CommandLog(Base):
	__tablename__ = 'command_log'
	pk = Column(INTEGER, nullable=False, primary_key=True)
	cmd_id = Column(VARCHAR(64), nullable=True)
	cmd = Column(BLOB,nullable=False)
	is_type = Column(VARCHAR(10), default='os', nullable=False)
	sender = Column(VARCHAR(64), default='sender1', nullable=False)
	executed_date = Column(DATETIME,default=datetime.datetime.now, nullable=False)
	dependencies = Column(VARCHAR(320), default='', nullable=False)
	api_log = Column(VARCHAR(64), default='', nullable=False)
	result_code = Column(INTEGER, nullable=False)

metadata = Base.metadata
engine = create_engine('sqlite:///croniodb',connect_args={'check_same_thread':False},poolclass=StaticPool) #http://docs.sqlalchemy.org/en/latest/dialects/sqlite.html#module-sqlalchemy.dialects.sqlite.pysqlite
from sqlalchemy.orm import sessionmaker
session = scoped_session(sessionmaker(autocommit=False,autoflush=False,bind=engine))