# -*- coding: utf-8 -*-
import random
import string
import datetime

from twisted.trial import unittest
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, Deferred

from txsolr.client import SolrClient


# TODO: Add tests for exceptions.
# FIXME: avoid hardcoded url
SOLR_URL = 'http://localhost:8983/solr/'


def _randomString(size):
    return ''.join(random.choice(string.letters) for _ in range(size))


class AddingDocumentsTestCase(unittest.TestCase):

    def setUp(self):
        self.client = SolrClient(SOLR_URL)

    @inlineCallbacks
    def testAddOneDocument(self):
        """L{SolrClient.add} adds one document to the index."""
        doc = {'id': _randomString(20)}

        yield self.client.add(doc)
        yield self.client.commit()

        r = yield self.client.search('id:%s' % doc['id'])

        self.assertEqual(r.results.numFound, 1,
                         "Added document not found in the index")

        self.assertEqual(r.results.docs[0]['id'], doc['id'],
                         "Found ID does not match with added document")

    @inlineCallbacks
    def testAddWithoutOverwrite(self):
        """
        L{SolrClient.add} does not overwrite documents if the C{overwrite}
        parameter is C{False}.
        """
        initialId = _randomString(20)
        initialName = _randomString(20)
        newName = _randomString(20)

        doc = {'id': initialId,
               'name': initialName}

        yield self.client.add(doc)
        yield self.client.commit()

        doc = {'id': initialId,
               'name': newName}

        yield self.client.add(doc, overwrite=False)
        yield self.client.commit()

        r = yield self.client.search('id:%s' % doc['id'])

        self.assertNotEqual(r.results.docs[0]['name'], newName,
                            'Overwrite option did not work')

        self.assertEqual(r.results.docs[0]['name'], initialName,
                         'Overwrite option did not work')

    @inlineCallbacks
    def testAddWithCommitWithin(self):
        """
        L{SolrClient.add} commits the changes within the given time if the
        C{commitWithin} argument is C{True}.
        """

        def wait(milliseconds):
            d = Deferred()
            reactor.callLater(milliseconds / 1000.0, d.callback, None)
            return d

        doc = {'id': _randomString(20)}

        yield self.client.add(doc, commitWithin=1000)

        r = yield self.client.search('id:%s' % doc['id'])

        self.assertEqual(r.results.numFound, 0,
                         "Comitted immediately")

        yield wait(2000)  # give extra time to the commit operation

        r = yield self.client.search('id:%s' % doc['id'])

        self.assertEqual(r.results.numFound, 1,
                         "Operation was not commited")

    @inlineCallbacks
    def testAddOneDocumentMultipleFields(self):
        """L{SolrClient.add} add multiple documents with multiple fields."""
        name = _randomString(20)
        links = [_randomString(20) for _ in range(5)]

        for seq in (list, tuple, set):
            doc = {'id': _randomString(20),
                   'name': name,
                   'title': _randomString(20),
                   'links': seq(links)}

            yield self.client.add(doc)

        yield self.client.commit()

        r = yield self.client.search('name:%s' % name)

        self.assertEqual(r.results.numFound, 3,
                         "Did not get expected results")

        for doc in r.results.docs:
            self.assertTrue(doc['links'], links)

    @inlineCallbacks
    def testAddManyDocuments(self):
        """L{SolrClient.add} adds multiple documents to the index."""
        name = _randomString(20)

        docs = []
        for _ in range(5):
            doc = {'id': _randomString(20),
                   'name': name,
                   'title': [_randomString(20)]}
            docs.append(doc)

        yield self.client.add(docs)
        yield self.client.commit()

        r = yield self.client.search('name:%s' % name)

        self.assertEqual(r.results.numFound, len(docs),
                         'Document was not added')

    @inlineCallbacks
    def testAddUnicodeDocument(self):
        """L{SolrClient.add} adds documents with unicode characters."""
        doc = {'id': _randomString(20),
               'title': [u'カカシ外伝～戦場のボーイズライフ ☝☜']}

        yield self.client.add(doc)
        yield self.client.commit()

        r = yield self.client.search('id:%s' % doc['id'])

        self.assertEqual(r.results.docs[0]['title'], doc['title'],
                         "Unicode value does not match with found document")

    @inlineCallbacks
    def testAddDocumentWithNoneField(self):
        """L{SolrClient.add} adds documents with C{None} fields."""
        doc = {'id': _randomString(20),
               'title': None}

        yield self.client.add(doc)
        yield self.client.commit()

        r = yield self.client.search('id:%s' % doc['id'])

        self.assertFalse('title' in r.results.docs[0])

    @inlineCallbacks
    def testAddDocumentWithDatetime(self):
        """L{SolrClient.add} adds documents with C{datetime} fields."""
        # NOTE: Microseconds are ignored by Solr
        doc = {'id': _randomString(20),
               'test1_dt': datetime.datetime(2010, 1, 1, 23, 59, 59, 999),
               'test2_dt': datetime.date(2010, 1, 1)}

        yield self.client.add(doc)
        yield self.client.commit()

        r = yield self.client.search('id:%s' % doc['id'])

        doc = r.results.docs[0]

        # FIXME: dates proably should be parsed to datetime objects
        self.assertEqual(doc['test1_dt'], u'2010-01-01T23:59:59Z',
                         'Datetime value does not match')
        self.assertEqual(doc['test2_dt'], u'2010-01-01T00:00:00Z',
                         'Date value does not match')

    @inlineCallbacks
    def testUpdateOneDocument(self):
        """L{SolrClient.add} updates one document."""
        data = _randomString(20)
        updated_data = _randomString(20)

        doc = {'id': _randomString(20),
               'test_s': data}

        # add initial data
        yield self.client.add(doc)
        yield self.client.commit()

        # update data
        doc['test_s'] = updated_data
        yield self.client.add(doc)
        yield self.client.commit()

        r = yield self.client.search('id:%s' % doc['id'])
        self.assertEqual(r.results.docs[0]['test_s'], updated_data,
                         'Update did not work')

    @inlineCallbacks
    def testUpdateManyDocuments(self):
        """L{SolrClient.add} updates many documents."""
        data = _randomString(20)
        updated_data = _randomString(20)

        docs = []
        for _ in range(5):
            doc = {'id': _randomString(20),
                   'test_s': data}
            docs.append(doc)

        # add initial data
        yield self.client.add(docs)
        yield self.client.commit()

        # update data
        for doc in docs:
            doc['test_s'] = updated_data

        yield self.client.add(docs)
        yield self.client.commit()

        for doc in docs:
            r = yield self.client.search('id:%s' % doc['id'])
            self.assertEqual(r.results.docs[0]['test_s'], updated_data,
                             'Multiple update did not work')


class DeletingDocumentsTestCase(unittest.TestCase):

    def setUp(self):
        self.client = SolrClient(SOLR_URL)

    @inlineCallbacks
    def testDeleteOneDocumentByID(self):
        """L{SolrClient.delete} removes a document with the given id."""
        doc = {'id': _randomString(20),
               'name': _randomString(20)}

        # Fist add the document
        yield self.client.add(doc)
        yield self.client.commit()

        # Next delete the document
        yield self.client.delete(doc['id'])
        yield self.client.commit()

        r = yield self.client.search('id:%s' % doc['id'])
        self.assertEqual(r.results.numFound, 0,
                         "The document was not deleted")

        r = yield self.client.search('name:%s' % doc['name'])
        self.assertEqual(r.results.numFound, 0,
                         "The document was not deleted")

    @inlineCallbacks
    def testDeleteManyDocumentsByID(self):
        """L{SolrClient.delete} removes many document with the given ids."""
        name = _randomString(20)

        docs = []
        for _ in range(5):
            doc = {'id': _randomString(20),
                   'name': name}
            docs.append(doc)

        # Add the documents
        yield self.client.add(docs)
        yield self.client.commit()

        # Delete the documents
        ids = [doc['id'] for doc in docs]
        yield self.client.delete(ids)
        yield self.client.commit()

        r = yield self.client.search('name:%s' % name)
        self.assertEqual(r.results.numFound, 0,
                         'Document was not deleted')

        for doc in docs:
            r = yield self.client.search('id:%s' % doc['id'])
            self.assertEqual(r.results.numFound, 0,
                             'Document was not deleted')

    @inlineCallbacks
    def testDeleteOneDocumentByQuery(self):
        """
        L{SolrClient.deleteByQuery} removes one document matching the given
        query.
        """
        doc = {'id': _randomString(20),
               'name': _randomString(20)}

        # Fist add the document
        yield self.client.add(doc)
        yield self.client.commit()

        # Next delete the document
        yield self.client.deleteByQuery('id:%s' % doc['id'])
        yield self.client.commit()

        r = yield self.client.search('id:%s' % doc['id'])

        self.assertEqual(r.results.numFound, 0,
                         "The document was not deleted")

        r = yield self.client.search('name:%s' % doc['name'])

        self.assertEqual(r.results.numFound, 0,
                         "The document was not deleted")

    def testDeleteManyDocumentsByQuery(self):
        """
        L{SolrClient.deleteByQuery} removes all documents matching the given
        query.
        """
        name = _randomString(20)

        docs = []
        for _ in range(5):
            doc = {'id': _randomString(20),
                   'name': name}
            docs.append(doc)

        # Add the documents
        yield self.client.add(docs)
        yield self.client.commit()

        # Delete the documents
        yield self.client.deleteByQuery('name:%s' % name)
        yield self.client.commit()

        r = yield self.client.search('name:%s' % name)
        self.assertEqual(r.results.numFound, 0,
                         'Document was not deleted')

        for doc in docs:
            r = yield self.client.search('id:%s' % doc['id'])
            self.assertEqual(r.results.numFound, 0,
                             'Document was not deleted')


class QueryingDocumentsTestCase(unittest.TestCase):

    @inlineCallbacks
    def setUp(self):
        self.client = SolrClient(SOLR_URL)

        # Test documents used for querying
        self.narutoId = _randomString(20)
        self.bleachId = _randomString(20)
        self.deathnoteId = _randomString(20)

        self.documents = [
            {'id': self.narutoId,
             'title':  u'Naruto',
             'links': ['http://en.wikipedia.org/wiki/Naruto'],
             'category': 'action comedy drama fantasy',
             'popularity': 10,
             'info_t': (u'Naruto (NARUTO—ナルト—?, romanized as NARUTO) '
                        u'is an ongoing Japanese manga series written '
                        u'and illustrated by Masashi Kishimoto. The '
                        u'plot tells the story of Naruto Uzumaki, '
                        u'an adolescent ninja who constantly searches '
                        u'for recognition and aspires to become a Hokage, '
                        u'the ninja in his village that is acknowledged '
                        u'as the leader and the strongest of all.')},

            {'id': self.bleachId,
             'title':  u'Bleach',
             'category': 'action comedy drama supernatural',
             'links': ['http://en.wikipedia.org/wiki/Bleach_(manga)'],
             'popularity': 7,
             'info_t': (u'Bleach (ブリーチ Burīchi?, Romanized as BLEACH '
                        u'in Japan) is a Japanese manga series written '
                        u'and illustrated by Tite Kubo. Bleach follows '
                        u'the adventures of Ichigo Kurosaki after he '
                        u'obtains the powers of a Soul Reaper - a death '
                        u'personification similar to the Grim Reaper - '
                        u'from Rukia Kuchiki.')},

             {'id': self.deathnoteId,
             'title':  u'Death Note',
             'category': 'drama mystery psychological supernatural thriller',
             'links': ['http://en.wikipedia.org/wiki/Death_Note'],
             'popularity': 8,
             'info_t': (u'Death Note (デスノート Desu Nōto?) is a manga '
                        u'series created by writer Tsugumi Ohba and '
                        u'manga artist Takeshi Obata. The main character '
                        u'is Light Yagami, a high school student who '
                        u'discovers a supernatural notebook, the "Death '
                        u'Note", dropped on Earth by a death god '
                        u'named Ryuk.')},
        ]

        yield self.client.add(self.documents)
        yield self.client.commit()

    @inlineCallbacks
    def testSimpleQuery(self):
        """L{SolrClient.search} resolves a simple query."""
        r = yield self.client.search('title:Bleach OR title:"Death Note"')

        self.assertEqual(r.results.numFound, 2,
                         'Wrong numFound after query')

        for doc in r.results.docs:
            self.assertTrue(doc['id'] in (self.bleachId, self.deathnoteId),
                            'Document found does not match with added one')

    @inlineCallbacks
    def testUnicodeQuery(self):
        """L{SolrClient.search} resolves queries with unicode characters."""

        r = yield self.client.search(u'info_t:ブリーチ')

        self.assertEqual(r.results.numFound, 1,
                         'Wrong numFound after query')

        doc = r.results.docs[0]
        self.assertEqual(doc['id'], self.bleachId,
                        'Document found does not match with added one')

    @inlineCallbacks
    def testSearchWithUnicodeArguments(self):
        """
        L{SolrClient.search} accepts query arguments such as filter query.
        """
        r = yield self.client.search('*:*', fq=u'info_t:ブリーチ')

        self.assertEqual(r.results.numFound, 1,
                         'Wrong numFound after query')

        doc = r.results.docs[0]
        self.assertEqual(doc['id'], self.bleachId,
                        'Document found does not match with added one')

    @inlineCallbacks
    def testQueryWithFields(self):
        """
        L{SolrClient.search} shows which field to show in the result C{dict}.
        """

        # Fist test query with a single field
        r = yield self.client.search('info_t:manga', fl='links')
        for doc in r.results.docs:
            self.assertTrue('links' in doc,
                           'Results do not have specified field')

            self.assertFalse('id' in doc,
                             'Results have unrequested fields')

            self.assertFalse('info_t' in doc,
                             'Results have unrequested fields')

            self.assertFalse('popularity' in doc,
                             'Results have unrequested fields')

        # Test query with multiple fields
        r = yield self.client.search('info_t:manga', fl='links,popularity')
        for doc in r.results.docs:
            self.assertTrue('links' in doc,
                           'Results do not have specified field')

            self.assertFalse('id' in doc,
                             'Results have unrequested fields')

            self.assertFalse('info_t' in doc,
                             'Results have unrequested fields')

            self.assertTrue('popularity' in doc,
                             'Results do not have specified field')

        # Test query with all fields
        r = yield self.client.search('info_t:manga', fl='*')
        for doc in r.results.docs:
            self.assertTrue('links' in doc,
                            'Results do not have specified field')

            self.assertTrue('id' in doc,
                            'Results do not have specified field')

            self.assertTrue('info_t' in doc,
                            'Results do not have specified field')

            self.assertTrue('popularity' in doc,
                            'Results do not have specified field')

    @inlineCallbacks
    def testQueryWithScore(self):
        """L{SolrClient.search} shows the score of the results."""
        r = yield self.client.search('info_t:manga', fl='id,score')
        for doc in r.results.docs:
            self.assertTrue('id' in doc,
                           'Results do not have ID field')

            self.assertTrue('score' in doc,
                           'Results do not have score')

    # TODO: poor test. Improve it
    @inlineCallbacks
    def testQueryWithHighlight(self):
        """L{SolrClient.search} shows highlighting."""
        r = yield self.client.search('info_t:manga',
                                     hl='true',
                                     hl_fl='info_t')

        self.assertTrue(hasattr(r, 'highlighting'))

    @inlineCallbacks
    def testQueryWithSort(self):
        """L{SolrClient.search} shows sorted results."""
        r = yield self.client.search('info_t:manga', sort='popularity desc')
        docs = r.results.docs

        self.assertEqual(docs[0]['id'], self.narutoId,
                         'Wrong sorting order')

        self.assertEqual(docs[1]['id'], self.deathnoteId,
                         'Wrong sorting order')

        self.assertEqual(docs[2]['id'], self.bleachId,
                         'Wrong sorting order')

    # TODO: poor test. Improve it
    @inlineCallbacks
    def testQueryWithFacet(self):
        """L{SolrClient.search} shows facets."""
        # field facet
        r = yield self.client.search('info_t:manga', facet='true',
                                     facet_field='category')

        category_facet = r.facet_counts['facet_fields']['category']

        self.assertEqual(len(category_facet), 16, 'Unexpected facet')

        # query facet
        # FIXME: current api does not allow multiple facet queries or fields
        r = yield self.client.search('info_t:manga', facet='true',
                                     facet_query='popularity:[0 TO 8]')

        facet_queries = r.facet_counts['facet_queries']

        self.assertEqual(len(facet_queries), 1, 'Unexpected facet')

    @inlineCallbacks
    def tearDown(self):
        ids = [doc['id'] for doc in self.documents]

        yield self.client.delete(ids)
        yield self.client.commit()


class CommitingTestCase(unittest.TestCase):

    def setUp(self):
        self.client = SolrClient(SOLR_URL)

    @inlineCallbacks
    def testCommit(self):
        """L{SolrClient.commits} commits the changes to Solr."""
        doc = {'id': _randomString(20)}
        yield self.client.add(doc)
        r = yield self.client.search('id:%s' % doc['id'])
        self.assertEqual(r.results.numFound, 0,
                         'Document addition was commited')

        yield self.client.commit()

        r = yield self.client.search('id:%s' % doc['id'])
        self.assertEqual(r.results.numFound, 1,
                         'Commit did not work')

    @inlineCallbacks
    def testRollback(self):
        """
        L{SolrClient.rollback} withdraws all the changes since the last commit.
        """
        doc = {'id': _randomString(20)}
        yield self.client.add(doc)
        yield self.client.rollback()
        yield self.client.commit()

        r = yield self.client.search('id:%s' % doc['id'])

        self.assertEqual(r.results.numFound, 0,
                         'Rollback did not work')

    @inlineCallbacks
    def testsOptimize(self):
        """L{SolrClient.optimize} commits and optimizes the index."""
        doc = {'id': _randomString(20)}
        yield self.client.add(doc)
        r = yield self.client.search('id:%s' % doc['id'])
        self.assertEqual(r.results.numFound, 0,
                         'Document addition was commited')

        yield self.client.optimize()

        r = yield self.client.search('id:%s' % doc['id'])
        self.assertEqual(r.results.numFound, 1,
                         'Optimize did not work')
