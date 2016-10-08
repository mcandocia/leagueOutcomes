from dbinfo import *
import os


def main():
	try:
		os.system('python insert_static.py')
		print 'updated static information'
	except:
		print 'no static update'
	os.system('python assign_match_version.py')
	print 'assigned match versions'
	os.system('''export PGPASSWORD="%s";
			psql -U %s -d %s -a -f dbcleaning.sql 
			-h %s -p %d''' % (password, user, database, host, port))
	print 'ran remainder of sql cleaning'

if __name__=='__main__':
	main()