# admissions
Admissions form for San Francisco Schoolhouse

The following libraries need to be installed in the directory that is
deployed to App Engine:

httplib2 -> /usr/lib/python2.7/dist-packages/httplib2

paypalrestsdk -> /usr/local/lib/python2.7/dist-packages/paypalrestsdk

pytz -> ../../pytz-2013.8/build/lib.linux-x86_64-2.7/pytz

Properties (e.g. 'admissions_email') are stored in the Config kind in
the Datastore.

Paypal web checkout documentation:

https://developer.paypal.com/webapps/developer/docs/integration/web/web-checkout/

Paypal Sandbox for testing:

https://developer.paypal.com/webapps/developer/docs/classic/lifecycle/ug_sandbox/

Known issues:

1. templates are HTML quoted when sent as emails. text strings should
not be quoted. e.g. email sent to parents

2. timestamps are in UTC. need to be converted to US/Pacific for
display in templates e.g. email sent to parents

