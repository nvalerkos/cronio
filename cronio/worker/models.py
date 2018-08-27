from __future__ import absolute_import
### Database - SQLite
from sqlalchemy import create_engine, UniqueConstraint
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
	sender_id = Column(VARCHAR(64), default='sender_1', nullable=False)
	created_date = Column(DATETIME, default=datetime.datetime.now, nullable=False)
	dependencies = Column(VARCHAR(320), default='', nullable=False)
	api_log = Column(VARCHAR(64), default='', nullable=False)
	status = Column(VARCHAR(64), default='pending', nullable=False)
	__table_args__ = (UniqueConstraint('cmd_id', 'sender_id', name='uix_1'),)

class CommandDeps(Base):
	__tablename__ = 'command_deps'
	pk = Column(INTEGER, nullable=False, primary_key=True)
	sender_id = Column(VARCHAR(64), default='sender_1', nullable=False)
	worker_id = Column(VARCHAR(64), nullable=False)
	dep_cmd_id = Column(VARCHAR(64), nullable=True)
	resolved_result_code = Column(Integer, default=0, nullable=False)
	resolved_date = Column(DATETIME, nullable=True)
	to_run_result_code = Column(Integer, default=0, nullable=False)
	to_run_cmd_id = Column(VARCHAR(64), nullable=True)
	created_date = Column(DATETIME, default=datetime.datetime.now, nullable=False)
	resolved = Column(VARCHAR(10), default='No', nullable=False)
	ok_to_run = Column(BOOLEAN, default=False, nullable=False)
	__table_args__ = (UniqueConstraint('dep_cmd_id', 'worker_id', 'to_run_result_code','to_run_cmd_id', 'sender_id', name='uix_1'),)

class CommandLog(Base):
	__tablename__ = 'command_log'
	pk = Column(INTEGER, nullable=False, primary_key=True)
	cmd_id = Column(VARCHAR(64), nullable=True)
	cmd = Column(BLOB,nullable=False)
	is_type = Column(VARCHAR(10), default='os', nullable=False)
	sender_id = Column(VARCHAR(64), default='sender_1', nullable=False)
	executed_date = Column(DATETIME,default=datetime.datetime.now, nullable=False)
	dependencies = Column(VARCHAR(320), default='', nullable=False)
	api_log = Column(VARCHAR(64), default='', nullable=False)
	result_code = Column(INTEGER, nullable=False)


metadata = Base.metadata
engine = create_engine('sqlite:///croniodb',connect_args={'check_same_thread':False},poolclass=StaticPool) #http://docs.sqlalchemy.org/en/latest/dialects/sqlite.html#module-sqlalchemy.dialects.sqlite.pysqlite
from sqlalchemy.orm import sessionmaker
session = scoped_session(sessionmaker(autocommit=False,autoflush=False,bind=engine))