import urllib.parse

from asyncbb.handlers import BaseHandler, JsonBodyMixin
from asyncbb.database import DatabaseMixin
from asyncbb.errors import JSONHTTPError
from tokenbrowser.id_service_client import IdServiceClient
from tornado.web import StaticFileHandler
from asyncbb.log import log

def sofa_manifest_from_row(row):
    return {
        "displayName": row['display_name'],
        "protocol": row['protocol'],
        "avatarUrl": row['avatar_url'],
        "interfaces": row['interfaces'],
        "ownerAddress": row['eth_address'],
        "paymentAddress": row['eth_address'],
        "featured": row['featured'],
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
        countsql = "SELECT COUNT(*) " + sql[8:]
        countargs = args[:]
        sql += " ORDER BY username OFFSET ${} LIMIT ${}".format(len(args) + 1, len(args) + 2)
        args.extend([offset, limit])

        async with self.db:
            count = await self.db.fetchrow(countsql, *countargs)
            rows = await self.db.fetch(sql, *args)

        results = [sofa_manifest_from_row(row) for row in rows]

        self.write({
            'query': query or '',
            'offset': offset,
            'limit': limit,
            'apps': results,
            'featured': featured,
            'total': count['count']
        })

class UserMixin:

    def get_current_user(self):
        val = self.get_secure_cookie("user")
        if isinstance(val, bytes):
            val = val.decode('ascii')
        if not val:
            # make sure empty strings aren't counted as valid
            return None
        return val

class LogoutHandler(BaseHandler):

    def post(self):

        redirect = urllib.parse.urlparse(self.request.headers.get('Referer', '')).path

        self.clear_all_cookies()
        self.redirect("/login?redirect={}".format(redirect))

class LoginPageHandler(JsonBodyMixin, StaticFileHandler):

    def initialize(self):
        super().initialize('public/')

    def get(self):
        return super().get('login.html')

    async def post(self):
        if 'auth_token' not in self.json:
            raise JSONHTTPError(400, body={'errors': [{'id': 'bad_arguments', 'message': 'Bad Arguments'}]})
        token = self.json['auth_token']

        idclient = IdServiceClient(use_tornado=True)
        try:
            user = await idclient.whodis(token)
        except:
            log.exception("...")
            user = None

        if user:
            self.set_secure_cookie("user", user['owner_address'])
            self.set_status(204)
        else:
            raise JSONHTTPError(400, body={'errors': [{'id': 'invalid_token', 'message': 'Invalid token'}]})

class CurrentUserHandler(UserMixin, BaseHandler):

    async def get(self):
        address = self.current_user
        if address:
            idclient = IdServiceClient(use_tornado=True)
            user = await idclient.get_user(address)
        else:
            raise JSONHTTPError(401)

        self.write({"user": user})
