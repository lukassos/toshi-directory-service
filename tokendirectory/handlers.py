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
        "initRequest": {"values": row['init_request']}
    }


class AppsHandler(DatabaseMixin, BaseHandler):
    async def get(self, eth_address):

        async with self.db:
            row = await self.db.fetchrow("SELECT * FROM apps WHERE eth_address = $1", eth_address)
        if row is None:
            raise JSONHTTPError(404, body={'errors': [{'id': 'not_found', 'message': 'Not Found'}]})
        result = sofa_manifest_from_row(row)
        self.write(result)

class SearchAppsHandler(DatabaseMixin, BaseHandler):
    async def get(self, force_featured=None):
        try:
            offset = int(self.get_query_argument('offset', 0))
            limit = int(self.get_query_argument('limit', 10))
        except ValueError:
            raise JSONHTTPError(400, body={'errors': [{'id': 'bad_arguments', 'message': 'Bad Arguments'}]})

        if force_featured:
            featured = True
        else:
            featured = self.get_query_argument('featured', 'false')
            if featured.lower() == 'false':
                featured = False
            else:
                featured = True
        query = self.get_query_argument('query', None)

        args = []
        sql = "SELECT * FROM apps"
        if query:
            args.append('%{}%'.format(query))
            sql += " WHERE username ILIKE $1"
            if featured:
                sql += " AND featured IS TRUE"
        elif featured:
            sql += " WHERE featured IS TRUE"
        sql += " ORDER BY username OFFSET ${} LIMIT ${}".format(len(args) + 1, len(args) + 2)
        args.extend([offset, limit])

        async with self.db:
            rows = await self.db.fetch(sql, *args)

        results = [sofa_manifest_from_row(row) for row in rows]

        self.write({
            'query': query or '',
            'offset': offset,
            'limit': limit,
            'apps': results,
            'featured': featured
        })
