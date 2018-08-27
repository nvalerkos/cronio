import os

class CronioUtils():
	#Assign From ENV (Environment Variables or set to from code if not found)
	def assignFromENVorSetTo(self, key, value):
		try:
			if key in os.environ:
				return os.environ[key]
			else:
				return value
		except Exception as e:
			return value

	def checkDependancyWorkerID(self, dictTest):
		if dictTest is None:
			return False
		elif type(dictTest) == type([]):
			if len(dictTest) > 0:
				if type(dictTest[0]) == type({}):
					for keys in dictTest:
						if not ("worker_id" in keys and "cmd_id" in keys):
							return False
					return 'dict'
				elif type(dictTest[0]) == type(str()) or type(dictTest[0]) == type(100) or type(dictTest[0]) == type(u''):
					return 'StringOrNumberOrUnicode'
				else:
					return False
			else:
				return False