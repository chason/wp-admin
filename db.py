#!/usr/bin/python
import MySQLdb
import re

# Methods for reading database information from WordPress and connecting to MySQL

def get_details(location):
    details = {}
    wpconfig = location + '/wp-config.php'
    try:
        wpconfig = open(wpconfig, 'r')
    except IOError as e:
        print("({0})".format(e))
    
    pattern = re.compile('''define\('(?P<name>[A-Za-z_0-9]+)',\s?'(?P<value>[^\']*)'\);''')
    pattern2 = re.compile('''\$table_prefix\s*=\s*'(?P<value>[^\']*)';''')
    for line in wpconfig:
        match = pattern.search(line)
        if match:
            details.update({match.group('name'): match.group('value')})
        else:
            match = pattern2.search(line)
            if match:
                details.update({'table_prefix': match.group('value')})
    wpconfig.close()
    return details

def connect(database, dbuser, dbpass, prefix):
    db = MySQLdb.connect(user=dbuser, passwd=dbpass)
    c = db.cursor()
    sql = "SELECT option_name,option_value from {0}.{1}options where option_name='siteurl';".format(database,prefix)
    try:
	c.execute(sql) 
    return c
