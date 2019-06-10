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

"""
Commands' log of executed commands
"""
class CommandLog(Base):
	__tablename__ = 'command_log'
	pk = Column(INTEGER, nullable=False, primary_key=True)
	sender_id = Column(VARCHAR(64), default='sender_1', nullable=False)
	cmd_id = Column(VARCHAR(64), nullable=True)
	cmd = Column(BLOB,nullable=False)
	is_type = Column(VARCHAR(10), default='os', nullable=False)
	executed_date = Column(DATETIME,default=datetime.datetime.now, nullable=False)
	does_depend_on = Column(BOOLEAN, default=False, nullable=False)
	api_log = Column(VARCHAR(64), default='', nullable=False)
	status = Column(VARCHAR(64), default='Completed', nullable=False)
	"""
	Possible status values:
		Completed - Default
		Error
		Failed Depends on Condition
	"""
	result_code = Column(INTEGER, nullable=False)


"""
Commands and their dependencies if any
"""
class Commands(Base):
	__tablename__ = 'command'
	pk = Column(INTEGER, nullable=False, primary_key=True)
	cmd_id = Column(VARCHAR(64), nullable=True)
	cmd = Column(BLOB,nullable=False)
	is_type = Column(VARCHAR(10), default='os', nullable=False)
	sender_id = Column(VARCHAR(64), default='sender_1', nullable=False)
	created_date = Column(DATETIME, default=datetime.datetime.now, nullable=False)
	does_depend_on = Column(BOOLEAN, default=False, nullable=False)
	api_log = Column(VARCHAR(64), default='', nullable=False)
	status = Column(VARCHAR(64), default='Pending', nullable=False)
	"""
	Possible status values:
		Pending - Default
		Running
		Error
	"""
	__table_args__ = (UniqueConstraint('cmd_id', 'sender_id', name='command_uix_1'),)


"""
Own Commands that our commands depend on from Other Workers/Own.
"""
class OwnCommandsThatDependOn(Base):
	__tablename__ = 'own_commands_depend_on'
	pk = Column(INTEGER, nullable=False, primary_key=True)
	sender_id = Column(VARCHAR(64), default='sender_1', nullable=False)
	depends_on_worker_id = Column(VARCHAR(64), nullable=False)
	depends_on_cmd_id = Column(VARCHAR(64), nullable=True)
	depends_on_result_code = Column(Integer, default=0, nullable=False)
	run_cmd_id = Column(VARCHAR(64), nullable=True)
	created_date = Column(DATETIME, default=datetime.datetime.now, nullable=False)
	status = Column(VARCHAR(10), default='Waiting', nullable=False)
	"""
	Possible status values:
		Waiting - Default
		Fail
		OK
	"""
	"""
	Below are the resulted data which when we receive word that the depends_on_cmd_id is executed, after we check the result code received
	with what we have on our record is the same, then we execute it.
	"""
	resulted_result_code = Column(Integer, default=0, nullable=False)
	resulted_datetime = Column(DATETIME, nullable=True)
	__table_args__ = (UniqueConstraint('sender_id', 'depends_on_worker_id', 'depends_on_cmd_id','depends_on_result_code', 'run_cmd_id', name='own_commands_depend_on_uix_1'),)


"""
Own Commands That Other Workers Depend On
( Other workers will not execute their commands unless this worker sends them result)
"""
class OwnCommandsThatOtherWorkersDependOn(Base):
	__tablename__ = 'own_commands_other_workers_depend_on'
	pk = Column(INTEGER, nullable=False, primary_key=True)
	sender_id = Column(VARCHAR(64), default='sender_1', nullable=False)
	worker_id = Column(VARCHAR(64), nullable=False)
	cmd_id = Column(VARCHAR(64), nullable=True)
	created_date = Column(DATETIME, default=datetime.datetime.now, nullable=False)
	"""
	Below are the resulted data which are send to the above worker_id
	"""
	result_sent = Column(BOOLEAN, default=False, nullable=False)
	result_sent_datetime = Column(DATETIME, nullable=True)
	result_code = Column(Integer, default=None, nullable=True)
	__table_args__ = (UniqueConstraint('sender_id', 'worker_id', 'cmd_id', name='own_commands_other_workers_depend_on_uix_1'),)



metadata = Base.metadata
engine = create_engine('sqlite:///croniodb',connect_args={'check_same_thread':False},poolclass=StaticPool) #http://docs.sqlalchemy.org/en/latest/dialects/sqlite.html#module-sqlalchemy.dialects.sqlite.pysqlite
from sqlalchemy.orm import sessionmaker
session = scoped_session(sessionmaker(autocommit=False,autoflush=False,bind=engine))