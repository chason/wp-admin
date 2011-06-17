#!/usr/bin/python
"""
wp-admin.py
==============

Desc: Command line tool for managing WordPress installations

Author: Chason Chaffin <chason @ pinkrobot org>

License: GPL
"""

import random
import string
import MySQLdb
import re
import time
import logging
import optparse
import sys

class WPAdmin(object):
    """
    Main class for wp-admin
    """

    def __init__(self):
        """
        Just sets up the logger for now
        """
        self.logger = logging.getLogger("wpadmin")
        self.options = None

    def get_details(self, location):
        """
        Get database details from wp-config.php file

        @returns: list with database details
        """

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

    def dbconnect(self, details):
        """
        Connect to the database

        @returns: database cursor
        """

        db = MySQLdb.connect(user=details['DB_USER'], 
                passwd=details['DB_PASSWORD'], 
                host=details['DB_HOST'], 
                db=details['DB_NAME'])
        c = db.cursor()
        return c    

    def genpass(self, digits=8, chars=string.letters + string.digits):
        """
        Generate a random password

        @returns: random password
        """

        return ''.join([random.choice(chars) for i in xrange(digits)])

    def print_user_details(self, user):
        """
        Prints out user details
        
        @returns: 0
        """
        print("""
        User successfully created:
        Username: {name}
        Password: {passwd}
        Nicename: {name}
        Email: {email}
        """.format(name=user['name'], passwd=user['password'], 
                   email=user['email']))
        
        return 0

    def create_admin(self, db, details, **kargs): 
        """
        Creates a WordPress user with administrator permissions

        @returns: list with user details
        """
        user = {
            'name': 'tempadmin',
            'password': self.genpass(8),
            'nicename': 'tempadmin',
            'email': 'nobody@domain.com',
        }
        for key in kargs.keys():
            if kargs[key]:
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

    def delete_user(self, db, details, username):
        """
        Delete a user from WordPress database

        @returns: 0
        """

        uid_sql = """
            SELECT ID from {prefix}users WHERE user_login='{name}';
        """.format(prefix=details['table_prefix'], name=username)
        db.execute(uid_sql)
        try:
            uid, = db.fetchone()
        except TypeError:
            print("No user with username {0} found".format(username))
            return 1

        uid = int(uid)

        users_sql = """
            DELETE FROM {prefix}users WHERE ID={uid};
        """.format(prefix=details['table_prefix'], uid=uid)
        db.execute(users_sql)

        meta_sql = """
            DELETE FROM {prefix}usermeta WHERE user_id={uid};
        """.format(prefix=details['table_prefix'], uid=uid)
        db.execute(meta_sql)

        some_left = db.execute(uid_sql)
        if some_left:
            self.delete_user(db, details, username)
        
        return 0

    def set_log_level(self):
        """
        Set log level according to command-line options

        @returns: logger object
        """
        if self.options.debug:
            self.logger.setLevel(logging.DEBUG)
        elif self.options.quiet:
            self.logger.setLevel(logging.ERROR)
        else:
            self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())
        return self.logger

    def run(self):
        """
        Perform actions based on CLI options

        @returns status code
        """
        parser = setup_parser()
        (self.options, args) = parser.parse_args()
        logger = self.set_log_level()

        if (len(sys.argv) <= 2 or len(args) != 1):
            parser.print_help()
            return 2
        details = self.get_details(args[0])
        db = self.dbconnect(details)

        if self.options.add_admin:
            user = self.create_admin(db, details, name=self.options.user,
                    password=self.options.passwd, nicename=self.options.user,
                    email=self.options.email)
            self.print_user_details(user)
        if self.options.del_user:
            self.delete_user(db, details, self.options.user)
            print("All users with username '{0}' successfully deleted.".format(self.options.user))
        
def setup_parser():
    """
    Setup the optparser

    @returns: parser
    """
    usage = "usage: %prog [options] LOCATION"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("--debug", action="store_true",
        dest="debug", default=False, help=
        "Show debugging information.")
    parser.add_option("--quiet", action="store_true",
        dest="quiet", default=False, help=
        "Show less output.")
    parser.add_option("--add-admin", "-a", action="store_true", 
        dest="add_admin", default=False, help=
        "Add admin user. If no username is specified tempadmin will be used")
    parser.add_option("--del-user", "-d", action="store_true",
        dest="del_user", default=False, help=
        "Delete user. Username must be specified with -u option")
    parser.add_option("--user", "-u", action="store",
        dest="user", default=False, help=
        "Specify username for tasks that require it.")
    parser.add_option("--pass", "-p", action="store",
        dest="passwd", default=False, help=
        "Specify password for adding a user.")
    parser.add_option("--email", "-e", action="store",
        dest="email", default=False, help=
        "Specify email for adding a user.")

    return parser

def main():
    """
    Yeah!
    """
    wpadmin = WPAdmin()
    wpadmin.run()

if __name__ == '__main__':
    sys.exit(main())
