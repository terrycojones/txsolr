import unittest
from datetime import datetime, date

from txsolr.input import SimpleXMLInputFactory, escapeTerm


class EscapingTest(unittest.TestCase):

    def test_escapeTerm(self):
        terms = [(r'Hello*World', r'Hello\*World'),
                 (r'Hello "World"', r'Hello \"World\"'),
                 (r'Hello |&^"~*?', r'Hello \|\&\^\"\~\*\?'),
                 (r'Hello (World)', r'Hello \(World\)'),
                 (r'Hello World', r'Hello World'), ]

        for raw, escaped in terms:
            self.assertEqual(escapeTerm(raw), escaped)


class XMLInputTest(unittest.TestCase):

    def setUp(self):
        self.input = SimpleXMLInputFactory()

    def test_encodeValue(self):
        """
        Tests the Python value to XML value encoder
        """

        value = datetime(2010, 1, 1, 0, 0, 0)
        value = self.input._encodeValue(value)
        self.assertEqual(value, '2010-01-01T00:00:00Z')

        value = date(2010, 1, 1)
        value = self.input._encodeValue(value)
        self.assertEqual(value, '2010-01-01T00:00:00Z')

        value = True
        value = self.input._encodeValue(value)
        self.assertEqual(value, 'true')

        value = 'sample str'
        value = self.input._encodeValue(value)
        self.assert_(isinstance(value, unicode))

        value = None
        value = self.input._encodeValue(value)
        self.assert_(isinstance(value, unicode))

    def test_createAdd(self):
        """
        Tests the creation of add input for the request
        """

        document = {'id': 1, 'text': 'hello'}
        expected = ('<add><doc><field name="text">hello</field>'
                    '<field name="id">1</field></doc></add>')
        input = self.input.createAdd(document).body
        self.assertEqual(input, expected, 'Wrong input')

    def test_createAddWithCollection(self):

        document = {'id': 1, 'collection': [1, 2, 3]}
        expected = ('<add><doc><field name="id">1</field>'
                    '<field name="collection">1</field>'
                    '<field name="collection">2</field>'
                    '<field name="collection">3</field></doc></add>')

        input = self.input.createAdd(document).body
        self.assertEqual(input, expected, 'Wrong input')

    def test_createAddExceptions(self):

        self.assertRaises(AttributeError, self.input.createAdd, None)
        self.assertRaises(AttributeError, self.input.createAdd, 'string')


    def test_createAddWithOverwrite(self):
        document = {'id': 1, 'text': 'hello'}
        expected = ('<add overwrite="true">'
                    '<doc><field name="text">hello</field>'
                    '<field name="id">1</field></doc></add>')

        input = self.input.createAdd(document, overwrite=True).body
        self.assertEqual(input, expected, 'Wrong input')

    def test_createAddWithCommitWithin(self):
        document = {'id': 1, 'text': 'hello'}
        expected = ('<add commitWithin="80">'
                    '<doc><field name="text">hello</field>'
                    '<field name="id">1</field></doc></add>')

        input = self.input.createAdd(document, commitWithin=80).body
        self.assertEqual(input, expected, 'Wrong input')

    def test_createDelete(self):
        """
        Tests the creation fo delete input for the request
        """

        id = 123
        expected = '<delete><id>123</id></delete>'
        self.assertEqual(self.input.createDelete(id).body, expected)

    def test_createDeleteWithEncoding(self):

        id = '<hola>'
        expected = '<delete><id>&lt;hola&gt;</id></delete>'
        self.assertEqual(self.input.createDelete(id).body, expected)

    def test_createDeleteMany(self):

        id = [1, 2, 3]
        expected = '<delete><id>1</id><id>2</id><id>3</id></delete>'
        self.assertEqual(self.input.createDelete(id).body, expected)

    def test_commit(self):
        input = self.input.createCommit().body
        expected = '<commit />'
        self.assertEqual(input, expected)

    def test_commitWaitFlush(self):
        input = self.input.createCommit(waitFlush=True).body
        expected = '<commit waitFlush="true" />'
        self.assertEqual(input, expected)

    def test_commitWaitSearcher(self):
        input = self.input.createCommit(waitSearcher=True).body
        expected = '<commit waitSearcher="true" />'
        self.assertEqual(input, expected)

    def test_commitExpungeDeletes(self):
        input = self.input.createCommit(expungeDeletes=True).body
        expected = '<commit expungeDeletes="true" />'
        self.assertEqual(input, expected)

    def test_optimize(self):
        input = self.input.createOptimize().body
        expected = '<optimize />'
        self.assertEqual(input, expected)

    def test_optimizeWaitFlush(self):
        input = self.input.createOptimize(waitFlush=True).body
        expected = '<optimize waitFlush="true" />'
        self.assertEqual(input, expected)

    def test_optimizeWaitSearcher(self):
        input = self.input.createOptimize(waitSearcher=True).body
        expected = '<optimize waitSearcher="true" />'
        self.assertEqual(input, expected)

    def test_optimizeMaxSegments(self):
        input = self.input.createOptimize(maxSegments=2).body
        expected = '<optimize maxSegments="2" />'
        self.assertEqual(input, expected)
