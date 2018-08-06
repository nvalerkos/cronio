from __future__ import absolute_import
import time, sys, pprint, json, os, tempfile
import logging
import stomp


class CronioSender(object):
	def __init__(self, settings = {}):
		#Set Default Values
		self.assignSenderDefaultValues()
		settingKeys = ['CRONIO_SENDER_EXCHANGE_LOG_INFO','CRONIO_SENDER_EXCHANGE_LOG_ERROR','CRONIO_SENDER_AMQP_USERNAME','CRONIO_SENDER_AMQP_PASSWORD','CRONIO_SENDER_WORKER_QUEUE','CRONIO_SENDER_AMQP_HOST','CRONIO_SENDER_AMQP_VHOST','CRONIO_SENDER_AMQP_PORT','CRONIO_SENDER_AMQP_USE_SSL','CRONIO_SENDER_LOGGER_LEVEL','CRONIO_SENDER_LOGGER_FORMATTER']
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
		self.CRONIO_SENDER_EXCHANGE_LOG_INFO = "cronio_log_info"
		self.CRONIO_SENDER_EXCHANGE_LOG_ERROR = "cronio_log_error"
		self.CRONIO_SENDER_AMQP_USERNAME = "sender1"
		self.CRONIO_SENDER_AMQP_PASSWORD = "somepass"
		self.CRONIO_SENDER_WORKER_QUEUE = "cronio_queue"
		self.CRONIO_SENDER_AMQP_HOST = 'localhost'
		self.CRONIO_SENDER_AMQP_VHOST = '/'
		self.CRONIO_SENDER_AMQP_PORT = 61613
		self.CRONIO_SENDER_AMQP_USE_SSL = False
		self.CRONIO_SENDER_LOGGER_LEVEL =  logging.INFO
		self.CRONIO_SENDER_LOGGER_FORMATTER = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


	def sendCMD(self, cmd, is_type = "python", cmd_id=False):
		jobSend = {"cmd": cmd, "type": is_type, "cmd_id": cmd_id}
		self.logger_sender.debug('Sending CMD: %s' % cmd)
		self.conn.send(body=json.dumps(jobSend), destination=self.CRONIO_SENDER_WORKER_QUEUE, vhost=self.CRONIO_SENDER_AMQP_VHOST)

	def sendPythonFile(self, pythonFile, cmd_id = False):
		if (os.path.isfile(pythonFile)):
			self.logger_sender.debug('Reading Python file: %s' % pythonFile)
			with open(pythonFile) as f:
				cmds = f.readlines()
			self.sendCMD("".join(cmds),"python",cmd_id)
			return True
		else:
			print 'Python file does not exists : %s' % pythonFile
			self.logger_sender.debug('Python file does not exists : %s' % pythonFile)
			return False			
		# except Exception as e:
		# 	raise e
		# 	self.logger_sender.debug('Exception while sending/reading python file: %s' % e)
		# 	return False
			
			

	def sendCmdFile(self, cmdFile, cmd_id = False):
		try:
			if (os.path.isfile(cmdFile)):
				self.logger_sender.debug('Reading commands file: %s' % cmdFile)
				with open(cmdFile) as f:
					cmds = f.readlines()
				self.sendCMD("".join(cmds),"os",cmd_id)
				return True
			else:
				self.logger_sender.debug('Commands file does not exists : %s' % cmdFile)
				return False			
		except Exception as e:
			print e
			self.logger_sender.debug('Exception while sending/reading commands file: %s' % e)
			return False

	def disconnectSenderSTOMP(self):
		self.logger_sender.debug('Disconnecting...')
		self.conn.disconnect()

	def initConnectSenderSTOMP(self):
		self.conn = stomp.Connection(host_and_ports=[(self.CRONIO_SENDER_AMQP_HOST, self.CRONIO_SENDER_AMQP_PORT)],use_ssl=self.CRONIO_SENDER_AMQP_USE_SSL,vhost=self.CRONIO_SENDER_AMQP_VHOST)
		self.conn.set_listener('', self.cronio_sender_listener)
		self.conn.start()
		try:
			self.conn.connect(self.CRONIO_SENDER_AMQP_USERNAME, self.CRONIO_SENDER_AMQP_PASSWORD, wait=True)
		except Exception as e:
			self.logger_sender.critical('Failed to connect to STOMP "%s"' % str(e))
			raise e
		# ack=auto when received removes it from queue
		# ack='client' make it ack only when told to
		self.conn.subscribe(destination=self.CRONIO_SENDER_EXCHANGE_LOG_INFO, id="log", ack='client')
		self.conn.subscribe(destination=self.CRONIO_SENDER_EXCHANGE_LOG_ERROR, id="error", ack='client')

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
	
	def __exit__(self, exc_type, exc_value, tb):
		self.logger_sender.debug('Disconnecting...')
		self.conn.disconnect()


