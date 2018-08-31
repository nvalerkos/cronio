# -*- coding: utf-8 -*-
import sys,os,logging,json,pprint,time,uuid
#if its installed within a folder, please use the below
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

cmd_ids = [str(uuid.uuid4()),str(uuid.uuid4()),str(uuid.uuid4()),str(uuid.uuid4()),str(uuid.uuid4()),str(uuid.uuid4())]
# pprint.pprint(cmd_ids)

# Use those on the following commands:
# git clone a repo
# CS.sendCMD("git clone https://gitlab.com/doctormo/python-crontab.git","worker_1","os",cmd_ids[1])
#execute ls command on the current folder
# CS.sendCMD("ls","worker_1","os",cmd_ids[2])
# execute python commands using that repo - you will need to change the sys.path.append.
# CS.sendCMD("import sys\nsys.path.append('/opt/cronio/example/python-crontab')\nfrom crontab import CronTab\ncron = CronTab(user='nikolas')\niter2 = cron.find_comment('comment')  \nfor item2 in iter2:  \n\tprint item2","worker_1","python",cmd_ids[3],[cmd_ids[2],cmd_ids[1]])

CS.sendCMD('cleardb',"worker_1",'operation',cmd_ids[4])

# CS.sendCMD("print 'hello'","worker_1","python",cmd_ids[3],None)


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


install_apt_packages = """
import os
os.environ['PATH']='/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
os.system('apt-get update')
os.system('apt-get install -y python-mysqldb')
"""

CS.sendCMD(install_apt_packages,"worker_1","python","apt-install-mysqldb",None)
checkENVs = """
import os, pprint
pprint.pprint(os.environ)
"""
# CS.sendCMD(checkENVs,"worker_1","python","checkenvs",None)
# show envs variables of process (525 is the pid)
# CS.sendCMD("cat /proc/525/environ", "worker_1", "os", "checkenv", None)

CS.sendCMD("pip install envparse","worker_1","os","checkenvs",None)


checkENVs = """
from envparse import env
env.read_envfile("/root/.env")
print "hostname is " + str(env('HOSTNAME',default='localhost'))
"""
CS.sendCMD(checkENVs,"worker_1","python","checkenvs",None)

# CS.sendCMD("pip install mysql-python","worker_1","os","pip-install-mysqldb",None)
# CS.sendWorkflow(cmds)
PythonFile = "docker/backup_db_file.py"
# CS.sendPythonFile(PythonFile,"worker_1")
time.sleep(10)