from tornado.escape import json_decode
from tornado.testing import gen_test

from tokendirectory.app import urls
from asyncbb.test.database import requires_database
from tokenservices.test.base import AsyncHandlerTest

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

        setup_data = [
            ("TokenBotA", TEST_ADDRESS[:-1] + 'f', False),
            ("TokenBotB", TEST_ADDRESS[:-1] + 'e', False),
            ("FeaturedBotA", TEST_ADDRESS[:-1] + 'd', True),
            ("FeaturedBotB", TEST_ADDRESS[:-1] + 'c', True),
            ("FeaturedBotC", TEST_ADDRESS[:-1] + 'b', True)
        ]

        for username, addr, featured in setup_data:
            async with self.pool.acquire() as con:
                await con.execute("INSERT INTO apps (username, eth_address, featured) VALUES ($1, $2, $3)", username, addr, featured)

        resp = await self.fetch("/apps", method="GET")
        self.assertResponseCodeEqual(resp, 200)
        body = json_decode(resp.body)
        self.assertEqual(len(body['apps']), 5)

        resp = await self.fetch("/apps?featured", method="GET")
        self.assertEqual(resp.code, 200)
        body = json_decode(resp.body)
        self.assertEqual(len(body['apps']), 3)

        for true in ['', 'true', 'featured', 'TRUE', 'True']:

            resp = await self.fetch("/apps?featured={}".format(true), method="GET")
            self.assertEqual(resp.code, 200)
            body = json_decode(resp.body)
            self.assertEqual(len(body['apps']), 3, "Failed to map featured={} to true".format(true))

        for false in ['false', 'FALSE', 'False']:

            resp = await self.fetch("/apps?featured={}".format(false), method="GET")
            self.assertEqual(resp.code, 200)
            body = json_decode(resp.body)
            self.assertEqual(len(body['apps']), 5, "Failed to map featured={} to false".format(false))

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
