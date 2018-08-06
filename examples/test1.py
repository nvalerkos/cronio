# -*- coding: utf-8 -*-
import sys,os,logging
#if its installed within a folder, please use the below
#sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cronio import CronioUtils, CronioSender

CS = CronioSender({'CRONIO_SENDER_EXCHANGE_LOG_INFO': "cronio_log_info",
'CRONIO_SENDER_EXCHANGE_LOG_ERROR': "cronio_log_error",
'CRONIO_SENDER_AMQP_USERNAME': "sender1",
'CRONIO_SENDER_AMQP_PASSWORD': "somepass",
'CRONIO_SENDER_WORKER_QUEUE': "cronio_queue",
'CRONIO_SENDER_AMQP_HOST': 'localhost',
'CRONIO_SENDER_AMQP_VHOST': '/',
'CRONIO_SENDER_AMQP_PORT': 61613,
'CRONIO_SENDER_AMQP_USE_SSL': False,
'CRONIO_SENDER_LOGGER_LEVEL':  logging.DEBUG,
'CRONIO_SENDER_LOGGER_FORMATTER': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
'CRONIO_SENDER_RUNTIME_SECONDS': 5})

"""
2018-08-06 15:22:12,223 - cronio_worker - DEBUG - New Message Job ls
2018-08-06 15:22:12,223 - cronio_worker - DEBUG -  with cmd_id = 2
2018-08-06 15:22:12,223 - cronio_worker - DEBUG - Worker remove from queue "T_2@@session-LNN7mEPObjx2UeCL4SttZg@@1"
2018-08-06 15:22:12,224 - cronio_worker - DEBUG - Executing commands "ls"
2018-08-06 15:22:12,224 - cronio_worker - DEBUG - OS RUN command: [u'ls']
2018-08-06 15:22:12,225 - cronio_worker - DEBUG -  Return Code: 0
2018-08-06 15:22:12,226 - cronio_worker - DEBUG -  Log Will Send Message:
2018-08-06 15:22:12,226 - cronio_worker - DEBUG -   OUT: python-crontab
test1.py
worker.py

2018-08-06 15:22:12,226 - cronio_worker - DEBUG -   ERROR: 
2018-08-06 15:22:12,226 - cronio_worker - DEBUG - Sending Log Message to cronio_log_info with vhost /
2018-08-06 15:22:12,226 - cronio_worker - DEBUG -  Log Message: {"log": "python-crontab\ntest1.py\nworker.py\n", "cmd_id": 2, "error": false}
2018-08-06 15:22:12,226 - cronio_worker - DEBUG - New Message Job import sys
sys.path.append('/home/nikolas/cronio/examples/python-crontab')
from crontab import CronTab
cron = CronTab(user='nikolas')
iter2 = cron.find_comment('comment')  
for item2 in iter2:  
	print item2
2018-08-06 15:22:12,226 - cronio_worker - DEBUG -  with cmd_id = 3
2018-08-06 15:22:12,226 - cronio_worker - DEBUG - Worker remove from queue "T_2@@session-LNN7mEPObjx2UeCL4SttZg@@2"
2018-08-06 15:22:12,227 - cronio_worker - DEBUG - Return Temp Path of file /tmp/tmprEh5bb
2018-08-06 15:22:12,227 - cronio_worker - DEBUG - Executing with Python2.7 "/tmp/tmprEh5bb"
2018-08-06 15:22:12,227 - cronio_worker - DEBUG - OS RUN command: ['/usr/bin/python2.7', '/tmp/tmprEh5bb']
2018-08-06 15:22:12,263 - cronio_worker - DEBUG -  Return Code: 0
2018-08-06 15:22:12,263 - cronio_worker - DEBUG -  Log Will Send Message:
2018-08-06 15:22:12,263 - cronio_worker - DEBUG -   OUT: # * * * * * python /home/nikolas/test.py # comment

2018-08-06 15:22:12,263 - cronio_worker - DEBUG -   ERROR: 
2018-08-06 15:22:12,263 - cronio_worker - DEBUG - Sending Log Message to cronio_log_info with vhost /
2018-08-06 15:22:12,263 - cronio_worker - DEBUG -  Log Message: {"log": "# * * * * * python /home/nikolas/test.py # comment\n", "cmd_id": 3, "error": false}
2018-08-06 15:22:12,263 - cronio_worker - DEBUG - Removing file "/tmp/tmprEh5bb"
"""


#clone git directory
CS.sendCMD("git clone https://gitlab.com/doctormo/python-crontab.git","os",1)
#execute ls command on the current folder
CS.sendCMD("ls","os",2)
# execute python commands
CS.sendCMD("import sys\nsys.path.append('/home/nikolas/cronio/examples/python-crontab')\nfrom crontab import CronTab\ncron = CronTab(user='nikolas')\niter2 = cron.find_comment('comment')  \nfor item2 in iter2:  \n\tprint item2","python",3)
