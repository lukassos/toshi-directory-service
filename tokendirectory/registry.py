from tokenservices.handlers import BaseHandler
from tokenservices.database import DatabaseMixin
from tokenservices.errors import JSONHTTPError

from tornado.web import StaticFileHandler
from tokenservices.clients import IdServiceClient
from tokenservices.utils import validate_address

from .handlers import UserMixin, sofa_manifest_from_row

def response_for_row(row):
    rval = sofa_manifest_from_row(row)
    if 'featured' in row:
        rval['featured'] = row['featured']
    else:
        rval['featured'] = False
    if 'request_for_featured' in row:
        rval['requestForFeatured'] = row['request_for_featured']
    return rval

class RootHandler(UserMixin, StaticFileHandler):

    def initialize(self):
        super().initialize('public/')

    async def get(self):

        if not self.current_user:
            self.redirect("/login")
        else:
            return super().get('registry.html')

class AppsHandler(UserMixin, DatabaseMixin, BaseHandler):

    async def get(self):
        if not self.current_user:
            raise JSONHTTPError(401)

        try:
            offset = int(self.get_query_argument('offset', 0))
            limit = int(self.get_query_argument('limit', 10))
        except ValueError:
            raise JSONHTTPError(400, body={'errors': [{'id': 'bad_arguments', 'message': 'Bad Arguments'}]})

        async with self.db:
            count = await self.db.fetchrow(
                "SELECT count(*) FROM submissions WHERE submitter_token_id = $1",
                self.current_user)
            apps = await self.db.fetch(
                "SELECT apps.*, sofa_manifests.*, submissions.request_for_featured FROM submissions "
                "JOIN apps ON submissions.app_token_id = apps.token_id "
                "JOIN sofa_manifests ON apps.token_id = sofa_manifests.token_id "
                "WHERE submissions.submitter_token_id = $1 "
                "ORDER BY apps.name "
                "OFFSET $2 "
                "LIMIT $3",
                self.current_user,
                offset, limit)

        results = []
        for row in apps:
            val = response_for_row(row)
            results.append(val)

        self.write({
            'offset': offset,
            'limit': limit,
            'apps': results,
            'total': count['count']
        })

    async def post(self):
        """Handles submitting a new app to the directory service"""

        if not self.current_user:
            raise JSONHTTPError(401)

        if not all(x in self.json for x in ['display_name', 'token_id']):
            raise JSONHTTPError(400, body={'errors': [{'id': 'bad_arguments', 'message': 'Bad Arguments'}]})

        token_id = self.json['token_id']
        if not validate_address(token_id):
            raise JSONHTTPError(400, body={'errors': [{'id': 'invalid_token_id', 'message': 'Invalid Arguments'}]})

        # check if the user has already submitted this app
        async with self.db:
            existing = await self.db.fetchrow(
                "SELECT * FROM submissions WHERE submitter_token_id = $1 AND app_token_id = $2",
                self.current_user, self.json['token_id'])
        if existing:
            raise JSONHTTPError(400, body={'errors': [{'id': 'already_exists', 'message': 'App already exists'}]})

        # check if the app has already been submitted (by someone else for e.g.)
        async with self.db:
            existing = await self.db.fetchrow(
                "SELECT * FROM apps WHERE token_id = $1",
                self.json['token_id'])

        # TODO: maybe this is actually ok (but it would be weird)
        if existing:
            raise JSONHTTPError(400, body={'errors': [{'id': 'already_exists', 'message': 'App already exists'}]})

        client = IdServiceClient(use_tornado=True)
        bot = await client.get_user(self.json['token_id'])
        if bot is None:
            raise JSONHTTPError(400, body={'errors': [{'id': 'not_found', 'message': 'Cannot find given address in the id service'}]})

        username = bot['username']
        payment_address = bot['payment_address']
        display_name = self.json['display_name']

        init_request = ['paymentAddress', 'language']
        languages = ['en']
        interfaces = ['ChatBot']
        protocol = 'sofa-v1.0'

        avatar_url = self.json.get('avatar_url', None)
        if not avatar_url:
            avatar_url = 'https://token-id-service.herokuapp.com/identicon/{}.png'.format(token_id)

        async with self.db:
            await self.db.execute(
                "INSERT INTO apps "
                "(token_id, name) VALUES ($1, $2) ",
                token_id, display_name)
            await self.db.execute(
                "INSERT INTO sofa_manifests "
                "(token_id, payment_address, username, init_request, languages, interfaces, protocol, avatar_url) "
                "VALUES "
                "($1, $2, $3, $4, $5, $6, $7, $8)",
                token_id, payment_address, username, init_request, languages, interfaces, protocol, avatar_url)
            await self.db.execute(
                "INSERT INTO submissions "
                "(app_token_id, submitter_token_id) "
                "VALUES "
                "($1, $2)",
                token_id, self.current_user)
            row = await self.db.fetchrow("SELECT * FROM apps JOIN sofa_manifests ON apps.token_id = sofa_manifests.token_id WHERE apps.token_id = $1", token_id)
            await self.db.commit()

        self.write(response_for_row(row))

    async def put(self):
        """Handles submitting a new app to the directory service"""

        if not self.current_user:
            raise JSONHTTPError(401)

        if not all(x in self.json for x in ['display_name', 'token_id']):
            raise JSONHTTPError(400, body={'errors': [{'id': 'bad_arguments', 'message': 'Bad Arguments'}]})

        token_id = self.json['token_id']
        if not validate_address(token_id):
            raise JSONHTTPError(400, body={'errors': [{'id': 'invalid_address', 'message': 'Invalid Arguments'}]})

        # check if the user has already submitted this app
        async with self.db:
            existing = await self.db.fetchrow(
                "SELECT * FROM submissions WHERE submitter_token_id = $1 AND app_token_id = $2",
                self.current_user, self.json['token_id'])
        if not existing:
            raise JSONHTTPError(400, body={'errors': [{'id': 'app_does_not_exists', 'message': 'App Doesn\'t exists'}]})

        display_name = self.json['display_name']
        avatar_url = self.json.get('avatar_url', None)
        if not avatar_url:
            avatar_url = 'https://token-id-service.herokuapp.com/identicon/{}.png'.format(token_id)

        async with self.db:
            await self.db.execute(
                "UPDATE apps "
                "SET name = $1 "
                "WHERE token_id = $2",
                display_name, token_id)
            await self.db.execute(
                "UPDATE sofa_manifests "
                "SET avatar_url = $1 "
                "WHERE token_id = $2",
                avatar_url, token_id)
            row = await self.db.fetchrow(
                "SELECT * FROM apps "
                "JOIN sofa_manifests ON apps.token_id = sofa_manifests.token_id "
                "JOIN submissions ON submissions.app_token_id = apps.token_id "
                "WHERE apps.token_id = $1", token_id)
            await self.db.commit()

        self.write(response_for_row(row))

class RequestFeaturedHandler(UserMixin, DatabaseMixin, BaseHandler):

    async def post(self):
        if not self.current_user:
            raise JSONHTTPError(401)

        address = self.json['address']
        async with self.db:
            await self.db.execute("UPDATE submissions SET request_for_featured = TRUE WHERE app_token_id = $1", address)
            await self.db.commit()

        self.set_status(204)

class RemoveFeaturedHandler(UserMixin, DatabaseMixin, BaseHandler):

    async def post(self):
        if not self.current_user:
            raise JSONHTTPError(401)

        address = self.json['address']
        async with self.db:
            await self.db.execute("UPDATE submissions SET request_for_featured = FALSE WHERE app_token_id = $1", address)
            await self.db.execute("UPDATE apps SET featured = FALSE WHERE token_id = $1", address)
            await self.db.commit()

        self.set_status(204)

urls = [
    (r"^/?$", RootHandler),
    (r"^/registry/apps/?$", AppsHandler),
    (r"^/registry/featured/add/?$", RequestFeaturedHandler),
    (r"^/registry/featured/remove/?$", RemoveFeaturedHandler)
]
