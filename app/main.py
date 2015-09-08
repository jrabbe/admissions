import app_engine_config
import logging
import models
import os
import paypalrestsdk
import sys
import time
import traceback
import urllib
import webapp2

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.ext import ndb
from google.appengine.api import taskqueue
from google.appengine.ext import ereporter

from django import forms
from django.core.validators import validate_email
from django.template.loader import render_to_string

from paypalrestsdk import ResourceNotFound

ereporter.register_logger()


def url_prefix():
  return 'http://' + os.environ['HTTP_HOST']


class ApplicationForm(forms.Form):
  child = forms.CharField(required=True)
  gender = forms.ChoiceField(choices=[('male', 'male'), ('female', 'female')])
  parent_1 = forms.CharField(required=True)
  parent_2 = forms.CharField(required=False)
  address = forms.CharField(required=True)
  telephone = forms.CharField(required=True)
  email_1 = forms.EmailField(required=True)
  email_2 = forms.EmailField(required=False)
  birthday = forms.DateField(required=True)
  current_grade = forms.ChoiceField(choices=[('Pre-K', 'Pre-K'), ('Kindergarten', 'Kindergarten'), ('Grade 1', 'Grade 1'),
                                             ('Grade 2', 'Grade 2'), ('Grade 3', 'Grade 3'), ('Grade 4', 'Grade 4'), 
                                             ('Grade 5', 'Grade 5')])
  current_school = forms.CharField(required=False)
  school_address = forms.CharField(required=False)
  essay_why = forms.CharField(required=False)
  describe_child = forms.CharField(required=False)
  essay_how = forms.CharField(required=False)


class SubmitPage(webapp2.RequestHandler):
  
  @ndb.transactional
  def get_application_id(self):
    counter_key = ndb.Key(models.Counter, 'application_id')
    counter = counter_key.get()
    if not counter:
      counter = models.Counter(id='application_id', value=1)
    else:
      counter.value += 1
    counter.put()
    return counter.value

  @ndb.transactional
  def save_application(self):
    self.application.put()
    taskqueue.add(url='/tasks/save_application', params={'application_id': self.application_id})

  def get(self):
    if self.request.get('testdata'):
      default_data= {'child': 'foo',
                     'gender': 'male',
                     'parent_1': 'parent 1',
                     'parent_2': 'parent 2',
                     'address': 'address',
                     'telephone': '555 1234',
                     'email_1': 'jlowry@gmail.com',
                     'email_2': 'jlowry@alexium.com',
                     'birthday': '07/09/2006',
                     'current_grade': 'Kindergarten',
                     'current_school': 'Sunset',
                     'school_address': 'Lawton',
                     'essay_why': 'why',
                     'describe_child': 'child',
                     'essay_how': 'how'}
      data = ApplicationForm(default_data)
    else:
      data = ApplicationForm()
    template_values = { 'form': data, 'application_id': self.get_application_id() }
    self.response.out.write(render_to_string('form.html', template_values))

  def post(self):
    data = ApplicationForm(data=self.request.POST)
    self.application_id = self.request.get('application_id')
    if data.is_valid():
      email_2 = data.cleaned_data.get('email_2')
      # email property cannot be an empty string
      if not email_2: email_2 = None
      # protect against double form submission with a unique integer, 
      # that becomes the application ID.
      self.application = models.Application(
        id=self.application_id,
        child=data.cleaned_data.get('child'),
        gender=data.cleaned_data.get('gender'),
        parent_1=data.cleaned_data.get('parent_1'),
        parent_2=data.cleaned_data.get('parent_2'),
        address=data.cleaned_data.get('address'),
        telephone=data.cleaned_data.get('telephone'),
        email_1=data.cleaned_data.get('email_1'),
        email_2=email_2,
        birthday=data.cleaned_data.get('birthday'),
        current_grade=data.cleaned_data.get('current_grade'),
        current_school=data.cleaned_data.get('current_school'),
        school_address=data.cleaned_data.get('school_address'),
        essay_why=data.cleaned_data.get('essay_why'),
        describe_child=data.cleaned_data.get('describe_child'),
        essay_how=data.cleaned_data.get('essay_how'))
      try:
        self.save_application()
      except:
        logging.info(''.join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])))
        logging.error('Application not saved.')
        self.response.out.write(render_to_string('error.html', {'errstr': 'Your application was not saved. Please try again.'}))
        return self.response

      # Call the request handler directly rather than send a redirect to the client
      # in order to avoid a round trip between client and server.
      payment = CreatePayment(request=self.request, response=self.response)
      return payment.get()

    else:
      template_values = { 'form': data, 'application_id': self.application_id }
      self.response.out.write(render_to_string('form.html', template_values))
      return self.response


class CreatePayment(webapp2.RequestHandler):
  """Redirects user to Paypal for payment approval. 

  A link to this URL can be sent to someone that did not pay first time around."""

  # https://developer.paypal.com/webapps/developer/docs/api/#transaction-object
  def create_payment(self, application):
    return paypalrestsdk.Payment({
        'intent': 'sale',
        'payer': { 'payment_method': 'paypal' },
        'redirect_urls': {
          'return_url': url_prefix() + '/payment/execute?application_id=' + application.key.id(),
          'cancel_url': url_prefix() + '/payment/cancel?application_id=' + application.key.id() },
        'transactions': [{
            'item_list': {
              'items': [{
                  # Name displays in the order summary display in the Paypal approval form
                  # Truncated to approx 50 chars in display, though full name can be seen in mouse-over.
                  'name': 'Application for SF Schoolhouse: %s (%s)' % (application.child, application.key.id()),
                  'price': '50.00',
                  'currency': 'USD',
                  'quantity': 1 }]},
            'amount': {
              'total': '50.00',
              'currency': 'USD' },
            # description field appears in email "Notification of payment received" sent by Paypal but not order summary.
            'description': 'Application for admission to SF Schoolhouse for %s (%s).' % (application.child, application.key.id())}]})

  def get(self):
    # Redirect the user to the Paypal approval URL.
    # Return a response object since this request handler can be called from within the app.
    application_id = self.request.get('application_id')
    application_key = ndb.Key(models.Application, application_id)
    application = application_key.get()

    paypalrestsdk.configure({
        'mode': app_engine_config.get_property('mode', default='sandbox'),
        'client_id': app_engine_config.get_property('client_id'),
        'client_secret': app_engine_config.get_property('client_secret') })

    try:
      payment = self.create_payment(application)
      if payment.create():
        logging.info('Payment created successfully: %s' % (payment.id))
        application.paypal_payment_id = payment.id
        application.put()
        for link in payment.links:
          if link.method == 'REDIRECT':
            logging.info('Redirect for approval: %s'% (link.href))
            return self.redirect(str(link.href))
        logging.error('No approval URL')
      else:
        print('Error while creating payment.')
        logging.error(payment.error)
    except:
      logging.info(''.join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])))
      logging.error('Payment failed.')

    errstr = ('Your application has been saved, but an error occurred '
              'while we were trying to redirect you to Paypal for payment. '
              'We will contact you shortly to resolve this problem.')
    self.response.out.write(render_to_string('error.html', {'errstr': errstr}))
    return self.response


class ExecutePayment(webapp2.RequestHandler):

  def get(self):
    payer_id = self.request.get('PayerID')
    application_id = self.request.get('application_id')
    application_key = ndb.Key(models.Application, application_id)
    application = application_key.get()

    paypalrestsdk.configure({
        'mode': app_engine_config.get_property('mode', default='sandbox'),
        'client_id': app_engine_config.get_property('client_id'),
        'client_secret': app_engine_config.get_property('client_secret') })

    payment = None
    if payer_id:
      try:
        payment = paypalrestsdk.Payment.find(application.paypal_payment_id)
      except ResourceNotFound as error:
        logging.error('Payment not found for Payment ID: %s' % (application.paypal_payment_id))
    else:
      logging.error('No Payer ID.')

    payment_successful = False
    if payment:
      try:
        payment_successful = payment.execute({'payer_id': payer_id})
      except:
        logging.info(''.join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])))
        logging.error('Payment execution failed.')

    if payment_successful:
      for i in range(0, 3):
        try:
          taskqueue.add(url='/tasks/record_payment', params={'application_id': application_id})
        except taskqueue.TransientError:
          logging.info(''.join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])))
          logging.error('Add task failed due to TransientError')
          time.sleep(1)
        else:
          logging.info('Payment executed successfully: %s' % (payment))
          url = str(url_prefix() + '/html/success.html')
          return self.redirect(url)
    else:
      logging.error(payment.error)

    errstr = ('Your application has been saved, but an error occurred '
              'during the payment process. We will contact you shortly '
              'to resolve this problem. ')
    self.response.out.write(render_to_string('error.html', {'errstr': errstr}))
    return self.response


class CancelPayment(webapp2.RequestHandler):
  """Called if user hits Cancel on the Paypal site."""

  def get(self):
    application_id = self.request.get('application_id')
    logging.error('Payment canceled for application: %s' % (application_id))
    url = str(url_prefix() + '/html/failure.html')
    self.redirect(url)


app = webapp2.WSGIApplication([('/submit', SubmitPage),
                               ('/payment/execute', ExecutePayment),
                               ('/payment/cancel', CancelPayment),
                               ('/payment/create', CreatePayment),],
                              debug=True)


