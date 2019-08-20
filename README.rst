jsondt
======

JSON with datetime support.

This module is a light shim around the existing standard library JSON moduile.

It encodes and decodes Python datetime objects as human-readable ISO8601 dates.

    .. image:: https://raw.githubusercontent.com/zeth/jsondt/master/iso8601.jpg

It is a drop-in replacement for standard library JSON, so you can just do:

>>> import jsondt as json

Then carry on with the standard library JSON documentation.

Currently, this module supports only Python 3.7 and above.

Backporting to older versions is possible if there is demand for it.

Simple example
--------------

Here we go:

>>> import jsondt as json
>>> from datetime import datetime
>>> myobject = {'ctime': datetime.now()}
>>> encoded = json.dumps(myobject)
>>> print(encoded)
'{"ctime": "2019-08-19T18:18:25.609815"}'
>>> decoded = json.loads(encoded)
>>> print(decoded)
{'ctime': datetime.datetime(2019, 8, 19, 18, 18, 25, 609815)}
>>> myobject == decoded
True

JavaScript compatible
---------------------

One of the main use cases is to interoperate with JSON produced by
JavaScript in the browser.

Spin up your Javascript console:

>>> const record = {'ctime': new Date()}
>>> const encoded = JSON.stringify(record);
>>> console.log(encoded)
{"ctime":"2019-08-19T17:25:03.547Z"}

Now get that JSON string to Python through your API call or post request
(here's one that we made earlier):

>>> encoded = '{"ctime":"2019-08-19T17:25:03.547Z"}'
>>> import jsondt as json
>>> json.loads(encoded)
{'ctime': datetime.datetime(2019, 8, 19, 17, 25, 3, 547000,
tzinfo=datetime.timezone.utc)}

Say Hello
---------

I am interested in more common use cases for ISO 8601 dates.

If you have an ISO 8601 date in JSON produced by a well known application
or library (in any language) and jsondt does not recognise it, please make
an issue on GitHub and I will see if I can add support.

Control Mode
------------

You probably don't need to care about this bit.

There is a second mode that is semi-automatic instead of fully-automatic.

Imagine we have this strange object:

>>> strange = {'a_date': datetime.datetime(2019, 8, 19, 21, 32, 59, 169730),
...            'b_date': '2018-05-01T07:03:44.560600'}

If we dump it and load it back, it will load both dates as datetime objects.

>>> import jsondt as json
>>> encoded = json.dumps(strange)
>>> decoded = json.loads(encoded)
>>> decoded == strange
False

If however, you prefer the original object back, you can use control mode.

>>> import jsondt as json
>>> encoded = json.dumps(strange, control=True)
>>> decoded = json.loads(encoded, control=True)
>>> decoded == strange
True

The way it works, is that with control=True, it puts a control code
(backslash D) at the start of the encoded date. Like so:

>>> print(encoded)
{"a_date": "\\D2019-08-19T21:32:59.169730",
 "b_date": "2018-05-01T07:03:44.560600"}

Thanks for reading
------------------

If you want more examples, read the supplied tests.
