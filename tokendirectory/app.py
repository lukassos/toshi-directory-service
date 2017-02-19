from . import handlers
from asyncbb.web import Application
from tokenservices.handlers import GenerateTimestamp

urls = [
    (r"^/v1/apps/(0x[a-fA-F0-9]{40})/?$", handlers.AppsHandler),
    (r"^/v1/(?:search/)?apps(?:/(featured))?/?$", handlers.SearchAppsHandler)
]

def main():
    app = Application(urls)
    app.start()
