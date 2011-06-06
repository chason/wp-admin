#!/usr/bin/python
import re

# Methods for reading database information from WordPress and connecting to MySQL

def get_details(location):
    details = {}
    wpconfig = location + '/wp-config.php'
    try:
        wpconfig = open(wpconfig, 'r')
    except IOError as e:
        print("({0})".format(e))
    
    pattern = re.compile('''define\('(?P<name>[A-Za-z_0-9]+)',\s?'(?P<value>[^\']+)'\);''')
    for line in wpconfig:
        match = pattern.search(line)
        if match:
            details.update({match.group('name'): match.group('value')})
    wpconfig.close()
    return details

