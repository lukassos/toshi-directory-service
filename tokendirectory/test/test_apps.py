import time

from tornado.escape import json_decode
from tornado.testing import gen_test

from tokendirectory.app import urls
from asyncbb.test.database import requires_database
from tokenservices.test.base import AsyncHandlerTest
from tokenbrowser.crypto import sign_payload
from tokenbrowser.request import sign_request
from ethutils import data_decoder

TEST_ADDRESS = "0x056db290f8ba3250ca64a45d16284d04bc6f5fbf"

class AppsHandlerTest(AsyncHandlerTest):

    def get_urls(self):
        return urls

    def get_url(self, path):
        path = "/v1{}".format(path)
        return super().get_url(path)

    @gen_test
    @requires_database
    async def test_get_app_index(self):
        resp = await self.fetch("/apps/", method="GET")
        self.assertResponseCodeEqual(resp, 200)
        body = json_decode(resp.body)
        self.assertEqual(len(body['apps']), 0)

    @gen_test
    @requires_database
    async def test_get_app(self):
        username = "TokenBot"
        async with self.pool.acquire() as con:
            await con.execute("INSERT INTO apps (username, eth_address) VALUES ($1, $2)", username, TEST_ADDRESS)
        resp = await self.fetch("/apps/{}".format(TEST_ADDRESS), method="GET")
        self.assertResponseCodeEqual(resp, 200)

    @gen_test
    @requires_database
    async def test_get_missing_app(self):
        resp = await self.fetch("/apps/{}".format(TEST_ADDRESS), method="GET")
        self.assertResponseCodeEqual(resp, 404)
