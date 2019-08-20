#   Copyright 2019 Zeth Green
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""JSON with datetime support.

This module is a light shim around the existing standard library JSON moduile.
It just adds support for encoding and decoding Python datetime objects. It is
a drop-in replacement, so you can just do:

    >>> import jsondt as json

Then carry on with the standard library JSON documentation.

Want more? Okay.

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

Want even more? Spin up your Javascript console:

   >>> const record = {'ctime': new Date()}
   >>> const encoded = JSON.stringify(record);
   >>> console.log(encoded)
   {"ctime":"2019-08-19T17:25:03.547Z"}

Now get that to Python through your API call (here we will just cut and paste):

   >>> encoded = '{"ctime":"2019-08-19T17:25:03.547Z"}'
   >>> import jsondt as json
   >>> json.loads(encoded)
   {'ctime': datetime.datetime(2019, 8, 19, 17, 25, 3, 547000,
   tzinfo=datetime.timezone.utc)}

Control Mode
------------

You probably don't need to care about this bit.

There is a second mode that is semi-automatic instead of fully-automatic.

Imagine we have this strange object:

   >>> strange = {'a_date': datetime.datetime(2019, 8, 19, 21, 32, 59, 169730),
   ...            'b_date': '2018-05-01T07:03:44.560600'}

If we dump it and load it back, it will load both dates as datetime objects.

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

The original documentation follows:
---
"""

import json
from datetime import datetime
from typing import Tuple, Callable, Any, Dict, Union, Iterable, TextIO

__version__ = '1.0.0'

JPair = Tuple[str, Any]
JObject = Dict[str, Any]
JParser = Callable[[str], Any]
JSeparators = Tuple[str, str]
JObjectHook = Callable[[Any], JObject]
JObjectPairsHook = Callable[[Iterable[JPair]], JObject]


class JSONEncoder(json.JSONEncoder):
    """Like standard library encoder but with encoding of datetime objects.

    +-------------------+---------------+
    | Python            | JSON          |
    +===================+===============+
    | datetime.datetime | ISO 8601 date |
    +-------------------+---------------+

    If ``control`` is True (False is the default), then a control
    character (\\D) will be prepended to the date.

    The original documentation follows:
    """
    __doc__ += json.JSONEncoder.__doc__  # type: ignore

    def __init__(
            self,
            *,
            skipkeys: bool = False,
            ensure_ascii: bool = True,
            check_circular: bool = True,
            allow_nan: bool = True,
            sort_keys: bool = False,
            indent: Union[int, None] = None,
            separators: Union[JSeparators, None] = None,
            default: Union[JObjectHook, None] = None,
            control: bool = False):
        self.control = control
        self.second_default = None
        if default:
            self.second_default = default
        super().__init__(
            skipkeys=skipkeys,
            ensure_ascii=ensure_ascii,
            check_circular=check_circular,
            allow_nan=allow_nan,
            sort_keys=sort_keys,
            indent=indent,
            separators=separators,
            default=None)

    # pylint: disable=method-hidden
    def default(self, o: Any) -> Union[str, JObject, Any]:
        if isinstance(o, datetime):
            iso_date = o.isoformat()
            if self.control:
                return r'\D' + iso_date
            return iso_date
        if self.second_default:
            return self.second_default(o)
        return super().default(o)


class JSONDecoder(json.JSONDecoder):
    """Like standard library decoder but with decoding of datetime objects.

    +---------------+-------------------+
    | JSON          | Python            |
    +===============+===================+
    | ISO 8601 date | datetime.datetime |
    +---------------+-------------------+

    If ``control`` is True (False is the default), then a control
    character (\\D) is necessary to recognise a date.

    The original documentation follows:

    """
    __doc__ += json.JSONDecoder.__doc__  # type: ignore

    def __init__(
            self,
            *,
            object_hook: Union[JObjectHook, None] = None,
            parse_float: Union[JParser, None] = None,
            parse_int: Union[JParser, None] = None,
            parse_constant: Union[JParser, None] = None,
            strict: bool = True,
            object_pairs_hook: Union[JObjectPairsHook, None] = None,
            control: bool = False,
            **kwargs: Any):
        self.control = control
        self.second_hook = object_pairs_hook
        self.third_hook = object_hook
        super().__init__(
            object_pairs_hook=self._deserialise_datetimes,
            parse_float=parse_float,
            parse_int=parse_int,
            parse_constant=parse_constant,
            strict=strict,
            **kwargs
        )

    def _deserialise_datetimes(
            self,
            ordered_pairs: Iterable[JPair]) -> JObject:
        """
        Replace matching strings with datetime objects.

        Go through each of the key/values in the JSON object and
        replace any matching strings with datetime.datetime objects.
        """
        result = {}
        for key, value in ordered_pairs:
            result[key] = self._check_value(value)

        if self.second_hook:
            return self.second_hook(result.items())
        if self.third_hook:
            return self.third_hook(result)
        return result

    def _check_value(self, value: Any) -> Any:
        """Parse the value into a datetime object,
        if the value is a string and starts with the control code."""
        if not isinstance(value, str):
            return value
        if value[:2] == r'\D':
            return self._from_iso_format(value[2:])
        if self.control:
            return value
        return self._check_for_date(value)

    def _check_for_date(self, value: str) -> Union[str, datetime]:
        """Parse the value into a datetime object,
        if the value starts with YYYY-MM-DD."""
        if value[:4].isnumeric():
            if value[4] == '-':
                if value[7] == '-':
                    return self._from_iso_format(value)
        return value

    @staticmethod
    def _from_iso_format(value: str) -> datetime:
        """Parse a string to a datetime."""
        if value.endswith('Z'):
            value = value[:-1] + '+00:00'
        return datetime.fromisoformat(value)


def dump(
        obj: Any,
        flp: TextIO,
        *,
        skipkeys: bool = False,
        ensure_ascii: bool = True,
        check_circular: bool = True,
        allow_nan: bool = True,
        cls: Union[type, None] = None,
        indent: Union[int, None] = None,
        separators: Union[JSeparators, None] = None,
        default: Union[JObjectHook, None] = None,
        sort_keys: bool = False,
        control: bool = False,
        **kwargs: Any) -> None:
    """
    Same as the standard dump except that datetime objects are serialised
    to ISO 8601 dates.

    If ``control`` is True (False is the default), then a control
    character (\\D) will be prepended to the date.

    The original documentation follows:

    """
    if not cls:
        cls = JSONEncoder

    return json.dump(
        obj,
        flp,
        control=control,
        cls=cls,
        skipkeys=skipkeys,
        ensure_ascii=ensure_ascii,
        check_circular=check_circular,
        allow_nan=allow_nan,
        indent=indent,
        separators=separators,
        default=default,
        sort_keys=sort_keys,
        **kwargs)


def dumps(
        obj: Any,
        *,
        skipkeys: bool = False,
        ensure_ascii: bool = True,
        check_circular: bool = True,
        allow_nan: bool = True,
        cls: Union[type, None] = None,
        indent: Union[int, None] = None,
        separators: Union[JSeparators, None] = None,
        default: Union[JObjectHook, None] = None,
        sort_keys: bool = False,
        control: bool = False,
        **kwargs: Any) -> str:
    """
    Same as the standard dumps except that datetime objects are serialised
    to ISO 8601 dates.

    If ``control`` is True (False is the default), then a control
    character (\\D) will be prepended to the date.

    The original documentation follows:


    """

    if not cls:
        cls = JSONEncoder

    return json.dumps(
        obj,
        control=control,
        skipkeys=skipkeys,
        ensure_ascii=ensure_ascii,
        check_circular=check_circular,
        allow_nan=allow_nan,
        cls=cls,
        indent=indent,
        separators=separators,
        default=default,
        sort_keys=sort_keys,
        **kwargs)


def load(
        fp: TextIO,
        *,
        cls: Union[type, None] = None,
        object_hook: Union[JObjectHook, None] = None,
        parse_float: Union[JParser, None] = None,
        parse_int: Union[JParser, None] = None,
        parse_constant: Union[JParser, None] = None,
        object_pairs_hook: Union[JObjectPairsHook, None] = None,
        control: bool = False,
        **kwargs: Any) -> Any:
    """
    Same as the standard load except that ISO 8601 dates are decoded
    to datetime objects.

    If ``control`` is True (False is the default), then a control
    character (\\D) is necessary to recognise a date.

    The original documentation follows:

    """
    # pylint: disable=invalid-name

    if not cls:
        cls = JSONDecoder

    return json.load(
        fp,
        cls=cls,
        object_hook=object_hook,
        parse_float=parse_float,
        parse_int=parse_int,
        parse_constant=parse_constant,
        object_pairs_hook=object_pairs_hook,
        control=control,
        **kwargs)


def loads(
        s: str,
        *,
        cls: Union[type, None] = None,
        object_hook: Union[JObjectHook, None] = None,
        parse_float: Union[JParser, None] = None,
        parse_int: Union[JParser, None] = None,
        parse_constant: Union[JParser, None] = None,
        object_pairs_hook: Union[JObjectPairsHook, None] = None,
        control: bool = False,
        **kwargs: Any) -> Any:
    """
    Same as the standard loads except that ISO 8601 dates are decoded
    to datetime objects.

    If ``control`` is True (False is the default), then a control
    character (\\D) is necessary to recognise a date.

    The original documentation follows:

    """
    # pylint: disable=invalid-name

    if not cls:
        cls = JSONDecoder

    return json.loads(
        s,
        cls=cls,
        object_hook=object_hook,
        parse_float=parse_float,
        parse_int=parse_int,
        parse_constant=parse_constant,
        object_pairs_hook=object_pairs_hook,
        control=control,
        **kwargs)


# pylint: disable=no-member
dump.__doc__ += json.dump.__doc__  # type: ignore
dumps.__doc__ += json.dumps.__doc__  # type: ignore
load.__doc__ += json.load.__doc__  # type: ignore
loads.__doc__ += json.loads.__doc__  # type: ignore
__doc__ += json.__doc__
