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

"""Tests for Jsondt."""

import unittest
import io
from datetime import datetime, timezone
from decimal import Decimal

import jsondt

WORF = {
    'name': 'Worf',
    'birthday': datetime(2340, 12, 9, 3, 32),
    'postings': {
        'USS Hawk': datetime(2358, 2, 3, 8, 0),
        'USS Enterprise D': datetime(2364, 2, 26, 6, 6),
        'Deep Space 9': datetime(2372, 1, 5, 4, 8),
        'USS Enterprise E': datetime(2373, 11, 23, 3, 35),
        'Federation Ambassador to QonoS': datetime(2375, 11, 26, 5, 31)
    },
    'children': 1
}

WORF_TEXT_CONTROL = (
    '{"name": "Worf", "birthday": "\\\\D2340-12-09T03:32:00", '
    '"postings": {"USS Hawk": "\\\\D2358-02-03T08:00:00", '
    '"USS Enterprise D": "\\\\D2364-02-26T06:06:00", '
    '"Deep Space 9": "\\\\D2372-01-05T04:08:00", '
    '"USS Enterprise E": "\\\\D2373-11-23T03:35:00", '
    '"Federation Ambassador to QonoS": "\\\\D2375-11-26T05:31:00"}, '
    '"children": 1}'
)

WORF_TEXT = (
    '{"name": "Worf", "birthday": "2340-12-09T03:32:00", '
    '"postings": {"USS Hawk": "2358-02-03T08:00:00", '
    '"USS Enterprise D": "2364-02-26T06:06:00", '
    '"Deep Space 9": "2372-01-05T04:08:00", '
    '"USS Enterprise E": "2373-11-23T03:35:00", '
    '"Federation Ambassador to QonoS": "2375-11-26T05:31:00"}, '
    '"children": 1}'
)

RESTAURANT = {
    'name': 'Steak House',
    'products': {'beer', 'chips', 'ketchup', 'steak', 'wine'},
    'date': datetime(2019, 8, 19, 10, 14, 9, 250255)
}

RESTAURANT_TEXT = (
    '{"name": "Steak House", "products": '
    '["beer", "chips", "ketchup", "steak", "wine"], '
    '"date": "2019-08-19T10:14:09.250255"}'
)

MENU_ITEM = {
    'name': 'ruishampurilainen',
    'price': Decimal('4.95'),
    'date': datetime(2019, 8, 19, 11, 20, 44, 107448)
}

MENU_ITEM_STR = (
    '{"name": "ruishampurilainen", "price": "4.95", '
    '"date": "2019-08-19T11:20:44.107448"}'
)


class TestDump(unittest.TestCase):
    """Test the dump functions."""
    def test_dump(self):
        """Should work for a blank object."""
        sio = io.StringIO()
        jsondt.dump({}, sio)
        self.assertEqual(sio.getvalue(), '{}')

    def test_dumps(self):
        """Should work for a blank object."""
        self.assertEqual(jsondt.dumps({}), '{}')

    def test_encode_truefalse(self):
        """Should still work for a complicated example
        that has nothing to do with datetimes."""
        self.assertEqual(
            jsondt.dumps(
                {True: False, False: True},
                sort_keys=True
            ),
            '{"false": true, "true": false}')
        self.assertEqual(
            jsondt.dumps(
                {2: 3.0, 4.0: 5, False: 1, 6: True},
                sort_keys=True
            ),
            '{"false": 1, "2": 3.0, "4.0": 5, "6": true}')

    def test_dump_datetime(self):
        """Datetime should dump with control code."""
        now = datetime.fromisoformat("2019-08-17T07:54:22.175")
        record = {'ctime': now}
        self.assertEqual(
            jsondt.dumps(record, control=True),
            '{"ctime": "\\\\D2019-08-17T07:54:22.175000"}')

    def test_dump_datetime_control(self):
        """Datetime should dump without control code."""
        now = datetime.fromisoformat("2019-08-17T07:54:22.175")
        record = {'ctime': now}
        self.assertEqual(
            jsondt.dumps(record),
            '{"ctime": "2019-08-17T07:54:22.175000"}')

    def test_dump_unknown_type(self):
        """Should still reject completely unknown types."""
        record = {'names': {'Zeth', 'Green'}}
        with self.assertRaises(TypeError):
            jsondt.dumps(record)

    def test_dump_embed_obj(self):
        """Should dump a dictionary of dictionaries."""
        record = jsondt.dumps(WORF)
        self.assertEqual(
            record,
            WORF_TEXT
        )

    def test_dump_embed_obj_control(self):
        """Should dump a dictionary of dictionaries."""
        record = jsondt.dumps(WORF, control=True)
        self.assertEqual(
            record,
            WORF_TEXT_CONTROL
        )

    def test_dump_subclass(self):
        """Should be able to subclass JSONEncoder."""
        class SetEncoder(jsondt.JSONEncoder):
            """Little Encoder that supports sets."""
            # pylint: disable=method-hidden
            def default(self, o):
                if isinstance(o, set):
                    newlist = list(o)
                    newlist.sort()
                    return newlist
                return super().default(o)

        stringified = jsondt.dumps(RESTAURANT, cls=SetEncoder)

        self.assertEqual(
            stringified,
            RESTAURANT_TEXT,
        )

    def test_dump_second_default(self):
        """Should be able to provide a second default."""
        def default(obj):
            if isinstance(obj, set):
                newlist = list(obj)
                newlist.sort()
                return newlist
            raise TypeError

        stringified = jsondt.dumps(RESTAURANT, default=default)

        self.assertEqual(
            stringified,
            RESTAURANT_TEXT,
        )


class TestLoad(unittest.TestCase):
    """Test the load functions."""
    def test_load(self):
        """Should work for a blank object."""
        sio = io.StringIO('{}')
        self.assertEqual(jsondt.load(sio), {})

    def test_loads(self):
        """Should work for a blank object."""
        self.assertEqual(jsondt.loads('{}'), {})

    def test_load_datetime(self):
        """Should load a datetime without a control code."""
        record_text = '{"ctime": "2019-08-17T07:54:22.175000"}'
        record = jsondt.loads(record_text)
        self.assertEqual(
            record,
            {'ctime': datetime(2019, 8, 17, 7, 54, 22, 175000)}
        )

    def test_load_datetime_control(self):
        """Should load a datatime that has a control code."""
        record_text = '{"ctime": "\\\\D2019-08-17T07:54:22.175000"}'
        record = jsondt.loads(record_text, control=True)
        self.assertEqual(
            record,
            {'ctime': datetime(2019, 8, 17, 7, 54, 22, 175000)}
        )

    def test_load_datetime_no_control(self):
        """Should load a datatime that has a control code
        even with control=False."""
        record_text = '{"ctime": "\\\\D2019-08-17T07:54:22.175000"}'
        record = jsondt.loads(record_text)
        self.assertEqual(
            record,
            {'ctime': datetime(2019, 8, 17, 7, 54, 22, 175000)}
        )

    def test_dont_load_datetime_no_control(self):
        """Should not a datatime that has no a control code
        and control=True."""
        record_text = '{"ctime": "2019-08-17T07:54:22.175000"}'
        record = jsondt.loads(record_text, control=True)
        self.assertEqual(
            record,
            {'ctime': '2019-08-17T07:54:22.175000'}
        )

    def test_load_datetime_controlmix_fields(self):
        """Should load control code datetimes in control mode
        and with an extra field."""
        record_text = (
            '{"product": "Fish", '
            '"bestbefore": "\\\\D2019-08-17T16:28:32.103179"}'
        )
        record = jsondt.loads(record_text, control=True)
        self.assertEqual(
            record,
            {
                'product': 'Fish',
                'bestbefore': datetime(2019, 8, 17, 16, 28, 32, 103179)
            }
        )

    def test_load_datetime_with_other_fields(self):
        """Should load with a non-datetime field."""
        rtext = '{"name": "Zeth", "mtime": "\\\\D2019-08-17T16:25:28.659913"}'
        record = jsondt.loads(rtext)
        self.assertEqual(
            record,
            {
                'name': 'Zeth',
                'mtime': datetime(2019, 8, 17, 16, 25, 28, 659913)
            }
        )

    def test_load_datetime_with_embed_obj(self):
        """Should load datetimes inside objects inside objects."""
        record = jsondt.loads(WORF_TEXT)
        self.assertEqual(
            record,
            WORF
        )

    def test_load_datetime_with_embed_obj_control(self):
        """Should load datetimes inside objects inside objects
        in control mode."""
        record = jsondt.loads(WORF_TEXT_CONTROL, control=True)
        self.assertEqual(
            record,
            WORF
        )

    def test_load_with_second_hook(self):
        """Load with an extra object_pairs_hook."""
        def derialise_decimal(ordered_pairs):
            """
            Replace matching strings with decimal objects.
            """
            result = {}
            for key, value in ordered_pairs:
                if key == 'price':
                    result[key] = Decimal(value)
                else:
                    result[key] = value
            return result

        menu_item = jsondt.loads(
            MENU_ITEM_STR,
            object_pairs_hook=derialise_decimal
        )
        self.assertEqual(menu_item, MENU_ITEM)

    def test_load_with_third_hook(self):
        """Load with an extra object_hook."""
        def derialise_decimal(obj):
            """
            Replace matching strings with decimal objects.
            """
            result = {}
            for key, value in obj.items():
                if key == 'price':
                    result[key] = Decimal(value)
                else:
                    result[key] = value
            return result

        menu_item = jsondt.loads(
            MENU_ITEM_STR,
            object_hook=derialise_decimal
        )
        self.assertEqual(menu_item, MENU_ITEM)

    def test_load_with_z_timezone(self):
        """Z is shorthand for UTC, especially used by JavaScript."""
        string_date = '{"ctime":"2019-08-19T19:35:59.999Z"}'
        object_date = jsondt.loads(string_date)
        self.assertEqual(
            object_date,
            {'ctime': datetime(
                2019, 8, 19, 19, 35, 59, 999000,
                tzinfo=timezone.utc
            )}
        )


if __name__ == "__main__":
    unittest.main()
