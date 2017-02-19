from tornado.escape import json_decode
from tornado.testing import gen_test

from tokendirectory.app import urls
from asyncbb.test.base import AsyncHandlerTest
from asyncbb.test.database import requires_database

from urllib.parse import quote_plus

TEST_ADDRESS = "0x056db290f8ba3250ca64a45d16284d04bc6f5fbf"

class SearchAppsHandlerTest(AsyncHandlerTest):

    def get_urls(self):
        return urls

    def fetch(self, url, **kwargs):
        return super(SearchAppsHandlerTest, self).fetch("/v1{}".format(url), **kwargs)

    @gen_test
    @requires_database
    async def test_username_query(self):
        username = "TokenBot"
        positive_query = 'enb'
        negative_query = 'TickleFight'

        async with self.pool.acquire() as con:
            await con.execute("INSERT INTO apps (username, eth_address) VALUES ($1, $2)", username, TEST_ADDRESS)

        resp = await self.fetch("/search/apps?query={}".format(positive_query), method="GET")
        self.assertEqual(resp.code, 200)
        body = json_decode(resp.body)
        self.assertEqual(len(body['apps']), 1)

        resp = await self.fetch("/search/apps?query={}".format(negative_query), method="GET")
        self.assertEqual(resp.code, 200)
        body = json_decode(resp.body)
        self.assertEqual(len(body['apps']), 0)

    @gen_test
    @requires_database
    async def test_featured_query(self):

        positive_query = 'bot'

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

        resp = await self.fetch("/search/apps?query={}".format(positive_query), method="GET")
        self.assertEqual(resp.code, 200)
        body = json_decode(resp.body)
        self.assertEqual(len(body['apps']), 5)

        resp = await self.fetch("/search/apps?query={}&featured".format(positive_query), method="GET")
        self.assertEqual(resp.code, 200)
        body = json_decode(resp.body)
        self.assertEqual(len(body['apps']), 3)

        for true in ['', 'true', 'featured', 'TRUE', 'True']:

            resp = await self.fetch("/search/apps?query={}&featured={}".format(positive_query, true), method="GET")
            self.assertEqual(resp.code, 200)
            body = json_decode(resp.body)
            self.assertEqual(len(body['apps']), 3, "Failed to map featured={} to true".format(true))

        for false in ['false', 'FALSE', 'False']:

            resp = await self.fetch("/search/apps?query={}&featured={}".format(positive_query, false), method="GET")
            self.assertEqual(resp.code, 200)
            body = json_decode(resp.body)
            self.assertEqual(len(body['apps']), 5, "Failed to map featured={} to false".format(false))

    @gen_test
    @requires_database
    async def test_bad_limit_and_offset(self):
        positive_query = 'enb'

        resp = await self.fetch("/search/apps?query={}&offset=x".format(positive_query), method="GET")
        self.assertEqual(resp.code, 400)

        resp = await self.fetch("/search/apps?query={}&limit=x".format(positive_query), method="GET")
        self.assertEqual(resp.code, 400)
