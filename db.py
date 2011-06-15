#!/usr/bin/python
import random
import string
import MySQLdb
import re
import time

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

def dbconnect(details):
    db = MySQLdb.connect(user=details['DB_USER'], passwd=details['DB_PASSWORD'], host=details['DB_HOST'], db=details['DB_NAME'])
    c = db.cursor()
    return c    

def genpass(digits=8, chars=string.letters + string.digits):
    return ''.join([random.choice(chars) for i in xrange(digits)])

def create_admin(db, details, **kargs): 
    user = {
        'name': 'tempadmin',
        'password': genpass(8),
        'nicename': 'tempadmin',
        'email': 'nobody@domain.com',
    }
    for key in kargs.keys():
        user.update({key: kargs[key]})
        
    users_sql = """
    INSERT INTO {prefix}users SET 
        user_login='{name}',
        user_pass=md5('{password}'), 
        user_nicename='{nicename}',
        user_email='{email}', 
        user_registered='{date}', 
        user_status='0',
        display_name='{nicename}';
    """.format(prefix=details['table_prefix'], name=user['name'],
            password=user['password'], nicename=user['nicename'], 
            email=user['email'], date=time.strftime("%Y-%m-%d %H:%M:%S"))

    users_sql2 = """
    SELECT ID from {prefix}users WHERE user_login='{name}';
    """.format(prefix=details['table_prefix'], name=user['name'])

    db.execute(users_sql)
    db.execute(users_sql2)
    uid, = db.fetchone()
    uid = int(uid)

    meta_sql = """
    INSERT INTO {prefix}usermeta SET
        user_id='{uid}',
        meta_key='wp_capabilities',
        meta_value='a:1:{{s:13:"administrator";b:1;}};'
    """.format(prefix=details['table_prefix'], uid=uid)

    meta_sql2 = """
    INSERT INTO {prefix}usermeta SET
        user_id='{uid}',
        meta_key='wp_user_level',
        meta_value='10';
    """.format(prefix=details['table_prefix'], uid=uid)

    db.execute(meta_sql)
    db.execute(meta_sql2)

    user.update({'uid': uid})

    return user

def delete_user(db, details, username):
    uid_sql = """
    SELECT ID from {prefix}users WHERE user_login='{name}';
    """.format(prefix=details['table_prefix'], name=username)
    db.execute(uid_sql)
    uid, = db.fetchone()
    uid = int(uid)

    users_sql = """
    DELETE FROM {prefix}users WHERE ID={uid};
    """.format(prefix=details['table_prefix'], uid=uid)
    db.execute(users_sql)

    meta_sql = """
    delete FROM {prefix}usermeta WHERE user_id={uid};
    """.format(prefix=details['table_prefix'], uid=uid)
    db.execute(meta_sql)

    some_left = db.execute(uid_sql)
    if some_left:
        delete_user(db, details, username)

