from __future__ import absolute_import
import time, sys, pprint, json, os, tempfile, datetime

#requirements.txt
import logging
import stomp
module_logger_worker = logging.getLogger('cronio_worker')

### Database - SQLite
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
 
engine = create_engine('sqlite:///croniodb',connect_args={'check_same_thread':False},poolclass=StaticPool) #http://docs.sqlalchemy.org/en/latest/dialects/sqlite.html#module-sqlalchemy.dialects.sqlite.pysqlite
from sqlalchemy.orm import sessionmaker
session = scoped_session(sessionmaker(autocommit=False,autoflush=False,bind=engine))

from .models import Base, Commands, CommandLog


class CronioWorker(object):
	def __init__(self, settings = {}):
		#Set Default Values
		self.assignDefaultValues()
		settingKeys = ['CRONIO_AMQP_USERNAME','CRONIO_AMQP_PASSWORD','CRONIO_EXCHANGE_LOG_INFO','CRONIO_EXCHANGE_LOG_ERROR','CRONIO_WORKER_QUEUE','CRONIO_AMQP_HOST','CRONIO_AMQP_VHOST','CRONIO_AMQP_PORT','CRONIO_AMQP_USE_SSL','CRONIO_LOGGER_LEVEL','CRONIO_LOGGER_FORMATTER','CRONIO_ENGINE_RUNTIME_SECONDS','CRONIO_TEST_IS_NOT_ON','CRONIO_WORKER_WORK_DIR','CRONIO_WORKER_ID','REFRESH_DATABASE']
		for key in settingKeys:
			if key in settings:
				setattr(self, key, settings[key])
			
		self.logger_worker = logging.getLogger('cronio_worker')
		self.logger_worker.setLevel(self.CRONIO_LOGGER_LEVEL)
		loggerSH = logging.StreamHandler()
		formatter = logging.Formatter(self.CRONIO_LOGGER_FORMATTER)
		loggerSH.setFormatter(formatter)
		
		if self.REFRESH_DATABASE:
			Base.metadata.drop_all(engine)
			session.commit()

		Base.metadata.create_all(engine)
		session.commit()

		self.logger_worker.addHandler(loggerSH)
		self.cronio_worker_listener = self.CronioWorkerListener(self)
		if self.CRONIO_TEST_IS_NOT_ON:
			self.initConnectWorkerSTOMP()

	class CronioWorkerListener(stomp.ConnectionListener):
		def __init__(self, parent):
			self.parent = parent

		def on_error(self, headers, message):
			self.parent.logger_worker.debug('Cronio Worker Listener received an error "%s"' % message)

		def on_message(self, headers, message):
			header_message_id = headers['message-id']
			
			self.parent.conn.ack(header_message_id,self.parent.CRONIO_WORKER_ID)
			message_obj = json.loads(message)
			cmd_id = False

			for req in ['cmd','type','cmd_id','api_log','sender', 'dependencies']:
				if req not in message_obj:
					self.parent.logger_worker.critical('Error - one or many required params are missing... : message-id: %s ' % str(header_message_id))
					return False

			# These are the passed params in the message, all of them are required, some might be null, still the key must exist in json.
			cmd = message_obj['cmd']
			is_type = message_obj['type']
			cmd_id = message_obj['cmd_id'] 
			api_log = message_obj['api_log']
			sender = message_obj['sender']
			dependencies = message_obj['dependencies']
			
			self.parent.sendAPIInform({'type':'info','status':'received','cmd_id': cmd_id, 'message_id':header_message_id, 'message_at': str(datetime.datetime.now())},api_log)

			if 'cmd' in message_obj and 'type' in message_obj:
				self.parent.logger_worker.debug('New Message Job %s' % str(cmd))
				if message_obj['type'] == 'operation' and 'cmd' in message_obj:
					if cmd == 'cleardb':
						self.parent.clearDatabase()
						self.parent.sendAPILog(0,{'out':'DB Cleared','error':'','exception':''}, cmd, api_log)
					else:
						self.parent.sendAPILog(10002,{'out':'','error':'Invalid Operation','exception':''}, cmd, api_log)
						self.parent.logger_worker.debug('Error - Invalid operation cmd %s - message-id: %s ' % (cmd,str(header_message_id)))
			

			

			# Check Dependencies inside the add command to db
			commandAddedPK = self.parent.addCommandToDB(cmd_id, cmd, is_type, sender, dependencies, api_log)
			self.parent.logger_worker.debug('Worker removed "%s" from queue' % header_message_id)

			if not commandAddedPK:
				# Will not process command if dependency check fails
				self.parent.logger_worker.debug('Worker will not process "%s" dependency_check_failed to execute (one or more.)' % cmd_id)
				self.parent.sendAPILog(10001,{'out':'','error':'Dependency Failed','exception':''}, cmd_id, api_log)
				self.parent.sendLog({'log':'', 'error': 'Dependency Failed' },cmd_id)
			
			elif message_obj['type'] == "python":
				# python cmd

				if "\n" in message_obj['cmd']:
					# this contains multiple commands, will use the os command to execute the temp python file that will be created.
					tmpfilepath = self.parent.writeToTemp(message_obj['cmd'])
					
					# TODO - needs to get the executable of python
					self.parent.logger_worker.debug('Executing with Python2.7 "%s"' % tmpfilepath)
					self.parent.ifOSRun(["/usr/bin/python2.7",tmpfilepath], cmd_id, message_obj)
					
					self.parent.logger_worker.debug('Removing file "%s"' % tmpfilepath)
					# remove the tmp file if you want to, if not comment it out
					os.remove(tmpfilepath)
				else:
					self.parent.ifPythonRun(message_obj['cmd'], cmd_id, message_obj)
				
				# Remove the command from DB and add it to log
				self.parent.removeCommandFromDB(commandAddedPK)

			elif message_obj['type'] == "os":

				# os cmd
				self.parent.logger_worker.debug('Executing commands "%s"' % message_obj['cmd'])
				if " " in message_obj['cmd']:
					cmds = message_obj['cmd'].split(" ")
				else:
					cmds = [message_obj['cmd']]
				self.parent.ifOSRun(cmds, cmd_id, message_obj)
				# Remove the command from DB and add it to log
				self.parent.removeCommandFromDB(commandAddedPK)



	def assignDefaultValues(self):
		self.CRONIO_AMQP_USERNAME =  "worker1"
		self.CRONIO_AMQP_PASSWORD =  "somepass"
		# By default, viewer logs are disabled in messages.
		self.CRONIO_EXCHANGE_LOG_INFO =  False#"cronio_log_info"
		self.CRONIO_EXCHANGE_LOG_ERROR =  False#"cronio_log_error"
		self.CRONIO_WORKER_QUEUE =  "cronio_queue"
		self.CRONIO_AMQP_HOST =  'localhost'
		self.CRONIO_AMQP_VHOST =  '/'
		self.CRONIO_AMQP_PORT =  61613
		self.CRONIO_AMQP_USE_SSL =  False
		self.CRONIO_LOGGER_LEVEL = logging.INFO
		self.CRONIO_LOGGER_FORMATTER = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
		self.CRONIO_ENGINE_RUNTIME_SECONDS = 60
		self.CRONIO_TEST_IS_NOT_ON = True
		self.CRONIO_WORKER_WORK_DIR = os.getcwd()
		self.CRONIO_WORKER_ID = 'worker1'
		# Enable this in your worker to refresh on each start
		self.REFRESH_DATABASE = False

	def initConnectWorkerSTOMP(self):
		self.conn = stomp.Connection(host_and_ports=[(self.CRONIO_AMQP_HOST, self.CRONIO_AMQP_PORT)],use_ssl=self.CRONIO_AMQP_USE_SSL,vhost=self.CRONIO_AMQP_VHOST)
		self.conn.set_listener('', self.cronio_worker_listener)
		self.conn.start()
		try:
			self.conn.connect(self.CRONIO_AMQP_USERNAME, self.CRONIO_AMQP_PASSWORD, wait=True)
		except Exception as e:
			self.logger_worker.critical('Failed to connect to STOMP "%s"' % str(e))
			raise e
		# ack=auto when received removes it from queue
		# ack='client' make it ack only when told to
		self.conn.subscribe(destination=self.CRONIO_WORKER_QUEUE, id=self.CRONIO_WORKER_ID, ack='client')

		# Run for 60 Seconds and stop, can be used to be called in crontab.
		time.sleep(self.CRONIO_ENGINE_RUNTIME_SECONDS)
		self.conn.disconnect()

	def addCommandToDB(self, cmd_id, cmd, is_type, sender, dependencies, api_log):
		pk = False
		pprint.pprint(dependencies)
		if dependencies is None:		
			commandNew = Commands(cmd_id=cmd_id,cmd=cmd,is_type=is_type, sender=sender, dependencies=json.dumps(dependencies), api_log=api_log)
			session.add(commandNew)
			session.commit()
			pk = commandNew.pk
		elif self.checkDependenciesOK(cmd_id, cmd, is_type, sender, dependencies, api_log):
			commandNew = Commands(cmd_id=cmd_id,cmd=cmd,is_type=is_type, sender=sender, dependencies=json.dumps(dependencies), api_log=api_log)
			session.add(commandNew)
			session.commit()
			pk = commandNew.pk
		else:
			return False
		return pk

	def checkDependenciesOK(self, cmd_id, cmd, is_type, sender, dependencies, api_log):
		dependency_check_failed = False
		for dependency_cmd_id in dependencies:

			dependencyFound = session.query(CommandLog).filter_by(cmd_id=dependency_cmd_id).first()
			if dependencyFound:
				if dependencyFound.result_code != 0:
					dependency_check_failed = True
					break
			else:
				dependency_check_failed = True
				break
		
		if dependency_check_failed:
			commandLogNew = CommandLog(cmd_id=cmd_id, cmd=json.dumps(cmd),is_type=is_type, sender=sender, dependencies=json.dumps(dependencies), result_code=10001, api_log=api_log)
			session.add(commandLogNew)
			session.commit()

		return not dependency_check_failed


	def removeCommandFromDB(self, pk):
		commandFound = session.query(Commands).filter_by(pk=pk).first()
		if commandFound:
			session.delete(commandFound)
			session.commit()

	def clearDatabase(self):
		print "Clear Database"
		Base.metadata.drop_all(engine)
		session.commit()
		Base.metadata.create_all(engine)
		session.commit()

	def ifOSRun(self, cmd, cmd_id, job_message):
		from subprocess import Popen, PIPE
		ExceptionError = ""
		OUT, ERROR = "",""
		result_code = 0
		try:
			self.logger_worker.debug('OS RUN command: %s' % str(cmd))
			p = Popen(cmd, stdout=PIPE, stderr=PIPE)
			OUT, ERROR = p.communicate()
			result_code = p.returncode
			self.logger_worker.debug(' Return Code: %s' % str(result_code))
		except Exception as e:
			self.logger_worker.debug(' Exception: %s' % str(e))
			ExceptionError = e
			if result_code == 0:
				result_code = 1

		self.logger_worker.debug(' Log Will Send Message:')	
		self.logger_worker.debug('  OUT: %s' % OUT)
		if ERROR != "" or ExceptionError != "":
			self.logger_worker.debug('  ERROR: %s'% str(ERROR+str(ExceptionError)))
		if self.CRONIO_TEST_IS_NOT_ON:
			self.sendAPILog(result_code,{'out':OUT,'error':str(ERROR),'exception':str(ExceptionError)},cmd_id, job_message['api_log'])
			self.addToCommandLog(cmd_id, cmd, job_message['type'], job_message['sender'], job_message['dependencies'], result_code, job_message['api_log'])
			self.sendLog({'log':OUT, 'error': ERROR+str(ExceptionError) },cmd_id)
		return True

	def addToCommandLog(self, cmd_id, cmd, is_type, sender, dependencies, result_code, api_log):
		commandLogNew = CommandLog(cmd_id=cmd_id, cmd=json.dumps(cmd),is_type=is_type, sender=sender, dependencies=json.dumps(dependencies), result_code=result_code, api_log=api_log)
		session.add(commandLogNew)
		session.commit()
		
	def writeToTemp(self, cmds):
		# Handle opening the file yourself. This makes clean-up
		# more complex as you must watch out for exceptions
		fd, path = tempfile.mkstemp()
		with os.fdopen(fd, 'w') as tmp:
			# do stuff with temp file
			tmp.write(cmds)
			tmp.close()
		self.logger_worker.debug('Return Temp Path of file %s',path)
		return path



	def ifPythonRun(self, cmd, cmd_id, job_message):
		import StringIO
		ExceptionError = ""
		result_code = 0
		# create file-like string to capture output
		codeOut = StringIO.StringIO()
		codeErr = StringIO.StringIO()
		
		# capture output and errors
		sys.stdout = codeOut
		sys.stderr = codeErr
		ExceptionError = u""
		try:
			os.chdir(self.CRONIO_WORKER_WORK_DIR)
			self.logger_worker.debug('PYTHON RUN command: %s'%str(cmd))
			exec cmd
		except Exception as e:
			raise e
			self.logger_worker.debug(' Exception: %s'%str(e))
			ExceptionError = str(e)
			result_code = 1
		finally:
			sys.stdout = sys.__stdout__
			sys.stderr = sys.__stderr__

		ERROR = u""+codeErr.getvalue()
		OUT = u""+codeOut.getvalue()
		codeOut.close()
		codeErr.close()

		self.logger_worker.debug(' Log Will Send Message:')	
		self.logger_worker.debug('  OUT: %s'%OUT)
		if ERROR != "" or ExceptionError != "":
			self.logger_worker.debug('  ERROR: %s'%str(ERROR+str(ExceptionError)))
		if self.CRONIO_TEST_IS_NOT_ON:
			self.sendAPILog(result_code,{'out':OUT,'error':ERROR,'exception':ExceptionError},cmd_id, job_message['api_log'])
			self.addToCommandLog(cmd_id, cmd, job_message['type'], job_message['sender'], job_message['dependencies'], result_code, job_message['api_log'])
			self.sendLog({'log':OUT, 'error': ERROR+str(ExceptionError) },cmd_id)
		return True

	def sendAPILog(self, result, info, cmd_id, api_log):
		api_message = {}
		api_message['cmd_id'] = cmd_id
		api_message['result'] = result
		api_message['info'] = info
		api_message['message_at'] = str(datetime.datetime.now())
		api_message['type'] = 'job'
		api_message['worker_id'] = self.CRONIO_WORKER_ID
		if self.CRONIO_TEST_IS_NOT_ON:
			pprint.pprint(api_message)
			self.conn.send(body=json.dumps(api_message), destination=api_log, vhost=self.CRONIO_AMQP_VHOST)

	def sendAPIInform(self, info, api_log):
		api_message = info
		api_message['worker_id'] = self.CRONIO_WORKER_ID
		if self.CRONIO_TEST_IS_NOT_ON:
			self.conn.send(body=json.dumps(api_message), destination=api_log, vhost=self.CRONIO_AMQP_VHOST)


	def sendLog(self, log, cmd_id):

		out_log = {'log': log['log'],'error' : False,'worker_id': self.CRONIO_WORKER_ID,'cmd_id': cmd_id}
		if log['error'] != '':
			out_log['error'] = True
			out_error = {'log': log['error'],'worker_id': self.CRONIO_WORKER_ID,'cmd_id': cmd_id}
			if self.CRONIO_TEST_IS_NOT_ON and self.CRONIO_EXCHANGE_LOG_ERROR:
				self.logger_worker.debug('Sending Error Message to %s with vhost %s'% (self.CRONIO_EXCHANGE_LOG_ERROR,self.CRONIO_AMQP_VHOST))
				self.logger_worker.debug(' Error Message: %s'% json.dumps(out_error))
				self.conn.send(body=json.dumps(out_error), destination=self.CRONIO_EXCHANGE_LOG_ERROR,vhost=self.CRONIO_AMQP_VHOST)
		
		if self.CRONIO_TEST_IS_NOT_ON and self.CRONIO_EXCHANGE_LOG_INFO:
			self.logger_worker.debug('Sending Log Message to %s with vhost %s'% (self.CRONIO_EXCHANGE_LOG_INFO,self.CRONIO_AMQP_VHOST))
			self.logger_worker.debug(' Log Message: %s'%json.dumps(out_log))
			self.conn.send(body=json.dumps(out_log), destination=self.CRONIO_EXCHANGE_LOG_INFO,vhost=self.CRONIO_AMQP_VHOST)