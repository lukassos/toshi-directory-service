from asyncbb.handlers import BaseHandler
from asyncbb.database import DatabaseMixin
from asyncbb.errors import JSONHTTPError

from tornado.web import StaticFileHandler
from tokenbrowser.id_service_client import IdServiceClient
from tokenbrowser.utils import validate_address

from .handlers import UserMixin, sofa_manifest_from_row

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
                "SELECT count(*) FROM submissions WHERE submitter_address = $1",
                self.current_user)
            apps = await self.db.fetch(
                "SELECT apps.* FROM submissions JOIN apps ON "
                "submissions.app_eth_address = apps.eth_address "
                "WHERE submissions.submitter_address = $1 "
                "ORDER BY apps.username "
                "OFFSET $2 "
                "LIMIT $3",
                self.current_user,
                offset, limit)

        results = [sofa_manifest_from_row(row) for row in apps]

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

        if not all(x in self.json for x in ['display_name', 'owner_address']):
            raise JSONHTTPError(400, body={'errors': [{'id': 'bad_arguments', 'message': 'Bad Arguments'}]})

        owner_address = self.json['owner_address']
        if not validate_address(owner_address):
            raise JSONHTTPError(400, body={'errors': [{'id': 'invalid_address', 'message': 'Invalid Arguments'}]})

        # check if the user has already submitted this app
        async with self.db:
            existing = await self.db.fetchrow(
                "SELECT * FROM submissions WHERE submitter_address = $1 AND app_eth_address = $2",
                self.current_user, self.json['owner_address'])
        if existing:
            raise JSONHTTPError(400, body={'errors': [{'id': 'already_exists', 'message': 'App already exists'}]})

        # check if the app has already been submitted (by someone else for e.g.)
        async with self.db:
            existing = await self.db.fetchrow(
                "SELECT * FROM apps WHERE eth_address = $1",
                self.json['owner_address'])

        # TODO: maybe this is actually ok (but it would be weird)
        if existing:
            raise JSONHTTPError(400, body={'errors': [{'id': 'already_exists', 'message': 'App already exists'}]})

        client = IdServiceClient(use_tornado=True)
        bot = await client.get_user(self.json['owner_address'])
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
            avatar_url = 'https://token-id-service.herokuapp.com/identicon/{}.png'.format(owner_address)

        async with self.db:
            await self.db.execute(
                "INSERT INTO apps "
                "(eth_address, username, display_name, init_request, languages, interfaces, protocol, avatar_url) "
                "VALUES "
                "($1, $2, $3, $4, $5, $6, $7, $8)",
                owner_address, username, display_name, init_request, languages, interfaces, protocol, avatar_url)
            await self.db.execute(
                "INSERT INTO submissions "
                "(app_eth_address, submitter_address) "
                "VALUES "
                "($1, $2)",
                owner_address, self.current_user)
            row = await self.db.fetchrow("SELECT * FROM apps WHERE eth_address = $1", owner_address)
            await self.db.commit()

        self.write(sofa_manifest_from_row(row))

urls = [
    (r"^/?$", RootHandler),
    (r"^/registry/apps/?$", AppsHandler)
]
