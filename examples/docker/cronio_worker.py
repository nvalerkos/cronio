# -*- coding: utf-8 -*-
import sys,os,logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cronio import CronioUtils, CronioWorker, CronioSender


CW = CronioWorker({'CRONIO_AMQP_USERNAME':   "worker1",
'CRONIO_AMQP_PASSWORD':   "somepass",
# To Enable Viewer Log, uncomment the below in worker and sender:
# 'CRONIO_EXCHANGE_LOG_INFO':   "cronio_log_info",
# 'CRONIO_EXCHANGE_LOG_ERROR':   "cronio_log_error",
'CRONIO_WORKER_ID':   "worker_1",
'CRONIO_AMQP_HOST':   '172.17.0.1',
'CRONIO_AMQP_VHOST':   '/',
'CRONIO_AMQP_PORT':   61613,
'CRONIO_AMQP_USE_SSL':   False,
'CRONIO_LOGGER_LEVEL':  logging.DEBUG,#logging.DEBUG
'CRONIO_LOGGER_FORMATTER':  '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
'CRONIO_ENGINE_RUNTIME_SECONDS':  59,
'CRONIO_WORKER_WORK_DIR': os.getcwd()})
