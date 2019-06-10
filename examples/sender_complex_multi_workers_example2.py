# -*- coding: utf-8 -*-
import sys,os,logging,json,pprint,time,uuid
#if its installed within a folder, please use the below
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cronio import CronioUtils, CronioSender
import stomp

# stomp_logger = logging.getLogger('stomp.py')
# stomp_logger.setLevel(logging.DEBUG)
WORKER_ID_1 = "worker_1"
WORKER_ID_2 = "worker_2"


"""
This example will send some commands which will depend on two worker's cmds result.
So
one sender -> two workers scenario but with invert resultcode ie. 
result_code = 1

"""



CS_1 = CronioSender({
# To Enable Viewer Log, uncomment the below in worker and sender:
# 'CRONIO_SENDER_EXCHANGE_LOG_INFO': "cronio_log_info",
# 'CRONIO_SENDER_EXCHANGE_LOG_ERROR': "cronio_log_error",
'CRONIO_SENDER_AMQP_USERNAME': "sender1",
'CRONIO_SENDER_AMQP_PASSWORD': "somepass",
'CRONIO_SENDER_WORKER_QUEUE': "cronio_queue"+WORKER_ID_1,
'CRONIO_SENDER_AMQP_HOST': 'localhost',
'CRONIO_SENDER_AMQP_VHOST': '/',
'CRONIO_SENDER_AMQP_PORT': 61613,
'CRONIO_SENDER_AMQP_USE_SSL': False,
'CRONIO_SENDER_LOGGER_LEVEL':  logging.DEBUG, #logging.DEBUG
'CRONIO_SENDER_LOGGER_FORMATTER': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
'CRONIO_SENDER_RUNTIME_SECONDS': 5})

class CronioSenderListener1(stomp.ConnectionListener):
	def on_error(self, headers, message):
		pprint.pprint(headers)
		pprint.pprint(message)
		CS_1.logger_sender.debug('Cronio Sender Listener received an error "%s"' % message)
	def on_message(self, headers, message):
		# Use the below to your discretion on receiving new messages
		# CS_1.logger_sender.debug(' %s' % str(headers['message-id']))
		# CS_1.logger_sender.debug(' Log %s' % str(message))
		# CS_1.logger_sender.debug('ACK Log - Remove from Queue %s' % str(headers['message-id']))
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
		CS_1.conn.ack(headers['message-id'],1)

CS_1.conn.disconnect()
CS_1.conn.remove_listener('default')
CS_1.cronio_sender_listener = CronioSenderListener1() 
CS_1.initConnectSenderSTOMP()
CS_1.conn.subscribe(destination=CS_1.CRONIO_SENDER_API_LOG, id="api_log", ack='client')


CS_2 = CronioSender({
# To Enable Viewer Log, uncomment the below in worker and sender:
# 'CRONIO_SENDER_EXCHANGE_LOG_INFO': "cronio_log_info",
# 'CRONIO_SENDER_EXCHANGE_LOG_ERROR': "cronio_log_error",
'CRONIO_SENDER_AMQP_USERNAME': "sender1",
'CRONIO_SENDER_AMQP_PASSWORD': "somepass",
'CRONIO_SENDER_WORKER_QUEUE': "cronio_queue"+WORKER_ID_2,
'CRONIO_SENDER_AMQP_HOST': 'localhost',
'CRONIO_SENDER_AMQP_VHOST': '/',
'CRONIO_SENDER_AMQP_PORT': 61613,
'CRONIO_SENDER_AMQP_USE_SSL': False,
'CRONIO_SENDER_LOGGER_LEVEL':  logging.DEBUG, #logging.DEBUG
'CRONIO_SENDER_LOGGER_FORMATTER': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
'CRONIO_SENDER_RUNTIME_SECONDS': 5})

class CronioSenderListener2(stomp.ConnectionListener):
	def on_error(self, headers, message):
		pprint.pprint(headers)
		pprint.pprint(message)
		CS_2.logger_sender.debug('Cronio Sender Listener received an error "%s"' % message)
	def on_message(self, headers, message):
		# Use the below to your discretion on receiving new messages
		# CS_1.logger_sender.debug(' %s' % str(headers['message-id']))
		# CS_1.logger_sender.debug(' Log %s' % str(message))
		# CS_1.logger_sender.debug('ACK Log - Remove from Queue %s' % str(headers['message-id']))
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
		CS_2.conn.ack(headers['message-id'],1)





CS_2.conn.disconnect()
CS_2.conn.remove_listener('default')
CS_2.cronio_sender_listener = CronioSenderListener2() 
CS_2.initConnectSenderSTOMP()

# SUBSCRIBE AT YOUR DISCRETION TO WHAT MESSAGES.
# By default is disabled, no need for this.
# CS_1.conn.subscribe(destination=CS_1.CRONIO_SENDER_EXCHANGE_LOG_INFO, id="view_log", ack='client')
# CS_1.conn.subscribe(destination=CS_1.CRONIO_SENDER_EXCHANGE_LOG_ERROR, id="view_error", ack='client')
CS_1.conn.subscribe(destination=CS_1.CRONIO_SENDER_API_LOG, id="api_log_1", ack='client')
# CS_2.conn.subscribe(destination=CS_1.CRONIO_SENDER_EXCHANGE_LOG_INFO, id="view_log", ack='client')
# CS_2.conn.subscribe(destination=CS_1.CRONIO_SENDER_EXCHANGE_LOG_ERROR, id="view_error", ack='client')
CS_2.conn.subscribe(destination=CS_2.CRONIO_SENDER_API_LOG, id="api_log_2", ack='client')



CS_1.sendCMD('cleardb',WORKER_ID_1,'operation',0)
CS_2.sendCMD('cleardb',WORKER_ID_2,'operation',0)

print "Wait a few seconds to cleardb"

from time import sleep
sleep(3) # Wait a few seconds to clear db, sometimes the db clear arrives a bit later of the dependency check or first command.

CS_1.sendCMD('echo "1"',WORKER_ID_1,'os',1)
CS_2.sendCMD('echow "2"',WORKER_ID_2,'os',2)


dependencies_cmd_4 = [
	{"cmd_id" : 1,"result_code" : 0, "worker_id" : WORKER_ID_1},
	{"cmd_id" : 2,"result_code" : 1, "worker_id" : WORKER_ID_2},
]

# dependency worker_2 cmd_id 2 on worker_id 1 for cmd_id 4

CS_1.sendCMD('echo "4"',WORKER_ID_1,'os',4, dependencies_cmd_4)

CS_1.conn.disconnect()
CS_2.conn.disconnect()
