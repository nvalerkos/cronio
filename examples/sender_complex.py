# -*- coding: utf-8 -*-
import sys,os,logging,json,pprint,time,uuid
#if its installed within a folder, please use the below
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cronio import CronioUtils, CronioSender
import stomp

# stomp_logger = logging.getLogger('stomp.py')
# stomp_logger.setLevel(logging.DEBUG)
WORKER_ID = "worker_1"

CS = CronioSender({
# To Enable Viewer Log, uncomment the below in worker and sender:
# 'CRONIO_SENDER_EXCHANGE_LOG_INFO': "cronio_log_info",
# 'CRONIO_SENDER_EXCHANGE_LOG_ERROR': "cronio_log_error",
'CRONIO_SENDER_AMQP_USERNAME': "sender1",
'CRONIO_SENDER_AMQP_PASSWORD': "somepass",
'CRONIO_SENDER_WORKER_QUEUE': "cronio_queue"+WORKER_ID,
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

CS.conn.disconnect()
CS.conn.remove_listener('default')
CS.cronio_sender_listener = CronioSenderListener() 
CS.initConnectSenderSTOMP()
# CS.sendCMD('cleardb',WORKER_ID,'operation',0)
# CS.sendCMD('echo "1"',WORKER_ID,'os',1)
# CS.sendCMD('echo "2"',WORKER_ID,'os',2)
# CS.sendCMD('echo "3"',WORKER_ID,'os',3)

dependencies_cmd_4 = [
	{"cmd_id" : 1,"result_code" : 0, "worker_id" : WORKER_ID},
	{"cmd_id" : 2,"result_code" : 0, "worker_id" : WORKER_ID},
	# {"cmd_id" : 3,"result_code" : 0, "worker_id" : WORKER_ID}
]

CS.sendCMD('echo "4"',WORKER_ID,'os',4, dependencies_cmd_4)
# CS.sendCMD('echo "6"',WORKER_ID,'os',6)

dependencies_cmd_5 = [
	{"cmd_id" : 4,"result_code" : 0, "worker_id" : WORKER_ID}
]

# CS.sendCMD('echo "5"',WORKER_ID,'os',5, dependencies_cmd_5)



# CS.sendCMD('echo "7"',WORKER_ID,'os',7)
# CS.sendCMD('echo "8"',WORKER_ID,'os',8)
# CS.sendCMD('echo "9"',WORKER_ID,'os',9)
# CS.sendCMD('echo "10"',WORKER_ID,'os',10, dependencies_cmd_5)
CS.conn.disconnect()