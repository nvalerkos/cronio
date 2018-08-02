import time, sys, pprint, json, os

#requirements.txt
import stomp

#Use this for receiving the output
#This needs to be created and the user to have access to read it.
CRONIO_EXCHANGE_LOG_INFO = "cronio_log_info"
CRONIO_EXCHANGE_LOG_ERROR = "cronio_log_error"

# RabbitMQ STOMP Settings
# Required Credentials
CRONIO_AMQP_USERNAME = "sender1"
CRONIO_AMQP_PASSWORD = "somepass"

#Use this for sending jobs to do
#This needs to be created and the user to have access to read it.
CRONIO_WORKER_QUEUE = "cronio_queue"
# RabbitMQ connection details and vhost
CRONIO_AMQP_HOST = 'localhost'
CRONIO_AMQP_VHOST = '/'
CRONIO_AMQP_PORT = 61613
CRONIO_AMQP_USE_SSL = False


class CronioSenderListener(stomp.ConnectionListener):
	def on_error(self, headers, message):
		print('received an error "%s"' % message)
	def on_message(self, headers, message):
		message_obj = json.loads(message)
		# remove from queue
		conn.ack(headers['message-id'],1)




def sendCMD(cmd,is_type = "python",cmd_id=False):
	jobSend = {"cmd": cmd, "type": is_type, "cmd_id": cmd_id}
	conn.send(body=json.dumps(jobSend), destination=CRONIO_WORKER_QUEUE,vhost=CRONIO_AMQP_VHOST)


conn = stomp.Connection(host_and_ports=[(CRONIO_AMQP_HOST, CRONIO_AMQP_PORT)],use_ssl=CRONIO_AMQP_USE_SSL,vhost=CRONIO_AMQP_VHOST)
conn.set_listener('', CronioSenderListener())
conn.start()
conn.connect(CRONIO_AMQP_USERNAME, CRONIO_AMQP_PASSWORD, wait=True)
# ack=auto when received removes it from queue
# ack='client' make it ack only when told to

conn.subscribe(destination=CRONIO_EXCHANGE_LOG_INFO, id="log", ack='client')
conn.subscribe(destination=CRONIO_EXCHANGE_LOG_ERROR, id="error", ack='client')
 
sendCMD("git clone https://gitlab.com/doctormo/python-crontab.git","os",2)
sendCMD("ls","os",2)
sendCMD("import sys\nsys.path.append('/home/nikolas/croniopy/python-crontab')\nfrom crontab import CronTab\ncron = CronTab(user='nikolas')\niter2 = cron.find_comment('comment')  \nfor item2 in iter2:  \n\tprint item2","python",3)
# wait a bit until all executed, it 
# TODO Wait until all of your send cmds are executed and then leave.
time.sleep(15)
conn.disconnect()
