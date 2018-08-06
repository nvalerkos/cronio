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