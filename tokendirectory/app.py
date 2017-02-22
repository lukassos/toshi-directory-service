from . import handlers
from asyncbb.web import Application
from tokenservices.handlers import GenerateTimestamp
from tornado.web import StaticFileHandler
from . import admin
from . import registry

urls = admin.urls + registry.urls + [
    # auth
    (r"^/login/?$", handlers.LoginPageHandler),
    (r"^/logout/?$", handlers.LogoutHandler),
    (r"^/currentuser/?$", handlers.CurrentUserHandler),

    # static
    (r"^/(.+\.(?:js|css))$", StaticFileHandler, {"path": "public/"}),

    # api
    (r"^/v1/apps/(0x[a-fA-F0-9]{40})/?$", handlers.AppsHandler),
    (r"^/v1/(?:search/)?apps(?:/(featured))?/?$", handlers.SearchAppsHandler)
]

def main():
    app = Application(urls)
    app.start()
