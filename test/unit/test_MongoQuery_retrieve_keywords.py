from __future__ import print_function
from builtins import str
from builtins import range
import pymongo
import subprocess
import tempfile
import shutil
import unittest
import os
import time
import sys
import json
from bson.objectid import ObjectId
# Get src directory and put it in path
# To get import forking for MongoDBLibrary

ROOT_DIR = os.path.dirname(os.path.abspath('..'))
SRC_DIR = os.path.join(ROOT_DIR, "src")
sys.path.insert(0, SRC_DIR)

# Suppress logging from MongoDBLibrary
f = open(os.devnull, 'w')
sys.stdout = f

# settings for unit test
test_mongo_connection_host = 'localhost'
test_mongo_connection_port = 51000
test_database_name = 'test_database'
test_collection_name = 'test_collection'
# Data for unit tests
data1 = {"firstName": "John", "lastName": "Smith", "age": 25,
         "address": {"streetAddress": "21 2nd Street", "city": "New York", "state": "NY", "postalCode": 10021},
         "phoneNumbers": [{"type": "home", "number": "212 555-1234"}, {"type": "fax", "number": "646 555-4567"}]}
data2 = {"firstName": "John", "lastName": "Wayne", "age": 99}
data3 = {"firstName": "Clark", "lastName": "Kent", "age": 81}
data4 = {"firstName": "Clark", "lastName": "Kent", "age": 81,
         "address": {"streetAddress": "21 2nd Street", "city": "Metropolis", "state": "NA", "postalCode": 10021},
         "phoneNumbers": [{"type": "home", "number": "919 555-1234"}, {"type": "fax", "number": "919 555-4567"}]}
selection1 = '{"firstName": "John"}'

from MongoDBLibrary import MongoDBLibrary


class TestMongoDBLibrary(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self._tmpdir = tempfile.mkdtemp()
        self._process = subprocess.Popen(['mongod', '--bind_ip', test_mongo_connection_host,
                                          '--port', str(test_mongo_connection_port),
                                          '--dbpath', self._tmpdir,
                                          '--nojournal', '--nohttpinterface',
                                          '--noauth', '--smallfiles',
                                          '--syncdelay', '0',
                                          '--maxConns', '10',
                                          '--nssize', '1', ],
                                         stdout=open(os.devnull, 'wb'),
                                         stderr=subprocess.STDOUT)
        # Mongo is super fast but
        # Wait for database connection
        for i in range(5):
            time.sleep(0.1)
            try:
                self._conn = pymongo.MongoClient(test_mongo_connection_host, test_mongo_connection_port)
            except pymongo.errors.ConnectionFailure:
                continue
            else:
                break
        else:
            self.tearDown()
            assert False, 'Cannot connect to the mongodb test instance'

    def test_retrieve_all_mongodb_records_when_multiple_documents(self):
        self.mongo_create_db()
        self.mongo_inser_data(data2)
        self.mongo_inser_data(data3)

        a = MongoDBLibrary()
        a.connect_to_mongodb(dbHost=test_mongo_connection_host, dbPort=test_mongo_connection_port)
        data = a.retrieve_all_mongodb_records(dbName=test_database_name, dbCollName=test_collection_name)
        a.disconnect_from_mongodb()

        expected = self.mongo_find_from_collection()
        self.assertEqual(data, expected)

    def test_retrieve_all_mongodb_records_when_one_document(self):
        self.mongo_create_db()
        self.mongo_inser_data(data2)

        a = MongoDBLibrary()
        a.connect_to_mongodb(dbHost=test_mongo_connection_host, dbPort=test_mongo_connection_port)
        data = a.retrieve_all_mongodb_records(dbName=test_database_name, dbCollName=test_collection_name)
        a.disconnect_from_mongodb()

        expected = self.mongo_find_from_collection()
        self.assertEqual(data, expected)

    def test_retrieve_all_mongodb_records_when_zero_documents(self):
        self.mongo_create_db()

        a = MongoDBLibrary()
        a.connect_to_mongodb(dbHost=test_mongo_connection_host, dbPort=test_mongo_connection_port)
        data = a.retrieve_all_mongodb_records(dbName=test_database_name, dbCollName=test_collection_name)
        a.disconnect_from_mongodb()

        expected = ''
        self.assertEqual(data, expected)

    def test_retrieve_all_mongodb_records_when_collection_does_not_exist(self):
        self.mongo_create_db()
        self.mongo_inser_data(data2)

        a = MongoDBLibrary()
        a.connect_to_mongodb(dbHost=test_mongo_connection_host, dbPort=test_mongo_connection_port)
        data = a.retrieve_all_mongodb_records(dbName=test_database_name, dbCollName='not_exist')
        a.disconnect_from_mongodb()

        expected = ''
        self.assertEqual(data, expected)

    def test_retrieve_all_mongodb_records_when_database_does_not_exist(self):
        self.mongo_create_db()
        self.mongo_inser_data(data2)

        a = MongoDBLibrary()
        a.connect_to_mongodb(dbHost=test_mongo_connection_host, dbPort=test_mongo_connection_port)
        data = a.retrieve_all_mongodb_records(dbName='no-database', dbCollName='not_exist')
        a.disconnect_from_mongodb()

        expected = ''
        self.assertEqual(data, expected)

    def test_retrieve_some_mongodb_records_when_multiple_documents(self):
        self.mongo_create_db()
        self.mongo_inser_data(data2)
        self.mongo_inser_data(data3)

        a = MongoDBLibrary()
        a.connect_to_mongodb(dbHost=test_mongo_connection_host, dbPort=test_mongo_connection_port)
        data = a.retrieve_some_mongodb_records(dbName=test_database_name, dbCollName=test_collection_name,
                                               recordJSON=selection1)
        a.disconnect_from_mongodb()

        expected = self.mongo_find_from_collection(record=selection1)
        self.assertEqual(data, expected)

    def test_retrieve_mongodb_records_with_desired_fields_when_one_document_in_db(self):
        self.mongo_create_db()
        self.mongo_inser_data(data1)

        field = 'address.postalCode, address.city'
        a = MongoDBLibrary()
        a.connect_to_mongodb(dbHost=test_mongo_connection_host, dbPort=test_mongo_connection_port)
        data = a.retrieve_mongodb_records_with_desired_fields(dbName=test_database_name,
                                                              dbCollName=test_collection_name, recordJSON='{}',
                                                              fields=field, return__id=False)
        a.disconnect_from_mongodb()
        data = self.cleanup_and_sort(data)
        expected = [(u'address', [(u'city', u'New York'), (u'postalCode', 10021)])]
        self.assertIn(expected, data)

    def test_retrieve_mongodb_records_with_desired_fields_when_multiple_documents_in_db(self):
        self.mongo_create_db()
        self.mongo_inser_data(data1)
        self.mongo_inser_data(data4)

        field = 'address.postalCode, address.city'
        a = MongoDBLibrary()
        a.connect_to_mongodb(dbHost=test_mongo_connection_host, dbPort=test_mongo_connection_port)
        data = a.retrieve_mongodb_records_with_desired_fields(dbName=test_database_name,
                                                              dbCollName=test_collection_name, recordJSON='{}',
                                                              fields=field, return__id=False)
        a.disconnect_from_mongodb()

        data = self.cleanup_and_sort(data)
        expected_1 = [(u'address', [(u'city', u'New York'), (u'postalCode', 10021)])]
        expected_2 = [(u'address', [(u'city', u'Metropolis'), (u'postalCode', 10021)])]
        self.assertIn(expected_1, data)
        self.assertIn(expected_2, data)

    def test_retrieve_mongodb_records_with_desired_fields_when_fields_is_empty(self):
        self.mongo_create_db()
        self.mongo_inser_data(data1)
        self.mongo_inser_data(data4)

        a = MongoDBLibrary()
        a.connect_to_mongodb(dbHost=test_mongo_connection_host, dbPort=test_mongo_connection_port)
        data = a.retrieve_mongodb_records_with_desired_fields(dbName=test_database_name,
                                                              dbCollName=test_collection_name, recordJSON='{}',
                                                              fields='', return__id=False)
        a.disconnect_from_mongodb()

        data = self.cleanup_and_sort(data)
        expected1 = [(u'address', [(u'city', u'New York'), (u'postalCode', 10021), (u'state', u'NY'), (u'streetAddress', u'21 2nd Street')]),
                      (u'age', 25),
                      (u'firstName', u'John'),
                      (u'lastName', u'Smith'),
                      (u'phoneNumbers', [[(u'number', u'212 555-1234'), (u'type', u'home')],
                                         [(u'number', u'646 555-4567'), (u'type', u'fax')]])]
        expected2 = [(u'address', [(u'city', u'Metropolis'), (u'postalCode', 10021), (u'state', u'NA'), (u'streetAddress', u'21 2nd Street')]),
                     (u'age', 81),
                     (u'firstName', u'Clark'),
                     (u'lastName', u'Kent'),
                     (u'phoneNumbers', [[(u'number', u'919 555-1234'), (u'type', u'home')],
                                        [(u'number', u'919 555-4567'), (u'type', u'fax')]])]

        self.assertIn(expected1, data)
        self.assertIn(expected2, data)

    def test_retrieve_mongodb_records_with_desired_fields__id_is_returned(self):
        self.mongo_create_db()
        self.mongo_inser_data(data1)
        self.mongo_inser_data(data4)

        field = 'address.postalCode, address.city'
        a = MongoDBLibrary()
        a.connect_to_mongodb(dbHost=test_mongo_connection_host, dbPort=test_mongo_connection_port)
        data = a.retrieve_mongodb_records_with_desired_fields(dbName=test_database_name,
                                                              dbCollName=test_collection_name, recordJSON='{}',
                                                              fields=field, return__id=True)
        a.disconnect_from_mongodb()

        expected = "'_id', ObjectId('"
        self.assertIn(expected, data)

    def test_retrieve_mongodb_records_with_desired_fields_when_searhing_a_record(self):
        self.mongo_create_db()
        self.mongo_inser_data(data1)
        self.mongo_inser_data(data4)

        field = 'address.postalCode, address.city'
        a = MongoDBLibrary()
        a.connect_to_mongodb(dbHost=test_mongo_connection_host, dbPort=test_mongo_connection_port)
        data = a.retrieve_mongodb_records_with_desired_fields(dbName=test_database_name,
                                                              dbCollName=test_collection_name, recordJSON=selection1,
                                                              fields=field, return__id=False)
        a.disconnect_from_mongodb()

        data = self.cleanup_and_sort(data)

        expected = [(u'address', [(u'city', u'New York'), (u'postalCode', 10021)])]
        self.assertIn(expected, data)

    def test_retrieve_mongodb_records_with_desired_fields_when_return__id_is_not_boolean(self):
        self.mongo_create_db()
        self.mongo_inser_data(data1)
        self.mongo_inser_data(data4)

        field = 'address.postalCode, address.city'
        a = MongoDBLibrary()
        a.connect_to_mongodb(dbHost=test_mongo_connection_host, dbPort=test_mongo_connection_port)
        data = a.retrieve_mongodb_records_with_desired_fields(dbName=test_database_name,
                                                              dbCollName=test_collection_name, recordJSON=selection1,
                                                              fields=field, return__id='foobar')
        a.disconnect_from_mongodb()

        data = self.cleanup_and_sort(data)

        expected = [(u'address', [(u'city', u'New York'), (u'postalCode', 10021)])]

        self.assertIn(expected, data)

    def tearDown(self):
        # Terminate Mongodb process
        if self._process:
            self._process.terminate()
            self._process.wait()
            self._process = None
            shutil.rmtree(self._tmpdir, ignore_errors=True)

    def cleanup_and_sort(self, data):
        data = data.replace('][', '],[')
        data = '[' + data + ']'
        data = eval(data)
        data = [dict(x) for x in data]

        for element in data:
            if '_id' in element:
                del element['_id']
            element['address'] = sorted(element['address'].items())
            if 'phoneNumbers' in element:
                element['phoneNumbers'] = sorted([sorted(e.items()) for e in element['phoneNumbers']])
        for i in range(0, len(data)):
            data[i] = sorted(data[i].items())
        return data

    def mongo_create_db(self, db=test_database_name, collection=test_collection_name):
        test_db = self._conn[db]
        self._collection = test_db[collection]

    def mongo_drop_database(self, db=test_database_name):
        self._conn.drop_database(db)

    def mongo_inser_data(self, data):
        self._collection.insert(data)

    def mongo_database_names(self, db=test_database_name, collection=test_collection_name):
        return self._conn.database_names()

    def mongo_find_from_collection(self, db=test_database_name, collection=test_collection_name, record='{}',
                                   projection=[]):
        data = ''
        for item in self._collection.find(dict(json.loads(record))):
            print(item)
            data = '%s%s' % (data, list(item.items()))
        return data


if __name__ == '__main__':
    unittest.main()
