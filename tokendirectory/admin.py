from asyncbb.handlers import BaseHandler
from asyncbb.database import DatabaseMixin
from asyncbb.errors import JSONHTTPError
from tornado.web import StaticFileHandler

from .handlers import UserMixin

class RootHandler(UserMixin, StaticFileHandler):

    def initialize(self):
        super().initialize('public/')

    async def get(self):

        if not self.is_admin_user():
            self.redirect("/login?redirect=/admin")
        else:
            return super().get('admin.html')

class AddFeaturedHandler(UserMixin, DatabaseMixin, BaseHandler):

    async def post(self):
        if not self.current_user:
            raise JSONHTTPError(401)

        address = self.json['address']
        async with self.db:
            await self.db.execute("UPDATE apps SET featured = TRUE WHERE eth_address = $1", address)
            await self.db.commit()

        self.set_status(204)

class RemoveFeaturedHandler(UserMixin, DatabaseMixin, BaseHandler):

    async def post(self):
        if not self.current_user:
            raise JSONHTTPError(401)

        address = self.json['address']
        async with self.db:
            await self.db.execute("UPDATE apps SET featured = FALSE WHERE eth_address = $1", address)
            await self.db.commit()

        self.set_status(204)

urls = [
    (r"^/admin/?$", RootHandler),
    (r"^/admin/featured/add/?$", AddFeaturedHandler),
    (r"^/admin/featured/remove/?$", RemoveFeaturedHandler)
]
