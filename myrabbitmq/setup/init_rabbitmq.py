import datetime, pprint, json, string, random
from pyrabbit.api import Client

AMQP_HOST_STOMP = "localhost:15672"
AMQP_VHOST = "/"
AMQP_API_USERNAME = "guest"
AMQP_API_PASSWORD = "guest"
DO_DELETE_ALL_USERS_EXCEPT_ADMIN = False # Delete old ones
	
if __name__ == "__main__":
	users = [
		{"username":"worker1", "password": "somepass", "tags": "cronio"},
		{"username":"worker2", "password": "somepass", "tags": "cronio"},
		{"username":"sender1", "password": "somepass", "tags": "cronio"}
	]

	cl = Client(AMQP_HOST_STOMP, AMQP_API_USERNAME, AMQP_API_PASSWORD)
	if cl.is_alive():

		if DO_DELETE_ALL_USERS_EXCEPT_ADMIN:
			UsersFoundInRabbitMQ = cl.get_users()
			for x in UsersFoundInRabbitMQ:
				pprint.pprint(x)
				if ("cronio") in x["tags"]:
					cl.delete_user(x["name"])
					print "User: "+x["name"] +" - Deleted"
		

			# if AMQP_VHOST in cl.get_vhost_names():
			# 	print "delete vhose: "
			# 	cl.delete_vhost(AMQP_VHOST)
		for user in users:
			print user

			cl.create_user(username=user["username"], password=user["password"], tags=user["tags"])
			# Not Secure to have access to all for rd and wr.
			cl.set_vhost_permissions(vname=AMQP_VHOST, username=user["username"], config=".*", rd=".*", wr=".*")