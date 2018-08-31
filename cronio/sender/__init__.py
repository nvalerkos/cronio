from __future__ import absolute_import
import time, sys, pprint, json, os, tempfile
import logging
import stomp,uuid

from ..utils import CronioUtils

class CronioSender(object):
	def __init__(self, settings = {}):
		#Set Default Values
		self.cronio_utils = CronioUtils()
		self.assignSenderDefaultValues()
		settingKeys = ['CRONIO_SENDER_EXCHANGE_LOG_INFO','CRONIO_SENDER_EXCHANGE_LOG_ERROR','CRONIO_SENDER_AMQP_USERNAME','CRONIO_SENDER_AMQP_PASSWORD','CRONIO_SENDER_WORKER_QUEUE','CRONIO_SENDER_AMQP_HOST','CRONIO_SENDER_AMQP_VHOST','CRONIO_SENDER_AMQP_PORT','CRONIO_SENDER_AMQP_USE_SSL','CRONIO_SENDER_LOGGER_LEVEL','CRONIO_SENDER_LOGGER_FORMATTER','CRONIO_SENDER_ID','CRONIO_SENDER_WORKER_PREFIX','CRONIO_SENDER_WORKER_DEPENDENCY_PREFIX']
		for key in settingKeys:
			if key in settings:
				setattr(self, key, settings[key])
		
		self.logger_sender = logging.getLogger('cronio_sender')
		self.logger_sender.setLevel(self.CRONIO_SENDER_LOGGER_LEVEL)
		loggerSH = logging.StreamHandler()
		formatter = logging.Formatter(self.CRONIO_SENDER_LOGGER_FORMATTER)
		loggerSH.setFormatter(formatter)
		self.logger_sender.addHandler(loggerSH)
		self.cronio_sender_listener = self.CronioSenderListener(self)
		self.initConnectSenderSTOMP()
		self.myself = self

	class CronioSenderListener(stomp.ConnectionListener):
		def __init__(self, parent):
			self.parent = parent

		def on_error(self, headers, message):
			self.parent.logger_sender.debug('Cronio Sender Listener received an error "%s"' % message)
		def on_message(self, headers, message):
			self.parent.logger_sender.debug('New Message Log %s' % str(headers['message-id']))
			message_obj = json.loads(message)
			self.parent.logger_sender.debug(' Log %s' % str(message))
			# remove from queue
			self.parent.logger_sender.debug('ACK Log - Remove from Queue %s' % str(headers['message-id']))
			self.parent.conn.ack(headers['message-id'],1)

	def assignSenderDefaultValues(self):
		self.CRONIO_SENDER_EXCHANGE_LOG_INFO = False
		self.CRONIO_SENDER_EXCHANGE_LOG_ERROR = False
		self.CRONIO_SENDER_AMQP_USERNAME = "sender1"
		self.CRONIO_SENDER_AMQP_PASSWORD = "somepass"
		self.CRONIO_SENDER_AMQP_HOST = 'localhost'
		self.CRONIO_SENDER_AMQP_VHOST = '/'
		self.CRONIO_SENDER_AMQP_PORT = 61613
		self.CRONIO_SENDER_AMQP_USE_SSL = False
		self.CRONIO_SENDER_LOGGER_LEVEL =  logging.INFO
		self.CRONIO_SENDER_LOGGER_FORMATTER = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
		self.CRONIO_SENDER_ID = 'sender1'
		self.CRONIO_SENDER_WORKER_PREFIX = 'queue_cronio_workers_'
		self.CRONIO_SENDER_WORKER_DEPENDENCY_PREFIX = 'queue_cronio_workers_dependency_'
		self.CRONIO_SENDER_API_LOG = 'queue_cronio_sender_api_log_' + self.CRONIO_SENDER_ID


	def sendCMD(self, cmd, worker_id, is_type = "python", cmd_id=False, dependencies = None):
		jobSend = {"cmd": cmd, "type": is_type, "cmd_id": cmd_id,'sender_id':self.CRONIO_SENDER_ID, 'dependencies': dependencies, 'api_log': self.CRONIO_SENDER_API_LOG}
		self.logger_sender.debug('Sending CMD: %s | To worker_id: %s' % (cmd, worker_id))
		depCheck = self.cronio_utils.checkDependancyWorkerID(dependencies)
		if depCheck == 'dict':
			for dependency in dependencies:
				
				dependencyDataCheck = {"type": "operation", "cmd": "inform_dependency_worker", "worker_id": worker_id, "cmd_id": dependency["cmd_id"], "api_log": self.CRONIO_SENDER_API_LOG, "sender_id": self.CRONIO_SENDER_ID}
				self.logger_sender.debug('Sending dependency check: %s | To worker_id: %s | Inform worker_id: %s' % (str(dependency), str(dependency["worker_id"]), str(worker_id)))
				self.conn.send(body=json.dumps(dependencyDataCheck), destination=self.CRONIO_SENDER_WORKER_DEPENDENCY_PREFIX+dependency["worker_id"], vhost=self.CRONIO_SENDER_AMQP_VHOST)

		print self.CRONIO_SENDER_WORKER_PREFIX+worker_id
		self.conn.send(body=json.dumps(jobSend), destination=self.CRONIO_SENDER_WORKER_PREFIX+worker_id, vhost=self.CRONIO_SENDER_AMQP_VHOST)

	def sendPythonFile(self, pythonFile, worker_id, cmd_id = False, dependencies = None):
		if (os.path.isfile(pythonFile)):
			self.logger_sender.debug('Reading Python file: %s' % pythonFile)
			with open(pythonFile) as f:
				cmds = f.readlines()
			self.sendCMD("".join(cmds), worker_id, "python",cmd_id, dependencies)
			return True
		else:
			print 'Python file does not exists : %s' % pythonFile
			self.logger_sender.debug('Python file does not exists : %s' % pythonFile)
			return False			
		# except Exception as e:
		# 	raise e
		# 	self.logger_sender.debug('Exception while sending/reading python file: %s' % e)
		# 	return False

	def sendCmdFile(self, cmdFile, worker_id, cmd_id = False, dependencies = None):
		try:
			if (os.path.isfile(cmdFile)):
				self.logger_sender.debug('Reading commands file: %s' % cmdFile)
				with open(cmdFile) as f:
					cmds = f.readlines()
				self.sendCMD("".join(cmds), worker_id, "os",cmd_id,dependencies)
				return True
			else:
				self.logger_sender.debug('Commands file does not exists : %s' % cmdFile)
				return False			
		except Exception as e:
			print e
			self.logger_sender.debug('Exception while sending/reading commands file: %s' % e)
			return False
			
	def sendWorkflow(self, workflow):
		for cmd in workflow:
			print cmd
			self.sendCMD(cmd['cmd'], cmd['worker_id'], cmd['type'], cmd['cmd_id'], cmd['dependencies'])

	def disconnectSenderSTOMP(self):
		self.logger_sender.debug('Disconnecting...')
		self.conn.disconnect()

	def initConnectSenderSTOMP(self):
		self.conn = stomp.Connection(host_and_ports=[(self.CRONIO_SENDER_AMQP_HOST, self.CRONIO_SENDER_AMQP_PORT)],use_ssl=self.CRONIO_SENDER_AMQP_USE_SSL,vhost=self.CRONIO_SENDER_AMQP_VHOST)
		self.conn.set_listener('default', self.cronio_sender_listener)
		self.conn.start()
		try:
			self.conn.connect(self.CRONIO_SENDER_AMQP_USERNAME, self.CRONIO_SENDER_AMQP_PASSWORD, wait=True)
			print "Connected..."
		except Exception as e:
			self.logger_sender.critical('Failed to connect to STOMP "%s"' % str(e))
			raise e
		# ack=auto when received removes it from queue
		# ack='client' make it ack only when told to
		
# this is disabled, the below def function __exit__ should automatically disconnect
		# wait a bit until all executed, it 	
		# TODO Wait until all of your send cmds are executed and then leave.
		# if self.CRONIO_SENDER_RUNTIME_SECONDS > 0:
		# 	self.logger_sender.debug('Sleeping for "%s"' % str(self.CRONIO_SENDER_RUNTIME_SECONDS))
		# 	time.sleep(self.CRONIO_SENDER_RUNTIME_SECONDS)
		# 	self.logger_sender.debug('Disconnecting...')
		# 	self.conn.disconnect()
		# else:
		# 	self.logger_sender.debug('Waiting for ever! -- or manually disconnect, can use CRONIO_SENDER_RUNTIME_SECONDS for a specific time to disconnect')
	

