# cronio

INTRO

>This project has a sender and a receiver, the sender sends commands through RabbitMQ on the queue of a worker (receiver), the receiver executes them either with OS or Python2.7

## Objectives

- [x] Prototype - Send some commands in OS or in Python and execute them, bring back the log or errors if any
- [x] Package Structure
- [x] Dependent Commands ie. dependancy: [1,2,3,200, cmd_id]
- [ ] Time to be executed ie. using python-crontab would be a good thing
- [ ] ENVs needs to be tested with docker that it can be set and read from this app.py
- [ ] Sender: Wait until all of your send cmds are executed and then leave.
- [ ] Worker: check if its the right binary to execute python2.7
- [ ] Run in other Languages ie. Ruby, Java, Cobol? Kidding..


## Requirements

1. STOMP Python Library 
2. SQLAlchemy (use of sqlite)
3. RabbitMQ Server (see myrabbitmq\ folder for details on raising a container with it.- You are welcome!)
	You can get one using our docker image - default username and password is guest.
	If you want the dockerfile for it, you can go to the folder's repository myrabbitmq.

Install Required packages (1,2)

	pip install -r requirements.txt 


## Installation 

PyPi

	pip install cronio



## Examples

For Code see examples\ directory
	
Worker:

	python worker.py # this will start the worker process, see inline comments


Sender:

	python sender.py # this has everything in it
	

## Custom Listener for Sender

Modify it base on your current needs on listening for worker's messages to act accordingly.

	class CronioSenderListener(stomp.ConnectionListener):
		def on_error(self, headers, message):
			# pprint.pprint(headers)
			# pprint.pprint(message)
			CS.logger_sender.debug('Cronio Sender Listener received an error "%s"' % message)
		def on_message(self, headers, message):
			# Use the below to your discretion on receiving new messages
			# CS.logger_sender.debug(' %s' % str(headers['message-id']))
			# CS.logger_sender.debug(' Log %s' % str(message))
			# CS.logger_sender.debug('ACK Log - Remove from Queue %s' % str(headers['message-id']))
			# MESSAGE IS IN JSON
			message_obj = json.loads(message)
			if headers['subscription'] == "api_log":
				pprint.pprint(message_obj)
			else:
				# a bunch of other messages
				print "view_log - or error"
			# remove from queue
			CS.conn.ack(headers['message-id'],1)


## Execute OS commands and pass a cmd_id (ID)

>Generate cmd_ids to use for each:

	cmd_ids = [str(uuid.uuid4()),str(uuid.uuid4()),str(uuid.uuid4()),str(uuid.uuid4()),str(uuid.uuid4()),str(uuid.uuid4())]
	pprint.pprint(cmd_ids)


>Execute a git command and get the result in the listener

	# Use those on the following commands:
	# git clone a repo
	CS.sendCMD("git clone https://gitlab.com/doctormo/python-crontab.git","os",cmd_ids[1])

>or just a simple listing

	#execute ls command on the current folder
	CS.sendCMD("ls","os",cmd_ids[2])
	

>Can send files if you want to execute those:

	# Absolute Path only
	PythonFile = "/opt/cronio/examples/test.py"
	CmdFile = "/opt/cronio/examples/test.sh"
	CS.sendPythonFile(PythonFile,1)
	CS.sendCmdFile(CmdFile,2)


	# Clear Database of its commands
	CS.sendCMD('cleardb','operation',cmd_ids[4])


>Use workflow to run on the worker.

	# Workflow Example - Set of commands related with each other.
	commands = [ {"cmd": "ls", "type": "os", "cmd_id": 1, "dependencies": None}, {"cmd": "mkdir test_1", "type": "os", "cmd_id": 2, "dependencies": None}, {"cmd": "cd test_1", "type": "os", "cmd_id": 3, "dependencies": [2]},{"cmd": "print \"hello cronio\"", "type": "python", "cmd_id": 4,"dependencies" : None}]
	CS.sendWorkflow(commands)



### ie.1
>Clone a repository for example

	sendCMD("git clone https://gitlab.com/doctormo/python-crontab.git","os",2)

### ie.2
>Do listing of files/folders 

	sendCMD("ls","os",2)

## Execute Python commands and pass a cmd_id (ID)

### ie.1
>Do a print in python

	sendCMD("print \"hello World\"","python",1)


### ie.2
>Do something more

	sendCMD("iter2=[2,3,4,5,6,7]\nfor item2 in iter2:\n\tprint item2","python",2)
