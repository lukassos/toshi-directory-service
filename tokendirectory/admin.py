from asyncbb.handlers import BaseHandler
from asyncbb.database import DatabaseMixin
from asyncbb.errors import JSONHTTPError
from tornado.web import StaticFileHandler
from tokenbrowser.id_service_client import IdServiceClient

from .handlers import UserMixin, sofa_manifest_from_row

class AdminUserMixin(UserMixin):

    async def is_admin_user(self):
        async with self.db:
            user = await self.db.fetchrow('SELECT * FROM admins WHERE eth_address = $1', self.current_user)
        return True if user else False

class RootHandler(AdminUserMixin, DatabaseMixin, StaticFileHandler):

    def initialize(self):
        super().initialize('public/')

    async def get(self):

        if not await self.is_admin_user():
            self.redirect("/login?redirect=/admin")
        else:
            return super().get('admin.html')

class AppsHandler(AdminUserMixin, DatabaseMixin, BaseHandler):

    async def get(self):
        if not await self.is_admin_user():
            raise JSONHTTPError(401)

        try:
            offset = int(self.get_query_argument('offset', 0))
            limit = int(self.get_query_argument('limit', 10))
        except ValueError:
            raise JSONHTTPError(400, body={'errors': [{'id': 'bad_arguments', 'message': 'Bad Arguments'}]})

        async with self.db:
            count = await self.db.fetchrow(
                "SELECT count(*) FROM submissions")
            apps = await self.db.fetch(
                "SELECT apps.*, submissions.request_for_featured FROM submissions JOIN apps ON "
                "submissions.app_eth_address = apps.eth_address "
                "ORDER BY apps.username "
                "OFFSET $1 "
                "LIMIT $2",
                offset, limit)

        results = []
        for row in apps:
            val = sofa_manifest_from_row(row)
            val['requestForFeatured'] = row['request_for_featured']
            results.append(val)

        self.write({
            'offset': offset,
            'limit': limit,
            'apps': results,
            'total': count['count']
        })

class AdminsHandler(AdminUserMixin, DatabaseMixin, BaseHandler):

    async def get(self):
        if not await self.is_admin_user():
            raise JSONHTTPError(401)

        try:
            offset = int(self.get_query_argument('offset', 0))
            limit = int(self.get_query_argument('limit', 10))
        except ValueError:
            raise JSONHTTPError(400, body={'errors': [{'id': 'bad_arguments', 'message': 'Bad Arguments'}]})

        async with self.db:
            count = await self.db.fetchrow(
                "SELECT count(*) FROM admins")
            admins = await self.db.fetch(
                "SELECT * FROM admins "
                "OFFSET $1 "
                "LIMIT $2",
                offset, limit)

        results = []
        client = IdServiceClient(use_tornado=True)
        for row in admins:
            val = await client.get_user(row['eth_address'])
            results.append(val)

        self.write({
            'offset': offset,
            'limit': limit,
            'admins': results,
            'total': count['count']
        })

class AddAdminHandler(AdminUserMixin, DatabaseMixin, BaseHandler):

    async def post(self):

        if not await self.is_admin_user():
            raise JSONHTTPError(401)

        address = self.json['address']
        async with self.db:
            row = await self.db.fetchrow("SELECT * FROM admins WHERE eth_address = $1", address)
            if row is None:
                await self.db.execute("INSERT INTO admins (eth_address) VALUES ($1)", address)
                await self.db.commit()

        self.set_status(204)


class RemoveAdminHandler(AdminUserMixin, DatabaseMixin, BaseHandler):

    async def post(self):

        if not await self.is_admin_user():
            raise JSONHTTPError(401)

        address = self.json['address']
        async with self.db:
            await self.db.execute("DELETE FROM admins WHERE eth_address= $1", address)
            await self.db.commit()

        self.set_status(204)

class AdminsSearchHandler(AdminUserMixin, DatabaseMixin, BaseHandler):

    async def get(self):

        if not await self.is_admin_user():
            raise JSONHTTPError(401)

        query = self.get_query_argument('query')

        client = IdServiceClient(use_tornado=True)
        results = await client.search_user(query)

        self.write(results)

class AddFeaturedHandler(AdminUserMixin, DatabaseMixin, BaseHandler):

    async def post(self):
        if not await self.is_admin_user():
            raise JSONHTTPError(401)

        address = self.json['address']
        async with self.db:
            await self.db.execute("UPDATE apps SET featured = TRUE WHERE eth_address = $1", address)
            await self.db.execute("UPDATE submissions SET request_for_featured = FALSE WHERE app_eth_address = $1", address)
            await self.db.commit()

        self.set_status(204)

class RemoveFeaturedHandler(AdminUserMixin, DatabaseMixin, BaseHandler):

    async def post(self):
        if not await self.is_admin_user():
            raise JSONHTTPError(401)

        address = self.json['address']
        async with self.db:
            await self.db.execute("UPDATE apps SET featured = FALSE WHERE eth_address = $1", address)
            await self.db.commit()

        self.set_status(204)

class RejectFeaturedHandler(AdminUserMixin, DatabaseMixin, BaseHandler):

    async def post(self):
        if not await self.is_admin_user():
            raise JSONHTTPError(401)

        address = self.json['address']
        async with self.db:
            await self.db.execute("UPDATE apps SET featured = FALSE WHERE eth_address = $1", address)
            await self.db.execute("UPDATE submissions SET request_for_featured = FALSE WHERE app_eth_address = $1", address)
            await self.db.commit()

        self.set_status(204)

urls = [
    (r"^/admin/?$", RootHandler),
    (r"^/admin/apps/?$", AppsHandler),
    (r"^/admin/admins/?$", AdminsHandler),
    (r"^/admin/admins/add?$", AddAdminHandler),
    (r"^/admin/admins/remove?$", RemoveAdminHandler),
    (r"^/admin/admins/search?$", AdminsSearchHandler),
    (r"^/admin/featured/add/?$", AddFeaturedHandler),
    (r"^/admin/featured/remove/?$", RemoveFeaturedHandler),
    (r"^/admin/featured/reject/?$", RejectFeaturedHandler)
]
