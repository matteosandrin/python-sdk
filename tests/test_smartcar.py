import unittest
import responses
import smartcar
import base64
import time
from datetime import datetime, timedelta
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

def basic_auth(id, secret):
    auth_pair = id + ':' + secret
    return 'Basic {}'.format(
        base64.b64encode(auth_pair.encode('utf-8')).decode('utf-8')
    )
def request():
    return responses.calls[0].request

class TestSmartcar(unittest.TestCase):
    def setUp(self):
        self.client_id = 'client-id'
        self.client_secret = 'client-secret'
        self.redirect_uri = 'https://redirect.uri'
        self.scope = ['a', 'b', 'c']
        self.client = smartcar.AuthClient(self.client_id, self.client_secret,
                self.redirect_uri, self.scope, True)
        self.maxDiff = None
        self.basic_auth = basic_auth(self.client_id, self.client_secret)
        self.expected = {'key': 'value', 'expires_in':7200}

    def test_is_expired(self):
        access = {'expires_in': 7200}

        now = datetime.utcnow()
        two_hours_from_now = (datetime.utcnow() + timedelta(hours=2.5))

        access['expiration'] = (datetime.utcnow() + timedelta(seconds=access['expires_in']))
        self.assertTrue(now <= access['expiration'] < two_hours_from_now)

        self.assertFalse(smartcar.is_expired(access['expiration']))

        access['expiration'] = (datetime.utcnow() - timedelta(hours=2.1))

        self.assertTrue(smartcar.is_expired(access['expiration']))

    def test_get_auth_url(self):
        client = smartcar.AuthClient(self.client_id, self.client_secret,
                self.redirect_uri, self.scope)
        actual = client.get_auth_url(force=True, state='stuff')
        query = urlencode({
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'approval_prompt': 'force',
            'scope': ' '.join(self.scope),
            'state': 'stuff'
        })
        expected = smartcar.const.CONNECT_URL + '/oauth/authorize?' + query
        self.assertEqual(actual, expected)

    def test_get_auth_url_test_mode_true(self):
        client = smartcar.AuthClient(self.client_id, self.client_secret,
                self.redirect_uri, self.scope, test_mode=True)
        actual = client.get_auth_url(force=True, state='stuff')
        query = urlencode({
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'approval_prompt': 'force',
            'mode': 'test',
            'scope': ' '.join(self.scope),
            'state': 'stuff'
        })
        expected = smartcar.const.CONNECT_URL + '/oauth/authorize?' + query
        self.assertEqual(actual, expected)

    def test_get_auth_url_test_mode_no_keyword_true(self):
        client = smartcar.AuthClient(self.client_id, self.client_secret,
                self.redirect_uri, self.scope, True)
        actual = client.get_auth_url(force=True, state='stuff')
        query = urlencode({
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'approval_prompt': 'force',
            'mode': 'test',
            'scope': ' '.join(self.scope),
            'state': 'stuff'
        })
        expected = smartcar.const.CONNECT_URL + '/oauth/authorize?' + query
        self.assertEqual(actual, expected)

    def test_get_auth_url_test_mode_false(self):
        client = smartcar.AuthClient(self.client_id, self.client_secret,
                self.redirect_uri, self.scope, test_mode=False)
        actual = client.get_auth_url(force=True, state='stuff')
        query = urlencode({
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'approval_prompt': 'force',
            'scope': ' '.join(self.scope),
            'state': 'stuff'
        })
        expected = smartcar.const.CONNECT_URL + '/oauth/authorize?' + query
        self.assertEqual(actual, expected)

    def test_get_auth_url_development_true(self):
        client = smartcar.AuthClient(self.client_id, self.client_secret,
                self.redirect_uri, self.scope, development=True)
        actual = client.get_auth_url(force=True, state='stuff')
        query = urlencode({
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'approval_prompt': 'force',
            'mode': 'test',
            'scope': ' '.join(self.scope),
            'state': 'stuff'
        })
        expected = smartcar.const.CONNECT_URL + '/oauth/authorize?' + query
        self.assertEqual(actual, expected)

    def test_get_auth_url_development_false(self):
        client = smartcar.AuthClient(self.client_id, self.client_secret,
                self.redirect_uri, self.scope, development=False)
        actual = client.get_auth_url(force=True, state='stuff')
        query = urlencode({
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'approval_prompt': 'force',
            'scope': ' '.join(self.scope),
            'state': 'stuff'
        })
        expected = smartcar.const.CONNECT_URL + '/oauth/authorize?' + query
        self.assertEqual(actual, expected)

    @responses.activate
    def test_exchange_code(self):
        body = {
            'grant_type': 'authorization_code',
            'code': 'code',
            'redirect_uri': self.redirect_uri
        }
        responses.add('POST', smartcar.const.AUTH_URL, json=self.expected)
        actual = self.client.exchange_code('code')
        self.assertIn('key', actual)
        self.assertTrue(actual['expiration'] > datetime.utcnow())
        self.assertTrue(actual['refresh_expiration'] > datetime.utcnow())
        self.assertEqual(request().headers['Authorization'], self.basic_auth)
        self.assertEqual(request().headers['Content-Type'], 'application/x-www-form-urlencoded')
        self.assertEqual(request().body, urlencode(body))

    @responses.activate
    def test_exchange_token(self):
        body = {
            'grant_type': 'refresh_token',
            'refresh_token': 'refresh_token'
        }
        responses.add('POST', smartcar.const.AUTH_URL, json=self.expected)
        actual = self.client.exchange_refresh_token('refresh_token')
        self.assertIn('key', actual)
        self.assertTrue(actual['expiration'] > datetime.utcnow())
        self.assertTrue(actual['refresh_expiration'] > datetime.utcnow())
        self.assertEqual(request().headers['Authorization'], self.basic_auth)
        self.assertEqual(request().headers['Content-Type'], 'application/x-www-form-urlencoded')
        self.assertEqual(request().body, urlencode(body))

    @responses.activate
    def test_get_vehicle_ids(self):
        query = { 'limit': 11, 'offset': 1 }
        access_token = 'access_token'
        url = smartcar.const.API_URL + '/vehicles?' + urlencode(query)
        responses.add('GET', url, json=self.expected, match_querystring=True)
        actual = smartcar.get_vehicle_ids(access_token, limit=query['limit'], offset=query['offset'])
        self.assertEqual(actual, self.expected)
        self.assertEqual(request().headers['Authorization'], 'Bearer ' + access_token)

    @responses.activate
    def test_get_user_id(self):
        access_token = 'access_token'
        data = {
            'id': 'user_id',
        }
        url = smartcar.const.API_URL + '/user'
        responses.add('GET', url, json=data)
        actual = smartcar.get_user_id(access_token)
        self.assertEqual(actual, data['id'])
        self.assertEqual(request().headers['Authorization'], 'Bearer ' + access_token)
