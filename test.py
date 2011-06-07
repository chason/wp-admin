#!/usr/bin/python

import db
import unittest

class TestDB(unittest.TestCase):
    
    sample_details = {
            'DB_NAME': 'testname',
            'DB_USER': 'testuser',
            'DB_PASSWORD': 'testpass',
            'DB_HOST': 'testhost',
            'DB_CHARSET': 'utf8',
            'DB_COLLATE': '',
            'table_prefix': 'wp_',
        }

    def test_get_details(self):
        details = db.get_details('.')
        self.failUnlessEqual(details,self.sample_details)  

if __name__ == '__main__':
    unittest.main()
