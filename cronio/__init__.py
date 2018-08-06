from __future__ import absolute_import

from .utils import CronioUtils
from .worker import CronioWorker
from .sender import CronioSender


__all__ = ['CronioUtils', 'CronioWorker', 'CronioSender']

if __name__ == '__main__':
	CU = CronioUtils()
	settings = {
		# "CRONIO_AMQP_USERNAME" : CU.assignFromENVorSetTo('CRONIO_AMQP_USERNAME', "worker1"),
		# "CRONIO_AMQP_PASSWORD" : CU.assignFromENVorSetTo('CRONIO_AMQP_PASSWORD', "somepass"),
		# #Use this for sending the output
		# #This needs to be created and the user to have access to write it.
		# "CRONIO_EXCHANGE_LOG_INFO" : CU.assignFromENVorSetTo('CRONIO_EXCHANGE_LOG_INFO', "cronio_log_info"),
		# "CRONIO_EXCHANGE_LOG_ERROR" : CU.assignFromENVorSetTo('CRONIO_EXCHANGE_LOG_ERROR', "cronio_log_error"),

		# #This needs to be created and the user to have access to read it.
		# #Use this for receiving jobs to do
		# "CRONIO_WORKER_QUEUE" : CU.assignFromENVorSetTo('CRONIO_WORKER_QUEUE', "cronio_queue"),

		# "CRONIO_AMQP_HOST" : CU.assignFromENVorSetTo('CRONIO_AMQP_HOST', 'localhost'),
		# "CRONIO_AMQP_VHOST" : CU.assignFromENVorSetTo('CRONIO_AMQP_VHOST', '/'),
		# "CRONIO_AMQP_PORT" : CU.assignFromENVorSetTo('CRONIO_AMQP_PORT', 61613),
		# "CRONIO_AMQP_USE_SSL" : CU.assignFromENVorSetTo('CRONIO_AMQP_USE_SSL', False),
		"CRONIO_ENGINE_RUNTIME_SECONDS": 5
	}
	CW = CronioWorker(settings)
