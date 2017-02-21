from asyncbb.handlers import BaseHandler
from asyncbb.database import DatabaseMixin
from asyncbb.errors import JSONHTTPError
from tokenservices.handlers import WebLoginHandler
from tornado.web import StaticFileHandler
from tokenbrowser.id_service_client import IdServiceClient

class UserMixin:

    def get_current_user(self):
        val = self.get_secure_cookie("user")
        if isinstance(val, bytes):
            val = val.decode('ascii')
        return val

class LoginHandler(WebLoginHandler):

    def is_address_allowed(self, address):
        return True

    def on_login(self, address):

        self.set_secure_cookie("user", address)
        self.write({
            "address": address
        })

class LogoutHandler(BaseHandler):

    def post(self):

        self.clear_all_cookies()
        self.redirect("/admin/login")

class LoginPageHandler(StaticFileHandler):

    def initialize(self):
        super().initialize('public/')

    def get(self):
        return super().get('login.html')

class RootHandler(UserMixin, StaticFileHandler):

    def initialize(self):
        super().initialize('public/')

    async def get(self):

        if not self.get_current_user():
            self.redirect("/admin/login")
        else:
            return super().get('admin.html')

class CurrentUserHandler(UserMixin, BaseHandler):

    async def get(self):
        address = self.current_user
        if address:
            idclient = IdServiceClient(use_tornado=True)
            user = await idclient.get_user(address)
        else:
            raise JSONHTTPError(401)

        self.write({"user": user})

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
