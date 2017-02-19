import regex
import json

from asyncbb.handlers import BaseHandler
from asyncbb.database import DatabaseMixin
from asyncbb.errors import JSONHTTPError
from tokenservices.handlers import RequestVerificationMixin
from tornado.escape import json_encode

def sofa_manifest_from_row(row):
    return {
      "displayName": row['display_name'],
      "protocol": row['protocol'],
      "avatarUrl": row['avatar_url'],
      "interfaces": row['interfaces'],
      "ownerAddress": row['eth_address'],
      "paymentAddress": row['eth_address'],
      "webApp": row['web_app'],
      "languages": row['languages'],
      "initRequest": {"values": row['init_request'] }
    }


class AppsHandler(DatabaseMixin, BaseHandler):
    async def get(self, eth_address=None):

        if eth_address:
            async with self.db:
                row = await self.db.fetchrow("SELECT * FROM apps WHERE eth_address = $1", eth_address)
            if row is None:
                raise JSONHTTPError(404, body={'errors': [{'id': 'not_found', 'message': 'Not Found'}]})
            result = sofa_manifest_from_row(row)

        else:
            try:
                offset = int(self.get_query_argument('offset', 0, True))
                limit = int(self.get_query_argument('limit', 10, True))
            except ValueError:
                raise JSONHTTPError(400, body={'errors': [{'id': 'bad_arguments', 'message': 'Bad Arguments'}]})
            async with self.db:
                rows = await self.db.fetch("""
                SELECT *
                FROM apps
                ORDER BY username
                OFFSET $1
                LIMIT $2
                """, offset, limit)
                result = {'apps': [sofa_manifest_from_row(row) for row in rows]}

        self.write(result)


class SearchAppsHandler(DatabaseMixin, BaseHandler):
    async def get(self):
        try:
            offset = int(self.get_query_argument('offset', 0, True))
            limit = int(self.get_query_argument('limit', 10, True))
        except ValueError:
            raise JSONHTTPError(400, body={'errors': [{'id': 'bad_arguments', 'message': 'Bad Arguments'}]})

        query = self.get_query_argument('query', None, True)

        if query is None:
            results = []
        else:
            async with self.db:
                rows = await self.db.fetch("""
                SELECT *
                FROM apps
                WHERE username ILIKE $1
                ORDER BY username
                OFFSET $2
                LIMIT $3
                """, '%' + query + '%', offset, limit)
            results = [sofa_manifest_from_row(row) for row in rows]

            self.write({
                'query': query,
                'offset': offset,
                'limit': limit,
                'results': results
            })
