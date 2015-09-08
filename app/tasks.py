import app_engine_config
import jinja2
import models
import os
import paypalrestsdk
import webapp2

from google.appengine.ext import ndb
from google.appengine.api import mail
from google.appengine.ext import ereporter

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates'),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

ereporter.register_logger()


class RecordPayment(webapp2.RequestHandler):

  def get(self):
    self.post()

  def post(self):
    application_id = self.request.get('application_id')
    application_key = ndb.Key(models.Application, application_id)
    application = application_key.get()
    paypalrestsdk.configure({
        'mode': app_engine_config.get_property('mode', default='sandbox'),
        'client_id': app_engine_config.get_property('client_id'),
        'client_secret': app_engine_config.get_property('client_secret') })
    payment = paypalrestsdk.Payment.find(application.paypal_payment_id)
    application.paid_amount = float(payment.transactions[0].amount.total)
    application.paid_currency = payment.transactions[0].amount.currency
    application.put()
    url = 'http://' + os.environ['HTTP_HOST'] + '/export/application?application_id=' + application_id
    template_values = { 'application': application, 'application_id': application_id,
                        'url': url }
    notify_template = JINJA_ENVIRONMENT.get_template('notify.txt')
    notify_mail_body = notify_template.render(template_values)
    mail.send_mail(sender=app_engine_config.get_property('mail_sender', default='jlowry@sfschoolhouse.org'),
                   to=app_engine_config.get_property('admissions_email', default='jlowry@sfschoolhouse.org'),
                   subject='Payment received for: %s' % application.child,
                   body=notify_mail_body)
        

class FindFailedPayments(webapp2.RequestHandler):

  def get(self):
    self.post()

  def post(self):
    qry = models.Application.query()
    qry.filter(models.Application.paid_amount == 0)
    results = qry.fetch(500)
    if results:
      url_prefix = 'http://' + os.environ['HTTP_HOST'] + '/export/application?application_id='
      template_values = { 'application': results, 'url_prefix': url_prefix }
      failed_template = JINJA_ENVIRONMENT.get_template('failed.txt')
      failed_mail_body = failed_template.render(template_values)
      mail.send_mail(sender='jlowry@sfschoolhouse.org', to='jlowry@sfschoolhouse.org',
                     subject='Failed payments for SF Schoolhouse applications',
                     body=failed_mail_body)
        

class SaveApplication(webapp2.RequestHandler):

  def get(self):
    self.post()

  def post(self):
    application_id = self.request.get('application_id')
    application_key = ndb.Key(models.Application, application_id)
    application = application_key.get()
    template_values = {'application': application, 'application_id': application_id}
    notify_template = JINJA_ENVIRONMENT.get_template('notify-for-new-application.txt')
    notify_mail_body = notify_template.render(template_values)
    mail.send_mail(sender=app_engine_config.get_property('mail_sender', default='jlowry@sfschoolhouse.org'),
                   to=application.email_1,
                   cc=app_engine_config.get_property('admissions_email', default='jlowry@sfschoolhouse.org'),
                   subject='Application to San Francisco Schoolhouse: %s' % application.child,
                   body=notify_mail_body)


app = webapp2.WSGIApplication([('/tasks/record_payment', RecordPayment),
                               ('/tasks/find_failed_payments', FindFailedPayments),
                               ('/tasks/save_application', SaveApplication)], 
                              debug=True)
