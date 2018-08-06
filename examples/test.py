import os,sys
import pip
import pprint

print(sys.version)

mylist = ['x', 3, 'b']
print '[%s]' % ', '.join(map(str, mylist))