# -*- coding: utf-8 -*-
import sys,os,logging,json,pprint,time,uuid
#if its installed within a folder, please use the below
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cronio import CronioUtils, CronioSender
import stomp

# stomp_logger = logging.getLogger('stomp.py')
# stomp_logger.setLevel(logging.DEBUG)

CS = CronioSender({
# To Enable Viewer Log, uncomment the below in worker and sender:
# 'CRONIO_SENDER_EXCHANGE_LOG_INFO': "cronio_log_info",
# 'CRONIO_SENDER_EXCHANGE_LOG_ERROR': "cronio_log_error",
'CRONIO_SENDER_AMQP_USERNAME': "sender1",
'CRONIO_SENDER_AMQP_PASSWORD': "somepass",
'CRONIO_SENDER_WORKER_QUEUE': "cronio_queue",
'CRONIO_SENDER_AMQP_HOST': 'localhost',
'CRONIO_SENDER_AMQP_VHOST': '/',
'CRONIO_SENDER_AMQP_PORT': 61613,
'CRONIO_SENDER_AMQP_USE_SSL': False,
'CRONIO_SENDER_LOGGER_LEVEL':  logging.DEBUG, #logging.DEBUG
'CRONIO_SENDER_LOGGER_FORMATTER': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
'CRONIO_SENDER_RUNTIME_SECONDS': 5})


class CronioSenderListener(stomp.ConnectionListener):
	def on_error(self, headers, message):
		pprint.pprint(headers)
		pprint.pprint(message)
		CS.logger_sender.debug('Cronio Sender Listener received an error "%s"' % message)
	def on_message(self, headers, message):
		# Use the below to your discretion on receiving new messages
		# CS.logger_sender.debug(' %s' % str(headers['message-id']))
		# CS.logger_sender.debug(' Log %s' % str(message))
		# CS.logger_sender.debug('ACK Log - Remove from Queue %s' % str(headers['message-id']))
		# MESSAGE IS IN JSON
		message_obj = json.loads(message)
		pprint.pprint(message_obj)
		# if headers['subscription'] == "api_log":
		# 	pprint.pprint(message_obj)
		# if headers['subscription'] == "api_log":
			# This here is where the magic happens
			# print "API LOG =================================="
			# pprint.pprint(message_obj)
			# print "API LOG ENDS ============================="
		# else:
			# a bunch of other messages
			# print "view_log - or error"

		# remove from queue
		CS.conn.ack(headers['message-id'],1)


CS.conn.disconnect()
CS.conn.remove_listener('default')
CS.cronio_sender_listener = CronioSenderListener() 
CS.initConnectSenderSTOMP()

# SUBSCRIBE AT YOUR DISCRETION TO WHAT MESSAGES.
# By default is disabled, no need for this.
# CS.conn.subscribe(destination=CS.CRONIO_SENDER_EXCHANGE_LOG_INFO, id="view_log", ack='client')
# CS.conn.subscribe(destination=CS.CRONIO_SENDER_EXCHANGE_LOG_ERROR, id="view_error", ack='client')
CS.conn.subscribe(destination=CS.CRONIO_SENDER_API_LOG, id="api_log", ack='client')

# IF YOU WANT TO UNSUBSCRIBE
# c.subscribe('/queue/test', 123)
# c.unsubscribe(123)
# FOR MORE CHECK STOMP-PY DOCS - http://jasonrbriggs.github.io/stomp.py/api.html#sending-and-receiving-messages

#clone git directory


# You can generate a Unique Identifier for each command, or something else.
cmd_ids = [str(uuid.uuid4()),str(uuid.uuid4()),str(uuid.uuid4()),str(uuid.uuid4()),str(uuid.uuid4()),str(uuid.uuid4())]
# pprint.pprint(cmd_ids)

# Use those on the following commands:
# git clone a repo
# CS.sendCMD("git clone https://gitlab.com/doctormo/python-crontab.git","worker_1","os",cmd_ids[1])
#execute ls command on the current folder
# CS.sendCMD("ls","worker_1","os",cmd_ids[2])
# execute python commands using that repo - you will need to change the sys.path.append.
# CS.sendCMD("import sys\nsys.path.append('/opt/cronio/example/python-crontab')\nfrom crontab import CronTab\ncron = CronTab(user='nikolas')\niter2 = cron.find_comment('comment')  \nfor item2 in iter2:  \n\tprint item2","worker_1","python",cmd_ids[3],[cmd_ids[2],cmd_ids[1]])
# CS.sendCMD("print 'hello'","worker_1","python",cmd_ids[3],None)


# Clear Database of its commands
CS.sendCMD('cleardb',"worker_1",'operation',cmd_ids[4])
CS.sendCMD('cleardb',"worker_2",'operation',cmd_ids[4])


# Workflow Example - Set of commands related with each other.
# commands = [ {"cmd": "ls", "type": "os", "cmd_id": 1, "dependencies": None, "worker_id":"worker_1"}, {"cmd": "mkdir test_1", "type": "os", "cmd_id": 2, "dependencies": None, "worker_id":"worker_1"}, {"cmd": "cd test_1", "type": "os", "cmd_id": 3, "dependencies": [2], "worker_id":"worker_1"},{"cmd": "print \"hello cronio\"", "type": "python", "cmd_id": 4,"dependencies" : None, "worker_id":"worker_1"}]
# CS.sendWorkflow(commands)
dependencies_cmd_100 = [
	# {"cmd_id" : "99","result_code" : 0, "worker_id" : "worker_4"},
	# {"cmd_id" : "98","result_code" : 0, "worker_id" : "worker_3"},
	{"cmd_id" : "97","result_code" : 0, "worker_id" : "worker_2"}
]

cmds = [
	{"cmd": "echo 'worker2'", "worker_id": "worker_2", "type": "os", "cmd_id": 97, "dependencies": None}, 
	# {"cmd": "echo 'worker3'", "worker_id": "worker_3", "type": "os", "cmd_id": 98, "dependencies": None},
	# {"cmd": "print \"hello cronio\"", "worker_id": "worker_4", "type": "python", "cmd_id": 99,"dependencies" : None},
	{"cmd": "echo 'worker1'", "worker_id": "worker_1", "type": "os", "cmd_id": 100, "dependencies": dependencies_cmd_100},
]

CS.sendWorkflow(cmds)

# content = {
# 	'comment': 'complex data structure we would ideally want in there',
# 	'ie.1' : {
# 		'key': 'is value bla bla', 'value' : [1,2,3,4,5,6,7,10011]
# 	},
# 	'ie.2' : {
# 		'key': 'is value bla bla', 'value' : [1,2,3,4,5,6,7,10011]
# 	},
# 	'ie.3' : {
# 		'key': 'is value bla bla', 'value' : [1,2,3,4,5,6,7,10011]
# 	}
# }
# data = json.dumps(content)
# data = data.encode('hex')
# # !!!!!!!!!!!!!!!!!!!
# # fix the absolute path below
# CS.sendCMD("python /opt/cronio/example/test3.py "+data,"os",cmd_ids[5])

# # Absolute Path only
# PythonFile = "/opt/cronio/examples/test.py"
# CmdFile = "/opt/cronio/examples/test.sh"

# CS.sendPythonFile(PythonFile,1)
# CS.sendCmdFile(CmdFile,2)

time.sleep(10)