# -*- coding: utf-8 -*-
import sys,os,logging
#if its installed within a folder, please use the below
#sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cronio import CronioUtils, CronioSender


CS = CronioSender({
'CRONIO_SENDER_EXCHANGE_LOG_INFO': "cronio_log_info",
'CRONIO_SENDER_EXCHANGE_LOG_ERROR': "cronio_log_error",
'CRONIO_SENDER_AMQP_USERNAME': "sender1",
'CRONIO_SENDER_AMQP_PASSWORD': "somepass",
'CRONIO_SENDER_WORKER_QUEUE': "cronio_queue",
'CRONIO_SENDER_AMQP_HOST': 'localhost',
'CRONIO_SENDER_AMQP_VHOST': '/',
'CRONIO_SENDER_AMQP_PORT': 61613,
'CRONIO_SENDER_AMQP_USE_SSL': False,
'CRONIO_SENDER_LOGGER_LEVEL':  logging.DEBUG,
'CRONIO_SENDER_LOGGER_FORMATTER': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
})

# Absolute Path only
PythonFile = "/opt/cronio/examples/test.py"
CmdFile = "/opt/cronio/examples/test.sh"

print CS.sendPythonFile(PythonFile,1)
print CS.sendCmdFile(CmdFile,2)
