from __future__ import absolute_import
import time, sys, pprint, json, os, tempfile

#requirements.txt
import logging
import stomp
module_logger_worker = logging.getLogger('cronio_worker')

class CronioWorker(object):
	def __init__(self, settings = {}):
		#Set Default Values
		self.assignDefaultValues()
		settingKeys = ['CRONIO_AMQP_USERNAME','CRONIO_AMQP_PASSWORD','CRONIO_EXCHANGE_LOG_INFO','CRONIO_EXCHANGE_LOG_ERROR','CRONIO_WORKER_QUEUE','CRONIO_AMQP_HOST','CRONIO_AMQP_VHOST','CRONIO_AMQP_PORT','CRONIO_AMQP_USE_SSL','CRONIO_LOGGER_LEVEL','CRONIO_LOGGER_FORMATTER','CRONIO_ENGINE_RUNTIME_SECONDS','CRONIO_TEST_IS_NOT_ON','CRONIO_WORKER_WORK_DIR']
		for key in settingKeys:
			if key in settings:
				setattr(self, key, settings[key])
			
		self.logger_worker = logging.getLogger('cronio_worker')
		self.logger_worker.setLevel(self.CRONIO_LOGGER_LEVEL)
		loggerSH = logging.StreamHandler()
		formatter = logging.Formatter(self.CRONIO_LOGGER_FORMATTER)
		loggerSH.setFormatter(formatter)
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
			message_obj = json.loads(message)
			cmd_id = False
			if 'cmd' in message_obj:
				self.parent.logger_worker.debug('New Message Job %s' % str(message_obj['cmd']))
			
			if 'cmd_id' in message_obj:
				self.parent.logger_worker.debug(' with cmd_id = %s' % str(message_obj['cmd_id']))
				cmd_id = message_obj['cmd_id'] 

			if message_obj['type'] == "python":
				self.parent.logger_worker.debug('Worker remove from queue "%s"' % headers['message-id'])
				self.parent.conn.ack(headers['message-id'],1)
				if "\n" in message_obj['cmd']:
					tmpfilepath = self.parent.writeToTemp(message_obj['cmd'])
					
					# TODO - needs to get the executable of python
					self.parent.logger_worker.debug('Executing with Python2.7 "%s"' % tmpfilepath)
					self.parent.ifOSRun(["/usr/bin/python2.7",tmpfilepath], cmd_id)
					
					# remove the tmp file if you want to, if not comment it out
					self.parent.logger_worker.debug('Removing file "%s"' % tmpfilepath)
					os.remove(tmpfilepath)
				else:
					self.parent.ifPythonRun(message_obj['cmd'], cmd_id)

			if message_obj['type'] == "os":

				self.parent.logger_worker.debug('Worker remove from queue "%s"' % headers['message-id'])
				self.parent.conn.ack(headers['message-id'],1)
				
				self.parent.logger_worker.debug('Executing commands "%s"' % message_obj['cmd'])
				if " " in message_obj['cmd']:
					cmds = message_obj['cmd'].split(" ")
				else:
					cmds = [message_obj['cmd']]
				self.parent.ifOSRun(cmds, cmd_id)


	def assignDefaultValues(self):
		self.CRONIO_AMQP_USERNAME =  "worker1"
		self.CRONIO_AMQP_PASSWORD =  "somepass"
		self.CRONIO_EXCHANGE_LOG_INFO =  "cronio_log_info"
		self.CRONIO_EXCHANGE_LOG_ERROR =  "cronio_log_error"
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
		self.conn.subscribe(destination=self.CRONIO_WORKER_QUEUE, id=2, ack='client')

		# Run for 60 Seconds and stop, can be used to be called in crontab.
		time.sleep(self.CRONIO_ENGINE_RUNTIME_SECONDS)
		self.conn.disconnect()





	def ifOSRun(self, cmd, cmd_id = False):
		from subprocess import Popen, PIPE
		ExceptionError = ""
		OUT, ERROR = "",""
		try:
			self.logger_worker.debug('OS RUN command: %s' % str(cmd))
			p = Popen(cmd, stdout=PIPE, stderr=PIPE)
			OUT, ERROR = p.communicate()
			rc = p.returncode
			self.logger_worker.debug(' Return Code: %s' % str(rc))
		except Exception as e:
			self.logger_worker.debug(' Exception: %s' % str(e))
			ExceptionError = e

		self.logger_worker.debug(' Log Will Send Message:')	
		self.logger_worker.debug('  OUT: %s' % OUT)
		self.logger_worker.debug('  ERROR: %s'% str(ERROR+str(ExceptionError)))
		if self.CRONIO_TEST_IS_NOT_ON:
			self.sendLog({'log':OUT, 'error': ERROR+str(ExceptionError) },cmd_id)
		return True

		
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



	def ifPythonRun(self, cmd, cmd_id = False):
		import StringIO
		ExceptionError = ""
		# create file-like string to capture output
		codeOut = StringIO.StringIO()
		codeErr = StringIO.StringIO()
		
		# capture output and errors
		sys.stdout = codeOut
		sys.stderr = codeErr
		ExceptionError = u""
		try:
			os.chdir(sef.CRONIO_WORKER_WORK_DIR)
			self.logger_worker.debug('PYTHON RUN command: %s'%str(cmd))
			exec cmd
		except Exception as e:
			self.logger_worker.debug(' Exception: %s'%str(e))
			ExceptionError = e
		finally:
			sys.stdout = sys.__stdout__
			sys.stderr = sys.__stderr__

		ERROR = u""+codeErr.getvalue()
		OUT = u""+codeOut.getvalue()
		codeOut.close()
		codeErr.close()

		self.logger_worker.debug(' Log Will Send Message:')	
		self.logger_worker.debug('  OUT: %s'%OUT)
		self.logger_worker.debug('  ERROR: %s'%str(ERROR+str(ExceptionError)))
		if self.CRONIO_TEST_IS_NOT_ON:
			self.sendLog({'log':OUT, 'error': ERROR+str(ExceptionError) },cmd_id)
		return True


	def sendLog(self, log,cmd_id=False):
		out_log = {'log': log['log'],'error' : False}
		if cmd_id:
			out_log['cmd_id'] = cmd_id

		if log['error'] != '':
			out_log['error'] = True
			out_error = {'log': log['error']}
			if cmd_id:
				out_error['cmd_id'] = cmd_id
			self.logger_worker.debug('Sending Error Message to %s with vhost %s'% (self.CRONIO_EXCHANGE_LOG_ERROR,self.CRONIO_AMQP_VHOST))
			self.logger_worker.debug(' Error Message: %s'% json.dumps(out_error))
			if self.CRONIO_TEST_IS_NOT_ON:
				self.conn.send(body=json.dumps(out_error), destination=self.CRONIO_EXCHANGE_LOG_ERROR,vhost=self.CRONIO_AMQP_VHOST)
		
		self.logger_worker.debug('Sending Log Message to %s with vhost %s'% (self.CRONIO_EXCHANGE_LOG_INFO,self.CRONIO_AMQP_VHOST))
		self.logger_worker.debug(' Log Message: %s'%json.dumps(out_log))
		if self.CRONIO_TEST_IS_NOT_ON:
			self.conn.send(body=json.dumps(out_log), destination=self.CRONIO_EXCHANGE_LOG_INFO,vhost=self.CRONIO_AMQP_VHOST)

	def __exit__(self, exc_type, exc_value, tb):
		if exc_type is not ValueError:
			self.logger_sender.debug('Disconnecting...')
			if self.CRONIO_TEST_IS_NOT_ON:
				self.conn.disconnect()

