from . import handlers
from asyncbb.web import Application
from tokenservices.handlers import GenerateTimestamp
from tornado.web import StaticFileHandler
from . import admin

urls = [
    (r"^/admin/?$", admin.RootHandler),
    (r"^/admin/login/?$", admin.LoginPageHandler),
    (r"^/admin/login/([a-fA-F0-9]+)/?$", admin.LoginHandler),
    (r"^/admin/logout/?$", admin.LogoutHandler),
    (r"^/admin/currentuser/?$", admin.CurrentUserHandler),
    (r"^/admin/featured/add/?$", admin.AddFeaturedHandler),
    (r"^/admin/featured/remove/?$", admin.RemoveFeaturedHandler),
    (r"^/(.+\.(?:js|css))$", StaticFileHandler, {"path": "public/"}),
    (r"^/v1/apps/(0x[a-fA-F0-9]{40})/?$", handlers.AppsHandler),
    (r"^/v1/(?:search/)?apps(?:/(featured))?/?$", handlers.SearchAppsHandler)
]

def main():
    app = Application(urls)
    app.start()
