import os

ROOT_PATH = os.path.dirname(__file__)
TEMPLATE_DIRS = (ROOT_PATH + "/templates",)
MIDDLEWARE_CLASSES = ['google.appengine.ext.ndb.NdbDjangoMiddleware']
