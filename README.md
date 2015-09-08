# admissions
Admissions form for San Francisco Schoolhouse

The following libraries need to be installed in the directory that is
deployed to App Engine:

lrwxrwxrwx 1 jlowry eng   41 Dec 21 22:22 httplib2 -> /usr/lib/python2.7/dist-packages/httplib2
lrwxrwxrwx 1 jlowry eng   52 Dec 21 15:15 paypalrestsdk -> /usr/local/lib/python2.7/dist-packages/paypalrestsdk
lrwxrwxrwx 1 jlowry eng   49 Nov 17 23:12 pytz -> ../../pytz-2013.8/build/lib.linux-x86_64-2.7/pytz

Properties (e.g. 'admissions_email' are stored in the Config kind in
the Datastore.

Paypal web checkout documentation:

https://developer.paypal.com/webapps/developer/docs/integration/web/web-checkout/

Paypal Sandbox for testing:

https://developer.paypal.com/webapps/developer/docs/classic/lifecycle/ug_sandbox/

Known issues:

#1 templates are HTML quoted when sent as emails. text strings should
 not be quoted. e.g. email sent to parents

#2 timestamps are in UTC. need to be converted to US/Pacific for
 display in templates e.g. email sent to parents

Steps for updating created_date and payment details (e.g. to record a
new payment in the Datastore):

$ ../../google_appengine/remote_api_shell.py admissions-prod

import models
key = ndb.Key(models.Application, '564')
a = key.get()
a.child
a.created_date = a.convert_local_dt_to_utc(2013, 11, 7, 7, 35)
a.paid_amount = 50.0
a.paid_currency = 'USD'
a.put()
