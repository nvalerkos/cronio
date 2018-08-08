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
'CRONIO_SENDER_LOGGER_LEVEL':  logging.INFO, #logging.DEBUG
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
		if headers['subscription'] == "api_log":
			pprint.pprint(message_obj)
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


# Generate a Unique Identifier
cmd_ids = [str(uuid.uuid4()),str(uuid.uuid4()),str(uuid.uuid4()),str(uuid.uuid4())]
pprint.pprint(cmd_ids)

# CS.sendCMD("python-crontab","os",cmd_ids[0])

# Use those on the following commands:

# git clone a repo
CS.sendCMD("git clone https://gitlab.com/doctormo/python-crontab.git","os",cmd_ids[1])
#execute ls command on the current folder
CS.sendCMD("ls","os",cmd_ids[2])
# execute python commands using that repo - you will need to change the sys.path.append.
CS.sendCMD("import sys\nsys.path.append('/home/nikolas/cronio/examples/python-crontab')\nfrom crontab import CronTab\ncron = CronTab(user='nikolas')\niter2 = cron.find_comment('comment')  \nfor item2 in iter2:  \n\tprint item2","python",cmd_ids[3],[cmd_ids[2],cmd_ids[1]])

# Clear Database
CS.sendCMD('cleardb','operation',1)

time.sleep(10)