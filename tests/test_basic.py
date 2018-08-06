# -*- coding: utf-8 -*-
import sys,os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cronio import CronioUtils, CronioWorker, CronioSender

import unittest, logging
def testAllConditions(conditions):
	TestOK = True
	for condition in conditions:
		TestOK = TestOK and condition
	return TestOK

class BasicTestSuite(unittest.TestCase):
	"""Basic test cases."""

	def __init__(self, *args, **kwargs):
		super(BasicTestSuite, self).__init__(*args, **kwargs)
		self.CW = CronioWorker({'CRONIO_ENGINE_RUNTIME_SECONDS':1,'CRONIO_LOGGER_LEVEL':logging.INFO,'CRONIO_TEST_IS_NOT_ON': False})

	def test_worker_temporary_write_file(self):
		try:
			# print "test_worker_temporary_write_file"
			tempfile = self.CW.writeToTemp('ls')
			import os.path
			conditions = []
			conditions.append((type(tempfile) == type("")))
			conditions.append(os.path.isfile(tempfile))
			os.remove(tempfile)
			conditions.append(not os.path.isfile(tempfile))
			self.assertTrue(testAllConditions(conditions))

		except Exception as e:
			print e
			self.assertTrue(False)



	def test_python_exec_exists(self):
		try:
			# print "test_python_exec"
			testcase = os.path.isfile("/usr/bin/python2.7")
			conditions = []
			conditions.append(testcase)
			self.assertTrue(testAllConditions(conditions))
			
		except Exception as e:
			print e
			self.assertTrue(False)


	def test_python_exec_works_properly(self):
		try:
			# print "test_python_exec_works_properly"
			tempfile = self.CW.writeToTemp('ls')
			conditions = []
			testcase = os.path.isfile(tempfile)
			conditions.append(testcase)
			self.CW.ifPythonRun('import sys\nprint sys.version_info[0]\nos.remove(\'%s\')'%tempfile)
			testcase = not os.path.isfile(tempfile)
			conditions.append(testcase)
			self.assertTrue(testAllConditions(conditions))

		except Exception as e:
			print e
			self.assertTrue(False)


	def test_os_exec_works_properly(self):
		try:
			# print "test_python_exec_works_properly"
			tempfile = self.CW.writeToTemp('ls')
			conditions = []
			testcase = os.path.isfile(tempfile)
			conditions.append(testcase)
			self.CW.ifOSRun(['rm','%s'%tempfile])
			testcase = not os.path.isfile(tempfile)
			conditions.append(testcase)
			self.assertTrue(testAllConditions(conditions))

		except Exception as e:
			print e
			print e
			self.assertTrue(False)



if __name__ == '__main__':
	unittest.main()
