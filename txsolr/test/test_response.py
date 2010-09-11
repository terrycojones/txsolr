import unittest

from txsolr.response import JSONSolrResponse
from txsolr.errors import SolrResponseError

class ResponseTest(unittest.TestCase):

    def test_jsonSolrResponse(self):

        raw = '''{
                 "responseHeader":{
                  "status":0,
                  "QTime":2,
                  "params":{
                    "indent":"on",
                    "wt":"json",
                    "q":"manuel"}},
                 "response":{"numFound":0,"start":0,"docs":[]}
                 }'''

        r = JSONSolrResponse(raw)

        print r.responseDict

        self.assertEqual(r.header['status'], 0)
        self.assertEqual(r.header['QTime'], 2)
        self.assertEqual(r.results.numFound, 0)
        self.assertEqual(len(r.results.docs), 0)

        raw = '''{
                 "responseHeader":{
                  "status":1,
                  "QTime":2,
                  "params":{
                    "indent":"on",
                    "wt":"json",
                    "q":"manuel"}},
                 "response":{"numFound":0,"start":0,"docs":[]}
                 }'''

        self.assertRaises(SolrResponseError, JSONSolrResponse, raw)

        raw = '''<response>
                    <lst name="responseHeader">
                     <int name="status">0</int>
                     <int name="QTime">0</int>
                     <lst name="params">
                      <str name="indent">on</str>
                      <str name="wt">standard</str>
                      <str name="q">manuel</str>
                     </lst>
                    </lst>
                    <result name="response" numFound="0" start="0"/>
                </response> '''

        self.assertRaises(SolrResponseError, JSONSolrResponse, raw)
