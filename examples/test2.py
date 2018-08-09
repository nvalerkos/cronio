import sys,os,json

original = {
	'comment': 'complex data structure we would ideally want in there',
	'ie.1' : {
		'key': 'is value bla bla', 'value' : [1,2,3,4,5,6,7,10011]
	},
	'ie.2' : {
		'key': 'is value bla bla', 'value' : [1,2,3,4,5,6,7,10011]
	},
	'ie.3' : {
		'key': 'is value bla bla', 'value' : [1,2,3,4,5,6,7,10011]
	}
}


if len(sys.argv) > 1:
	data = sys.argv[1]
	content = json.loads(data.decode('hex'))
else:
	print "exit - no arguements"
	exit()

print content == original