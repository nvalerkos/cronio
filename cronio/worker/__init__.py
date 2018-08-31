from __future__ import absolute_import
import time, sys, pprint, json, os, tempfile, datetime

#requirements.txt
import logging
import stomp
module_logger_worker = logging.getLogger("cronio_worker")

### Database - SQLite
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from sqlalchemy.orm import sessionmaker

from .models import Base, Commands, CommandLog, CommandDeps
from ..utils import CronioUtils

class CronioWorker(object):
	def __init__(self, settings = {}):
		#Set Default Values
		self.cronio_utils = CronioUtils()
		self.assignDefaultValues()
		settingKeys = ["CRONIO_AMQP_USERNAME","CRONIO_AMQP_PASSWORD","CRONIO_EXCHANGE_LOG_INFO","CRONIO_EXCHANGE_LOG_ERROR","CRONIO_AMQP_HOST","CRONIO_AMQP_VHOST","CRONIO_AMQP_PORT","CRONIO_AMQP_USE_SSL","CRONIO_LOGGER_LEVEL","CRONIO_LOGGER_FORMATTER","CRONIO_ENGINE_RUNTIME_SECONDS","CRONIO_TEST_IS_NOT_ON","CRONIO_WORKER_WORK_DIR","CRONIO_WORKER_ID","CRONIO_WORKER_PREFIX","CRONIO_WORKER_QUEUE","REFRESH_DATABASE"]
		change_in_queue = False
		ignore_change_in_queue = False
		for key in settingKeys:
			if key in settings:
				setattr(self, key, settings[key])
				if key in ["CRONIO_WORKER_PREFIX", "CRONIO_WORKER_ID"]:
					change_in_queue = True
				if key == "CRONIO_WORKER_QUEUE":
					ignore_change_in_queue = True


		if change_in_queue and not ignore_change_in_queue:
			self.CRONIO_WORKER_QUEUE = self.CRONIO_WORKER_PREFIX + self.CRONIO_WORKER_ID

		self.CRONIO_WORKER_DEPENDENCY_OWN = self.CRONIO_WORKER_DEPENDENCY_PREFIX + self.CRONIO_WORKER_ID

		self.logger_worker = logging.getLogger("cronio_worker")
		self.logger_worker.setLevel(self.CRONIO_LOGGER_LEVEL)
		loggerSH = logging.StreamHandler()
		formatter = logging.Formatter(self.CRONIO_LOGGER_FORMATTER)
		loggerSH.setFormatter(formatter)

		self.engine = create_engine("sqlite:///croniodb_"+self.CRONIO_WORKER_ID+".sqlite",connect_args={"check_same_thread":False},poolclass=StaticPool) #http://docs.sqlalchemy.org/en/latest/dialects/sqlite.html#module-sqlalchemy.dialects.sqlite.pysqlite
		self.session = scoped_session(sessionmaker(autocommit=False,autoflush=False,bind=self.engine))

		if self.REFRESH_DATABASE:
			Base.metadata.drop_all(self.engine)
			self.session.commit()

		Base.metadata.create_all(self.engine)
		self.session.commit()

		self.logger_worker.addHandler(loggerSH)
		self.cronio_worker_listener = self.CronioWorkerListener(self)
		if self.CRONIO_TEST_IS_NOT_ON:
			self.initConnectWorkerSTOMP()



	class CronioWorkerListener(stomp.ConnectionListener):
		def __init__(self, parent):
			self.parent = parent

		def on_error(self, headers, message):
			self.parent.logger_worker.critical("Cronio Worker Listener received an error \"%s\"" % message)

		def on_message(self, headers, message):
				header_message_id = headers["message-id"]
			# try:				
				
				self.parent.conn.ack(header_message_id, self.parent.CRONIO_WORKER_ID)
				message_obj = json.loads(message)
				cmd_id = False

				for req in ["cmd","type","cmd_id","api_log","sender_id"]:
					if req not in message_obj:
						self.parent.logger_worker.critical("Error - one or many required params are missing... : message-id: %s " % str(header_message_id))
						return False

				# These are the passed params in the message, all of them are required, some might be null, still the key must exist in json.
				cmd = message_obj["cmd"]
				is_type = message_obj["type"]
				cmd_id = message_obj["cmd_id"] 
				api_log = message_obj["api_log"]
				sender_id = message_obj["sender_id"]
				if "dependencies" in message_obj:
					dependencies = message_obj["dependencies"]
				else:
					dependencies = None
				
				self.parent.sendAPIInform({"type":"info","status":"received","cmd_id": cmd_id, "message_id":header_message_id, "message_at": str(datetime.datetime.now())},api_log)					
				self.parent.logger_worker.debug("New Message Job %s" % str(cmd))
				
				if message_obj["type"] == "operation" and "cmd" in message_obj:
					if cmd == "cleardb":
						self.parent.clearDatabase()
						self.parent.logger_worker.debug("Clearing Database")
						self.parent.sendAPILog(0,{"out":"DB Cleared","error":"","exception":""}, cmd, api_log)
					elif cmd == "inform_dependency_worker" and headers["destination"] == "/queue/"+self.parent.CRONIO_WORKER_DEPENDENCY_OWN:

						self.parent.logger_worker.debug("inform_dependency_worker cmd_id: %s  worker_id: %s" % (str(cmd_id), str(message_obj['worker_id'])))
						self.parent.sendDependencyResultToWorker(message_obj, api_log)
					elif cmd == "dependency_result" and headers["destination"] == "/queue/"+self.parent.CRONIO_WORKER_DEPENDENCY_OWN:
						self.parent.logger_worker.debug("Received Dependency Result cmd_id: %s  worker_id: %s" % (str(cmd_id), str(message_obj['worker_id'])))
						self.parent.dependencyResolved(cmd_id, message_obj['result_code'], message_obj['worker_id'], sender_id)
						# TODO Add this to the db
					else:
						# TODO ERROR Documentation 10002
						self.parent.sendAPILog(10002,{"out":"","error":"Invalid Operation","exception":""}, cmd, api_log)
						self.parent.logger_worker.debug("Error - Invalid operation cmd %s - message-id: %s - header destination: %s " % (cmd,str(header_message_id), headers["destination"]))
				else:
					self.parent.logger_worker.debug("Worker removed \"%s\" from queue" % header_message_id)
					commandAddedPK = self.parent.addCommandAndDependiesOfOtherWorkersToDB(cmd_id, cmd, is_type, sender_id, dependencies, api_log)
					self.parent.checkWorkersDependenciesRunIfOK(cmd_id)
# Disabled currently using the def checkWorkersDependenciesRunIfOK the below commented out should be removed.
					# if dependeciesNotOK:
					# 	# Will not process command if dependency check fails
					# 	self.parent.logger_worker.debug("Worker will not process \"%s\" dependency_check_failed to execute (one or more.)" % cmd_id)
					# 	# TODO ERROR Documentation 10001
					# 	self.parent.sendAPILog(10001,{"out":"","error":"Dependency Failed","exception":""}, cmd_id, api_log)
					# 	self.parent.sendLog({"log":"", "error": "Dependency Failed" },cmd_id)
					
					# elif message_obj["type"] == "python":
					# 	# python cmd

					# 	if "\n" in message_obj["cmd"]:
					# 		# this contains multiple commands, will use the os command to execute the temp python file that will be created.
					# 		tmpfilepath = self.parent.writeToTemp(message_obj["cmd"])
							
					# 		# TODO - needs to get the executable of python
					# 		self.parent.logger_worker.debug("Executing with Python2.7 \"%s\"" % tmpfilepath)
					# 		self.parent.ifOSRun(["/usr/bin/python2.7",tmpfilepath], cmd_id, message_obj)
							
					# 		self.parent.logger_worker.debug("Removing file \"%s\"" % tmpfilepath)
					# 		# remove the tmp file if you want to, if not comment it out
					# 		os.remove(tmpfilepath)
					# 	else:
					# 		self.parent.ifPythonRun(message_obj["cmd"], cmd_id, message_obj)
						
					# 	# Remove the command from DB and add it to log
					# 	self.parent.removeCommandFromDB(commandAddedPK)

					# elif message_obj["type"] == "os":

					# 	# os cmd
					# 	self.parent.logger_worker.debug("Executing commands \"%s\"" % message_obj["cmd"])
					# 	if " " in message_obj["cmd"]:
					# 		cmds = message_obj["cmd"].split(" ")
					# 	else:
					# 		cmds = [message_obj["cmd"]]
					# 	self.parent.ifOSRun(cmds, cmd_id, message_obj)
					# 	# Remove the command from DB and add it to log
					# 	self.parent.removeCommandFromDB(commandAddedPK)

			# except Exception as e:
			# 	self.parent.conn.nack(header_message_id, self.parent.CRONIO_WORKER_ID)
			# 	print e
			# 	self.parent.logger_worker.critical("Exception on message \"%s\"" % str(e))
			# 	raise e


	def checkWorkersDependenciesRunIfOK(self, cmd_id):
		commandFound = self.session.query(Commands).filter_by(cmd_id=cmd_id, status="pending").first()
		if commandFound:
			if commandFound.dependencies == "":
				self.runCMDFromDB(cmd_id)
			else:
				checkResolvedMissing = self.session.query(CommandDeps).filter_by(to_run_cmd_id=cmd_id,resolved='No').first()
				if checkResolvedMissing:
					# Dependencies still have not been resolved.
					return False
				else:
					# Dependencies all have been resolved.
					checkResolvedAll = self.session.query(CommandDeps).filter_by(to_run_cmd_id=cmd_id,resolved='Yes',ok_to_run=False).all()
					commandFound = self.session.query(Commands).filter_by(cmd_id=cmd_id).first()
					api_log = commandFound.api_log
					if checkResolvedAll:
						# Send message to sender_id due to failed dependencies, will not run.
						ERROR = "Failed Dependency - Will not run command with cmd_id \"%s\"" % str(cmd_id)
						self.logger_worker.critical(ERROR)
						self.sendAPILog(result_code,{"out":"","error":str(ERROR),"exception":""},cmd_id, api_log)
						self.sendLog({"log":"", "error": ERROR },cmd_id)
					else:
						checkResolvedAll = self.session.query(CommandDeps).filter_by(to_run_cmd_id=cmd_id,resolved='Yes',ok_to_run=True).all()
						if checkResolvedAll:
							self.runCMDFromDB(cmd_id)
		else:
			ERROR = "Could not find command with cmd_id: %s " % cmd_id
			self.logger_worker.critical(ERROR)
		return False


	def dependencyResolved(self, cmd_id, result_code, worker_id, sender_id):
		dependencyFound = self.session.query(CommandDeps).filter_by(dep_cmd_id=cmd_id,worker_id=worker_id,sender_id=sender_id).first()
		if dependencyFound:
			dependencyFound.resolved = 'Yes'
			dependencyFound.resolved_result_code = result_code
			dependencyFound.resolved_date = datetime.datetime.now()
			if dependencyFound.resolved_result_code == dependencyFound.to_run_result_code:
				dependencyFound.ok_to_run = True
			else:
				dependencyFound.ok_to_run = False
			self.session.commit()
			self.checkWorkersDependenciesRunIfOK(dependencyFound.to_run_cmd_id)
			return True
		return False


	def runCMDFromDB(self,cmd_id):
		commandFoundDB = self.session.query(Commands).filter_by(cmd_id=cmd_id,status='pending').first()
		if commandFoundDB:
			message_obj = {"type": commandFoundDB.is_type, "cmd": commandFoundDB.cmd, "cmd_id": commandFoundDB.cmd_id, "api_log": commandFoundDB.api_log, "dependencies": commandFoundDB.dependencies, "sender_id": commandFoundDB.sender_id}
			self.logger_worker.debug("Got a command from database with cmd_id \"%s\" trying to run it now." % cmd_id)
			if message_obj["type"] == "python":
				# python cmd

				if "\n" in message_obj["cmd"]:
					# this contains multiple commands, will use the os command to execute the temp python file that will be created.
					tmpfilepath = self.writeToTemp(message_obj["cmd"])
					
					# TODO - needs to get the executable of python
					self.logger_worker.debug("Executing with Python2.7 \"%s\"" % tmpfilepath)
					self.ifOSRun(["/usr/bin/python2.7",tmpfilepath], message_obj["cmd_id"], message_obj)
					
					self.logger_worker.debug("Removing file \"%s\"" % tmpfilepath)
					# remove the tmp file if you want to, if not comment it out
					os.remove(tmpfilepath)
				else:
					self.ifPythonRun(message_obj["cmd"], message_obj["cmd_id"], message_obj)


			elif message_obj["type"] == "os":
				# os cmd
				self.logger_worker.debug("Executing commands \"%s\"" % message_obj["cmd"])
				if " " in message_obj["cmd"]:
					cmds = message_obj["cmd"].split(" ")
				else:
					cmds = [message_obj["cmd"]]
				self.ifOSRun(cmds, message_obj["cmd_id"], message_obj)
			# Remove the command from DB and add it to log

			self.session.delete(commandFoundDB)
			self.session.commit()

		else:
			self.logger_worker.critical("Tried to run a command from database with cmd_id \"%s\" and failed to find it." % cmd_id)


	def assignDefaultValues(self):
		self.CRONIO_AMQP_USERNAME =  "worker1"
		self.CRONIO_AMQP_PASSWORD =  "somepass"
		# By default, viewer logs are disabled in messages.
		self.CRONIO_EXCHANGE_LOG_INFO =  False#"cronio_log_info"
		self.CRONIO_EXCHANGE_LOG_ERROR =  False#"cronio_log_error"
		self.CRONIO_AMQP_HOST =  "localhost"
		self.CRONIO_AMQP_VHOST =  "/"
		self.CRONIO_AMQP_PORT =  61613
		self.CRONIO_AMQP_USE_SSL =  False
		self.CRONIO_LOGGER_LEVEL = logging.INFO
		self.CRONIO_LOGGER_FORMATTER = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
		self.CRONIO_ENGINE_RUNTIME_SECONDS = 60
		self.CRONIO_TEST_IS_NOT_ON = True
		self.CRONIO_WORKER_WORK_DIR = os.getcwd()
		self.CRONIO_WORKER_ID = "worker_1"
		self.CRONIO_WORKER_PREFIX = "queue_cronio_workers_"
		self.CRONIO_WORKER_QUEUE = self.CRONIO_WORKER_PREFIX + self.CRONIO_WORKER_ID
		# !! NOTICE !! This is to enable the MultiWorker Dependency (Workers should only be allowed to write to that queue otherwise one worker would be able to send commands to other workers.)
		# IDEA Permissions Giver ?
		self.CRONIO_WORKER_DEPENDENCY_PREFIX = "queue_cronio_workers_dependency_"
		self.CRONIO_WORKER_DEPENDENCY_OWN = self.CRONIO_WORKER_DEPENDENCY_PREFIX + self.CRONIO_WORKER_ID
		# Enable this in your worker to refresh on each start
		self.REFRESH_DATABASE = True

	def initConnectWorkerSTOMP(self):
		self.conn = stomp.Connection(host_and_ports=[(self.CRONIO_AMQP_HOST, self.CRONIO_AMQP_PORT)],use_ssl=self.CRONIO_AMQP_USE_SSL,vhost=self.CRONIO_AMQP_VHOST)
		self.conn.set_listener("", self.cronio_worker_listener)
		self.conn.start()
		try:
			self.conn.connect(self.CRONIO_AMQP_USERNAME, self.CRONIO_AMQP_PASSWORD, wait=True)
			# ack=auto when received removes it from queue
			# ack="client" make it ack only when told to
			self.logger_worker.info("Subscribing to  \"%s\"" % str(self.CRONIO_WORKER_QUEUE))
			self.conn.subscribe(destination=self.CRONIO_WORKER_QUEUE, id=self.CRONIO_WORKER_ID+"_job_queue", ack="client")
			self.logger_worker.info("Subscribing to  \"%s\"" % str(self.CRONIO_WORKER_DEPENDENCY_OWN))
			self.conn.subscribe(destination=self.CRONIO_WORKER_DEPENDENCY_OWN, id=self.CRONIO_WORKER_ID+"_dependency", ack="client")

			# Run for 60 Seconds and stop, can be used to be called in crontab.
			time.sleep(self.CRONIO_ENGINE_RUNTIME_SECONDS)
		except Exception as e:
			self.logger_worker.critical("Failed to connect to STOMP \"%s\"" % str(e))
			raise e
		finally:
			self.conn.disconnect()
			
# if self.checkDependenciesOK(cmd_id, cmd, is_type, sender_id, dependencies, api_log):
	def addCommandAndDependiesOfOtherWorkersToDB(self, cmd_id, cmd, is_type, sender_id, dependencies, api_log):
		pk = False
		self.logger_worker.debug("Adding Command and Dependencies if any in DB.")
		self.logger_worker.debug(" Adding Command %s" % cmd_id)
		if dependencies is None:
			commandNew = Commands(cmd_id=cmd_id,cmd=cmd,is_type=is_type, sender_id=sender_id, dependencies=None, api_log=api_log)
			self.session.add(commandNew)
			self.session.commit()
			pk = commandNew.pk
			self.logger_worker.debug(" No Dependencies")
		else:
			commandNew = Commands(cmd_id=cmd_id,cmd=cmd,is_type=is_type, sender_id=sender_id, dependencies=json.dumps(dependencies), api_log=api_log)
			self.session.add(commandNew)
			self.session.commit()
			pk = commandNew.pk
			self.logger_worker.debug(" Adding Dependencies: ")
			for dependency in dependencies:
				newCmdDep = None
				if type(dependency) == type({}):
					dependency_worker_id = self.CRONIO_WORKER_ID
					if "worker_id" in dependency:
						dependency_worker_id = dependency['worker_id']
					self.logger_worker.debug("  - result_code is %s, dependency cmd_id: %s, worker_id: %s " % (dependency['result_code'], dependency['cmd_id'], dependency_worker_id))
					newCmdDep = CommandDeps(dep_cmd_id=dependency['cmd_id'], to_run_cmd_id= cmd_id, to_run_result_code=dependency['result_code'], worker_id=dependency_worker_id, sender_id=sender_id)
					self.session.add(newCmdDep)
					self.session.commit()
				else:
					self.logger_worker.debug("  - (Old Format default) result_code is 0, dependency cmd_id: %s" % dependency)
					newCmdDep = CommandDeps(dep_cmd_id=dependency, to_run_cmd_id= cmd_id, to_run_result_code=0, worker_id=self.CRONIO_WORKER_ID, sender_id=sender_id)
					self.session.add(newCmdDep)
					self.session.commit()
		return pk

	def removeCommandFromDB(self, pk):
		commandFound = self.session.query(Commands).filter_by(pk=pk).first()
		if commandFound:
			self.session.delete(commandFound)
			self.session.commit()

	def clearDatabase(self):
		print "Clear Database"
		Base.metadata.drop_all(self.engine)
		self.session.commit()
		Base.metadata.create_all(self.engine)
		self.session.commit()

	def ifOSRun(self, cmd, cmd_id, job_message):
		from subprocess import Popen, PIPE
		ExceptionError = ""
		OUT, ERROR = "",""
		result_code = 0
		try:
			self.logger_worker.debug("OS RUN command: %s" % str(cmd))
			p = Popen(cmd, stdout=PIPE, stderr=PIPE)
			OUT, ERROR = p.communicate()
			result_code = p.returncode
			self.logger_worker.debug(" Return Code: %s" % str(result_code))
		except Exception as e:
			self.logger_worker.debug(" Exception: %s" % str(e))
			ExceptionError = e
			if result_code == 0:
				result_code = 1

		self.logger_worker.debug(" Log Will Send Message:")	
		self.logger_worker.debug("  OUT: %s" % OUT)
		if ERROR != "" or ExceptionError != "":
			self.logger_worker.debug("  ERROR: %s"% str(ERROR+str(ExceptionError)))
		if self.CRONIO_TEST_IS_NOT_ON:
			self.sendAPILog(result_code,{"out":OUT,"error":str(ERROR),"exception":str(ExceptionError)},cmd_id, job_message["api_log"])
			self.addToCommandLog(cmd_id, cmd, job_message["type"], job_message["sender_id"], job_message["dependencies"], result_code, job_message["api_log"])
			self.sendLog({"log":OUT, "error": ERROR+str(ExceptionError) },cmd_id)
		return True

	def addToCommandLog(self, cmd_id, cmd, is_type, sender_id, dependencies, result_code, api_log):
		commandLogNew = CommandLog(cmd_id=cmd_id, cmd=json.dumps(cmd),is_type=is_type, sender_id=sender_id, dependencies=json.dumps(dependencies), result_code=result_code, api_log=api_log)
		self.session.add(commandLogNew)
		self.session.commit()
		
	def writeToTemp(self, cmds):
		# Handle opening the file yourself. This makes clean-up
		# more complex as you must watch out for exceptions
		fd, path = tempfile.mkstemp()
		with os.fdopen(fd, "w") as tmp:
			# do stuff with temp file
			tmp.write(cmds)
			tmp.close()
		self.logger_worker.debug("Return Temp Path of file %s",path)
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
			self.logger_worker.debug("PYTHON RUN command: %s"%str(cmd))
			exec cmd
		except Exception as e:
			raise e
			self.logger_worker.debug(" Exception: %s"%str(e))
			ExceptionError = str(e)
			result_code = 1
		finally:
			sys.stdout = sys.__stdout__
			sys.stderr = sys.__stderr__

		ERROR = u""+codeErr.getvalue()
		OUT = u""+codeOut.getvalue()
		codeOut.close()
		codeErr.close()

		self.logger_worker.debug(" Log Will Send Message:")	
		self.logger_worker.debug("  OUT: %s"%OUT)
		if ERROR != "" or ExceptionError != "":
			self.logger_worker.debug("  ERROR: %s"%str(ERROR+str(ExceptionError)))
		if self.CRONIO_TEST_IS_NOT_ON:
			self.sendAPILog(result_code,{"out":OUT,"error":ERROR,"exception":ExceptionError},cmd_id, job_message["api_log"])
			self.addToCommandLog(cmd_id, cmd, job_message["type"], job_message["sender_id"], job_message["dependencies"], result_code, job_message["api_log"])
			self.sendLog({"log":OUT, "error": ERROR+str(ExceptionError) },cmd_id)
		return True


	def sendAPILog(self, result, info, cmd_id, api_log):
		api_message = {}
		api_message["cmd_id"] = cmd_id
		api_message["result"] = result
		api_message["info"] = info
		api_message["message_at"] = str(datetime.datetime.now())
		api_message["type"] = "job"
		api_message["worker_id"] = self.CRONIO_WORKER_ID
		if self.CRONIO_TEST_IS_NOT_ON:
			pprint.pprint(api_message)
			self.conn.send(body=json.dumps(api_message), destination=api_log, vhost=self.CRONIO_AMQP_VHOST)

	def sendAPIInform(self, info, api_log):
		api_message = info
		api_message["worker_id"] = self.CRONIO_WORKER_ID
		if self.CRONIO_TEST_IS_NOT_ON:
			self.conn.send(body=json.dumps(api_message), destination=api_log, vhost=self.CRONIO_AMQP_VHOST)

	def sendLog(self, log, cmd_id):
		out_log = {"log": log["log"],"error" : False,"worker_id": self.CRONIO_WORKER_ID,"cmd_id": cmd_id}
		if log["error"] != "":
			out_log["error"] = True
			out_error = {"log": log["error"],"worker_id": self.CRONIO_WORKER_ID,"cmd_id": cmd_id}
			if self.CRONIO_TEST_IS_NOT_ON and self.CRONIO_EXCHANGE_LOG_ERROR:
				self.logger_worker.debug("Sending Error Message to %s with vhost %s"% (self.CRONIO_EXCHANGE_LOG_ERROR,self.CRONIO_AMQP_VHOST))
				self.logger_worker.debug(" Error Message: %s"% json.dumps(out_error))
				self.conn.send(body=json.dumps(out_error), destination=self.CRONIO_EXCHANGE_LOG_ERROR,vhost=self.CRONIO_AMQP_VHOST)
		
		if self.CRONIO_TEST_IS_NOT_ON and self.CRONIO_EXCHANGE_LOG_INFO:
			self.logger_worker.debug("Sending Log Message to %s with vhost %s"% (self.CRONIO_EXCHANGE_LOG_INFO,self.CRONIO_AMQP_VHOST))
			self.logger_worker.debug(" Log Message: %s"%json.dumps(out_log))
			self.conn.send(body=json.dumps(out_log), destination=self.CRONIO_EXCHANGE_LOG_INFO,vhost=self.CRONIO_AMQP_VHOST)

	def sendAPIInformWorkerDependencyResult(self, cmd_id, worker_id, result_code, api_log, sender_id):
		data = {"cmd_id": cmd_id, "worker_id": self.CRONIO_WORKER_ID, "result_code": result_code, "type": "operation", "cmd": "dependency_result", "sender_id": sender_id, "api_log": api_log}
		self.logger_worker.debug("Sending Worker Dependency with cmd_id: %s  and result_code: %s worker_id: %s"% (cmd_id, result_code, worker_id))
		self.sendAPIInform({"dependency_data":data, "worker_id": worker_id ,"message_at": str(datetime.datetime.now())},api_log)
		self.conn.send(body=json.dumps(data), destination=self.CRONIO_WORKER_DEPENDENCY_PREFIX + worker_id, vhost=self.CRONIO_AMQP_VHOST)

	def sendDependencyResultToWorker(self, message_obj, api_log):
		# CommandLog(cmd_id=cmd_id, cmd=json.dumps(cmd),is_type=is_type, sender_id=sender_id, dependencies=json.dumps(dependencies), result_code=10001, api_log=api_log)
		commandLogFound = self.session.query(CommandLog).filter_by(cmd_id=message_obj["cmd_id"]).first()
		if commandLogFound:
			self.sendAPIInformWorkerDependencyResult(message_obj["cmd_id"], message_obj["worker_id"], commandLogFound.result_code, api_log, message_obj["sender_id"])
		else:
			# 1003 Could not be found
			# TODO ERROR Documentation 10003
			self.sendAPIInformWorkerDependencyResult(message_obj["cmd_id"],message_obj["worker_id"], 10003, api_log, message_obj["sender_id"])
			self.sendAPIInform({"dependency_data":message_obj, "result_code": 10003, "message": "Could not find CMD ID in Database.","message_at": str(datetime.datetime.now())},api_log)
			self.sendAPILog(10003,{"out":message_obj,"error":"Could not find CMD in Database","exception":""}, message_obj["cmd_id"], api_log)