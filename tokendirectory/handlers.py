import urllib.parse

from asyncbb.handlers import BaseHandler, JsonBodyMixin
from asyncbb.database import DatabaseMixin
from asyncbb.errors import JSONHTTPError
from tokenservices.handlers import RequestVerificationMixin
from tokenbrowser.id_service_client import IdServiceClient
from tornado.web import StaticFileHandler, HTTPError
from asyncbb.log import log
from decimal import Decimal
from tokenbrowser.utils import validate_address, validate_decimal_string, parse_int

def sofa_manifest_from_row(row):
    return {
        "displayName": row['name'],
        "protocol": row['protocol'],
        "avatarUrl": row['avatar_url'],
        "interfaces": row['interfaces'],
        "ownerAddress": row['token_id'],
        "paymentAddress": row['payment_address'],
        "featured": row['featured'],
        "webApp": row['web_app'],
        "languages": row['languages'],
        "initRequest": {"values": row['init_request']}
    }

def app_from_row(row):
    return {
        "token_id": row['token_id'],
        "username": row['username'],
        "reputation_score": float(row['reputation_score']) if row['reputation_score'] else None,
        "review_count": row['review_count'],
        "is_app": True,
        "payment_address": row['payment_address'],
        "custom": {
            "about": row['description'],
            "name": row['name'],
            "avatar": row['avatar_url'],
            #"manifest": sofa_manifest_from_row(row)
        }
    }

class AppsHandler(DatabaseMixin, BaseHandler):
    async def get(self, token_id):

        async with self.db:
            row = await self.db.fetchrow(
                "SELECT apps.*, sofa_manifests.* FROM apps "
                "JOIN sofa_manifests ON "
                "sofa_manifests.token_id = apps.token_id "
                "WHERE apps.token_id = $1", token_id)
        if row is None:
            raise JSONHTTPError(404, body={'errors': [{'id': 'not_found', 'message': 'Not Found'}]})
        result = app_from_row(row)
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
        sql = "SELECT * FROM apps JOIN sofa_manifests ON sofa_manifests.token_id = apps.token_id "
        if query:
            args.append('%{}%'.format(query))
            sql += " WHERE apps.name ILIKE $1"
            if featured:
                sql += " AND apps.featured IS TRUE"
        elif featured:
            sql += " WHERE apps.featured IS TRUE"
        countsql = "SELECT COUNT(*) " + sql[8:]
        countargs = args[:]
        sql += " ORDER BY apps.name OFFSET ${} LIMIT ${}".format(len(args) + 1, len(args) + 2)
        args.extend([offset, limit])

        async with self.db:
            count = await self.db.fetchrow(countsql, *countargs)
            rows = await self.db.fetch(sql, *args)

        results = [app_from_row(row) for row in rows]

        self.write({
            'query': query or '',
            'offset': offset,
            'limit': limit,
            'apps': results,
            'featured': featured,
            'total': count['count']
        })


class SofaManifestHandler(DatabaseMixin, BaseHandler):
    async def get(self, token_id):

        async with self.db:
            row = await self.db.fetchrow(
                "SELECT apps.*, sofa_manifests.* FROM apps "
                "JOIN sofa_manifests ON "
                "sofa_manifests.token_id = apps.token_id "
                "WHERE apps.token_id = $1", token_id)
        if row is None:
            raise JSONHTTPError(404, body={'errors': [{'id': 'not_found', 'message': 'Not Found'}]})
        result = sofa_manifest_from_row(row)
        self.write(result)


class ReputationUpdateHandler(RequestVerificationMixin, DatabaseMixin, BaseHandler):

    async def post(self):

        if 'reputation' not in self.application.config or 'id' not in self.application.config['reputation']:
            raise HTTPError(404)

        try:
            address = self.verify_request()
        except JSONHTTPError:
            raise HTTPError(404)

        if address != self.application.config['reputation']['id']:
            raise HTTPError(404)

        if not all(x in self.json for x in ['address', 'score', 'count']):
            raise JSONHTTPError(400, body={'errors': [{'id': 'bad_arguments', 'message': 'Bad Arguments'}]})

        token_id = self.json['address']
        if not validate_address(token_id):
            raise JSONHTTPError(400, body={'errors': [{'id': 'invalid_address', 'message': 'Invalid Address'}]})

        count = self.json['count']
        count = parse_int(count)
        if count is None:
            raise JSONHTTPError(400, body={'errors': [{'id': 'invalid_count', 'message': 'Invalid Count'}]})

        score = self.json['score']
        if isinstance(score, str) and validate_decimal_string(score):
            score = Decimal(score)
        if not isinstance(score, (int, float, Decimal)):
            raise JSONHTTPError(400, body={'errors': [{'id': 'invalid_score', 'message': 'Invalid Score'}]})

        async with self.db:
            await self.db.execute("UPDATE apps SET reputation_score = $1, review_count = $2 WHERE token_id = $3",
                                  score, count, token_id)
            await self.db.commit()

        self.set_status(204)


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
            self.set_secure_cookie("user", user['token_id'])
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
