# Stores constants in the Datastore so that you don't need
# to have different values in your code.


from google.appengine.ext import ndb
from google.appengine.api import memcache


app_engine_global_config = {}


class Config(ndb.Model):
  name = ndb.StringProperty(required=True)
  value = ndb.StringProperty(required=True)


def get_property(name, default=None):
  # First check the instance cache. 
  # If it is in instance cache, add to memcache.
  # If not in instance cache, then check memcache.
  # If not in memcache, run a Datastore query to populate memcache.
  global app_engine_global_config
  if name in app_engine_global_config: 
    if app_engine_global_config[name]:
      memcache.add(key=name, value=app_engine_global_config[name], namespace='app_engine_global_config')
      return app_engine_global_config[name]
  value = memcache.get(name, namespace='app_engine_global_config')
  if value is not None:
    return value
  else:
    qry = Config.query()
    results = qry.fetch(50)
    retval = None
    for r in results:
      memcache.add(key=r.name, value=r.value, namespace='app_engine_global_config')
      if r.name == name: retval = r.value
    if retval:
      return retval
    else:
      return default

def initialize_config():
  # Initializes the config in the Datastore with a single item
  # so that we can access via the Admin Console Datastore Viewer
  # to add more entries manually.
  qry = Config.query()
  results = qry.fetch(1)
  if not results:
      config = Config(name="config", value="initialized")
      config.put()


