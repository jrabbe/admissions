import datetime
import pytz

from google.appengine.ext import ndb


class Counter(ndb.Model):
  value = ndb.IntegerProperty()


class Application(ndb.Model):
  # key is an application ID string.
  created_date = ndb.DateTimeProperty(auto_now_add=True)
  child = ndb.StringProperty(verbose_name='Child name', required=True)
  gender = ndb.StringProperty(verbose_name= 'Child gender', required=True, choices=['male', 'female'])
  parent_1 = ndb.StringProperty(verbose_name='Parent 1 name', required=True, indexed=False)
  parent_2 = ndb.StringProperty(verbose_name='Parent 2 name', indexed=False)
  address = ndb.TextProperty(verbose_name='Parent address', required=True, indexed=False)
  telephone = ndb.StringProperty(verbose_name='Parent phone number', required=True, indexed=False)
  email_1 = ndb.StringProperty(verbose_name='Parent 1 email', required=True, indexed=False)
  email_2 = ndb.StringProperty(verbose_name='Parent 2 email', indexed=False)
  birthday = ndb.DateProperty(verbose_name='Child birth date', required=True)
  current_grade = ndb.StringProperty(verbose_name= 'Child current grade', required=True,
                                     choices=['Pre-K', 'Kindergarten', 'Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 'Grade 5'])
  current_school = ndb.StringProperty(verbose_name='Name of child\'s current school', indexed=False)
  school_address = ndb.TextProperty(verbose_name='Address of child\'s current school')
  essay_why = ndb.TextProperty(verbose_name='Why do you want your child to attend the Schoolhouse')
  describe_child = ndb.TextProperty(verbose_name='Please tell us about your child so we can better get to know him or her')
  essay_how = ndb.TextProperty(verbose_name='Please describe how your family will participate in the Schoolhouse')
  paid_amount = ndb.FloatProperty()
  paid_currency = ndb.StringProperty()
  # We have to save the Paypal payment ID in the user session since it is not passed back in the return URL:
  # http://stackoverflow.com/questions/18543958/paypal-rest-api-how-to-retrieve-payment-id-after-user-has-approved-the-payment
  # http://stackoverflow.com/questions/20448664/implementation-of-paypal-rest-api-in-python
  paypal_payment_id = ndb.StringProperty()

  def convert_local_dt_to_utc(self, year, month, day, hour, minute):
    # created_date is set as UTC by App Engine
    # If you want to manually set created_date, you must use a naive datetime object,
    # i.e. has no associated tzinfo, but has the UTC-localized time.
    utc = pytz.UTC
    pacific = pytz.timezone('US/Pacific')
    pacific_date = pacific.localize(datetime.datetime(year, month, day, hour, minute))
    utc_aware = pacific_date.astimezone(utc)
    year, month, day, hour, minute = utc_aware.timetuple()[:5]
    utc_naive = datetime.datetime(year, month, day, hour, minute)
    return utc_naive

