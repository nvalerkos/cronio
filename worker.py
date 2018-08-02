import time, sys, pprint, json, os, tempfile

#requirements.txt
import stomp

def assignDefaultIfNone(key,value):
	try:
		if key in os.environ:
			return os.environ[key]
		else:
			return value
	except Exception as e:
		return value


# RabbitMQ STOMP Settings
# Required Credetials
CRONIO_AMQP_USERNAME = assignDefaultIfNone('CRONIO_AMQP_USERNAME', "worker1")
CRONIO_AMQP_PASSWORD = assignDefaultIfNone('CRONIO_AMQP_PASSWORD', "somepass")
#Use this for sending the output
#This needs to be created and the user to have access to write it.
CRONIO_EXCHANGE_LOG_INFO = assignDefaultIfNone('CRONIO_EXCHANGE_LOG_INFO', "cronio_log_info")
CRONIO_EXCHANGE_LOG_ERROR = assignDefaultIfNone('CRONIO_EXCHANGE_LOG_ERROR', "cronio_log_error")

#This needs to be created and the user to have access to read it.
#Use this for receiving jobs to do
CRONIO_WORKER_QUEUE = assignDefaultIfNone('CRONIO_WORKER_QUEUE', "cronio_queue")

CRONIO_AMQP_HOST = assignDefaultIfNone('CRONIO_AMQP_HOST', 'localhost')
CRONIO_AMQP_VHOST = assignDefaultIfNone('CRONIO_AMQP_VHOST', '/')
CRONIO_AMQP_PORT = assignDefaultIfNone('CRONIO_AMQP_PORT', 61613)
CRONIO_AMQP_USE_SSL = assignDefaultIfNone('CRONIO_AMQP_USE_SSL', False)

"""
CMDs
	PYTHON
		{"cmd":"print \"Hello World\"", "type":"python", "cmd_id": 1}
	OS
		{"cmd":"ls ~/", "type":"os", "cmd_id": 1}

ERROR

	PYTHON
	{"cmd":"print print \"Hello World\"", "type":"python", "cmd_id": 3}
"""

def ifOSRun(cmd, cmd_id):
	from subprocess import Popen, PIPE
	ExceptionError = ""
	OUT, ERROR = "",""
	try:
		print cmd
		p = Popen(cmd, stdout=PIPE, stderr=PIPE)
		OUT, ERROR = p.communicate()
		rc = p.returncode
		print p.returncode
	except Exception as e:
		print "Exception"
		ExceptionError = e

	pprint.pprint({'log':OUT, 'error': ERROR+str(ExceptionError) })
	sendLog({'log':OUT, 'error': ERROR+str(ExceptionError) },cmd_id)
	return True

	
def writeToTemp(cmds):
	# Handle opening the file yourself. This makes clean-up
	# more complex as you must watch out for exceptions
	fd, path = tempfile.mkstemp()
	with os.fdopen(fd, 'w') as tmp:
		# do stuff with temp file
		tmp.write(cmds)
		tmp.close()

	return path



def ifPythonRun(cmd, cmd_id = False):
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
		exec cmd
	except Exception as e:
		ExceptionError = e
	finally:
		sys.stdout = sys.__stdout__
		sys.stderr = sys.__stderr__

	ERROR = u""+codeErr.getvalue()
	OUT = u""+codeOut.getvalue()
	codeOut.close()
	codeErr.close()

	pprint.pprint({'log':OUT, 'error': ERROR+str(ExceptionError) })
	sendLog({'log':OUT, 'error': ERROR+str(ExceptionError) },cmd_id)
	return True


def sendLog(log,cmd_id=False):
	out_log = {'log': log['log'],'error' : False}
	if cmd_id:
		out_log['cmd_id'] = cmd_id

	if log['error'] != '':
		out_log['error'] = True
		out_error = {'log': log['error']}
		if cmd_id:
			out_error['cmd_id'] = cmd_id
		pprint.pprint(out_error)
		conn.send(body=json.dumps(out_error), destination=CRONIO_EXCHANGE_LOG_ERROR,vhost=CRONIO_AMQP_VHOST)

	conn.send(body=json.dumps(out_log), destination=CRONIO_EXCHANGE_LOG_INFO,vhost=CRONIO_AMQP_VHOST)

class CronioListener(stomp.ConnectionListener):
	def on_error(self, headers, message):
		print('received an error "%s"' % message)
	def on_message(self, headers, message):
		message_obj = json.loads(message)
		cmd_id = False
		if 'cmd_id' in message_obj:
			cmd_id = message_obj['cmd_id'] 

		if message_obj['type'] == "python":
			# Remove the message from queue
			conn.ack(headers['message-id'],1)
			if "\n" in message_obj['cmd']:
				tmpfilepath = writeToTemp(message_obj['cmd'])
				
				# TODO - needs to get the executable of python
				ifOSRun(["/usr/bin/python2.7",tmpfilepath], cmd_id)
				
				# remove the tmp file if you want to, if not comment it out
				os.remove(tmpfilepath)
			else:
				ifPythonRun(message_obj['cmd'], cmd_id)

		if message_obj['type'] == "os":
			conn.ack(headers['message-id'],1)
			if " " in message_obj['cmd']:
				cmds = message_obj['cmd'].split(" ")
			else:
				cmds = [message_obj['cmd']]
			ifOSRun(cmds, cmd_id)

		# pprint.pprint(message_obj)
		# pprint.pprint(headers)
		# remove from queue only when ack=client
		
		# do not remove from queue
		# conn.nack(headers['message-id'],1)


conn = stomp.Connection(host_and_ports=[(CRONIO_AMQP_HOST, CRONIO_AMQP_PORT)],use_ssl=CRONIO_AMQP_USE_SSL,vhost=CRONIO_AMQP_VHOST)
conn.set_listener('', CronioListener())
conn.start()
conn.connect(CRONIO_AMQP_USERNAME, CRONIO_AMQP_PASSWORD, wait=True)
# ack=auto when received removes it from queue
# ack='client' make it ack only when told to
conn.subscribe(destination=CRONIO_WORKER_QUEUE, id=2, ack='client')

# Run for 60 Seconds and stop, can be used to be called in crontab.
time.sleep(60)
conn.disconnect()