# MyRabbitMQ

> Creates a docker container with STOMP enabled, be sure to change the password of the guest (admin of RabbitMQ), is inside the env-file.txt.


## Use envfile for settings

	env-file.txt

## Make image

	docker build . -t myrabbitmq --force-rm

## How to run in background:

	docker run -d -p 15672:15672 -p 61613:61613 --restart always --env-file env-file.txt myrabbitmq

## Management Web

	http://localhost:15672/
