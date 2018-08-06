# cronio

INTRO

>This project has a sender and a receiver, the sender sends commands through RabbitMQ on the queue of a worker (receiver), the receiver executes them either with OS or Python2.7

## Objectives

- [x] Prototype - Send some commands in OS or in Python and execute them, bring back the log or errors if any
- [x] Package Structure
- [ ] Dependent Commands ie. cmd_dependancy: [1,2,3,200]
- [ ] Time to be executed ie. using python-crontab would be a good thing
- [ ] ENVs needs to be tested with docker that it can be set and read from this app.py
- [ ] Sender: Wait until all of your send cmds are executed and then leave.
- [ ] Worker: check if its the right binary to execute python2.7
- [ ] Run in other Languages ie. Ruby, Java, Cobol? Kidding..


## Requirements

1. STOMP Python Library 

	pip install -r requirements.txt 

or 

	pip install stomp-py

2. You will need to have a rabbitmq server with stomp

You can get one using our docker image - default username and password is guest.
If you want the dockerfile for it, you can go to the folder's repository myrabbitmq.

## Installation 

PyPi

	pip install cronio



## Examples

For Code see examples/ directory
	
Worker:

	python worker.py # this will start the process, see inline comments


Sender:

	python test1.py
	python test2.py 

## Execute OS commands and pass a cmd_id (ID)

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
