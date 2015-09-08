import jinja2
import logging
import models
import os
import pytz
import time
import webapp2

from datetime import datetime

from google.appengine.ext import ndb

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates'),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class DisplayApplication(webapp2.RequestHandler):

  def get(self):
    application_id = self.request.get('application_id')
    application_key = ndb.Key(models.Application, application_id)
    application = application_key.get()
    template_values = { 'application': application, 'application_id': application_id }
    logging.info(application.child)
    template = JINJA_ENVIRONMENT.get_template('application.html')
    self.response.write(template.render(template_values))


class ListApplications(webapp2.RequestHandler):

  @staticmethod
  def entity_key_as_int(entity):
    return int(entity.key.id())

  @staticmethod
  def timestamp_as_int(entity):
    if entity.created_date:
      return time.mktime(entity.created_date.timetuple())
    else:
      return 0

  def get(self):
    # Cannot order by key since it is a string
    # Cannot order by created_date since entities without this field are not returned
    # Therefore, we sort in memory
    qry = models.Application.query()
    results = qry.fetch(500)
    applications = sorted(results, key=ListApplications.timestamp_as_int, reverse=True)
    utc = pytz.timezone('UTC')
    for a in applications:
      if a.created_date:
        utc_date = utc.localize(a.created_date)
        a.created_date_pacific = utc_date.astimezone(pytz.timezone('US/Pacific'))
      else:
        a.created_date_pacific = None
    template_values = { 'applications': applications }
    template = JINJA_ENVIRONMENT.get_template('list.html')
    self.response.out.write(template.render(template_values))


class Export(webapp2.RequestHandler):

  def get(self):
    qry = models.Application.query()
    results = qry.fetch(500)
    template_values = { 'applications': results, }
    self.response.out.write(render_to_string('export.html', template_values))


app = webapp2.WSGIApplication([('/export/application', DisplayApplication),
                               ('/export/export', Export),
                               ('/export/list', ListApplications)], debug=True)

