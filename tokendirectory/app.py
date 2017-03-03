import asyncbb.web
import os
from . import handlers
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
    (r"^/v1/(?:search/)?apps(?:/(featured))?/?$", handlers.SearchAppsHandler),

    # reputation update endpoint
    (r"^/v1/reputation/?$", handlers.ReputationUpdateHandler)
]

class Application(asyncbb.web.Application):

    def process_config(self):
        config = super(Application, self).process_config()

        if 'REPUTATION_SERVICE_ID' in os.environ:
            config['reputation'] = {'id': os.environ['REPUTATION_SERVICE_ID'].lower()}

        return config

def main():
    app = Application(urls)
    app.start()
