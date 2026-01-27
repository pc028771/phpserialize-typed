# -*- coding: utf-8 -*-
"""
Tests for phpserialize-typed
Based on original phpserialize tests
"""
import unittest
from io import BytesIO
from collections import OrderedDict

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phpserialize import (
    dumps, loads, dump, load, phpobject,
    dict_to_list, dict_to_tuple, convert_member_dict
)


class TestBasicSerialization(unittest.TestCase):
    """Test basic serialization and unserialization."""

    def test_serialize_none(self):
        self.assertEqual(dumps(None), b'N;')
        self.assertIsNone(loads(b'N;'))

    def test_serialize_bool(self):
        self.assertEqual(dumps(True), b'b:1;')
        self.assertEqual(dumps(False), b'b:0;')
        self.assertTrue(loads(b'b:1;'))
        self.assertFalse(loads(b'b:0;'))

    def test_serialize_int(self):
        self.assertEqual(dumps(42), b'i:42;')
        self.assertEqual(dumps(-17), b'i:-17;')
        self.assertEqual(loads(b'i:42;'), 42)
        self.assertEqual(loads(b'i:-17;'), -17)

    def test_serialize_float(self):
        self.assertEqual(dumps(3.14), b'd:3.14;')
        self.assertEqual(loads(b'd:3.14;'), 3.14)

    def test_serialize_string(self):
        result = dumps("Hello World")
        self.assertEqual(result, b's:11:"Hello World";')
        self.assertEqual(loads(result), b'Hello World')

    def test_serialize_bytes(self):
        data = b'binary\x00data'
        result = dumps(data)
        self.assertEqual(loads(result), data)

    def test_serialize_unicode(self):
        text = "Hello Wörld"
        result = dumps(text)
        # Should be UTF-8 encoded
        self.assertIn(b'W\xc3\xb6rld', result)
        
        # Without decode_strings, returns bytes
        self.assertEqual(loads(result), text.encode('utf-8'))
        
        # With decode_strings, returns str
        self.assertEqual(loads(result, decode_strings=True), text)


class TestCollectionSerialization(unittest.TestCase):
    """Test serialization of lists, tuples, and dicts."""

    def test_serialize_list(self):
        data = [1, 2, 3]
        result = dumps(data)
        # Lists become associative arrays in PHP
        loaded = loads(result)
        self.assertEqual(loaded, {0: 1, 1: 2, 2: 3})
        
        # Can convert back to list
        self.assertEqual(dict_to_list(loaded), data)

    def test_serialize_tuple(self):
        data = (1, 2, 3)
        result = dumps(data)
        loaded = loads(result)
        # Can convert to tuple
        self.assertEqual(dict_to_tuple(loaded), data)

    def test_serialize_dict(self):
        data = {'foo': 'bar', 'baz': 42}
        result = dumps(data)
        loaded = loads(result)
        self.assertEqual(loaded, {b'foo': b'bar', b'baz': 42})
        
        # With decode_strings
        loaded_decoded = loads(result, decode_strings=True)
        self.assertEqual(loaded_decoded, data)

    def test_nested_structures(self):
        data = {
            'users': [
                {'name': 'Alice', 'age': 30},
                {'name': 'Bob', 'age': 25}
            ],
            'count': 2
        }
        result = dumps(data)
        loaded = loads(result, decode_strings=True)
        
        # Check structure (accounting for list->dict conversion)
        self.assertIn('users', loaded)
        self.assertEqual(loaded['count'], 2)


class TestDictConversion(unittest.TestCase):
    """Test dict to list/tuple conversion helpers."""

    def test_dict_to_list_valid(self):
        d = {0: 'a', 1: 'b', 2: 'c'}
        self.assertEqual(dict_to_list(d), ['a', 'b', 'c'])

    def test_dict_to_list_invalid(self):
        # Missing key
        d = {0: 'a', 2: 'c'}
        with self.assertRaises(ValueError):
            dict_to_list(d)
        
        # Non-sequential
        d = {0: 'a', 1: 'b', 3: 'd'}
        with self.assertRaises(ValueError):
            dict_to_list(d)

    def test_dict_to_tuple(self):
        d = {0: 1, 1: 2, 2: 3}
        self.assertEqual(dict_to_tuple(d), (1, 2, 3))


class TestObjectSerialization(unittest.TestCase):
    """Test PHP object serialization."""

    def test_phpobject_basic(self):
        obj = phpobject('MyClass', {'foo': 'bar', 'baz': 42})
        self.assertEqual(obj.__name__, 'MyClass')
        self.assertEqual(obj.foo, 'bar')
        self.assertEqual(obj.baz, 42)

    def test_phpobject_setattr(self):
        obj = phpobject('MyClass', {'foo': 'bar'})
        obj.foo = 'new value'
        self.assertEqual(obj.foo, 'new value')
        
        # Setting new attribute
        obj.new_attr = 'test'
        self.assertEqual(obj.new_attr, 'test')

    def test_phpobject_asdict(self):
        obj = phpobject('MyClass', {' * protected': 'value', 'public': 'data'})
        d = obj._asdict()
        self.assertEqual(d['protected'], 'value')
        self.assertEqual(d['public'], 'data')

    def test_serialize_phpobject(self):
        obj = phpobject('WP_User', {'username': 'admin'})
        result = dumps(obj)
        self.assertIn(b'WP_User', result)
        self.assertIn(b'username', result)
        self.assertIn(b'admin', result)

    def test_unserialize_object(self):
        data = b'O:7:"WP_User":1:{s:8:"username";s:5:"admin";}'
        obj = loads(data, object_hook=phpobject)
        self.assertIsInstance(obj, phpobject)
        self.assertEqual(obj.__name__, b'WP_User')
        # When decode_strings is False, the keys are bytes
        self.assertEqual(obj.__php_vars__[b'username'], b'admin')

    def test_unserialize_object_decoded(self):
        data = b'O:7:"WP_User":1:{s:8:"username";s:5:"admin";}'
        obj = loads(data, object_hook=phpobject, decode_strings=True)
        self.assertEqual(obj.__name__, 'WP_User')
        self.assertEqual(obj.username, 'admin')

    def test_object_hook_custom(self):
        class User:
            def __init__(self, username):
                self.username = username
        
        def custom_hook(name, d):
            if name == b'WP_User' or name == 'WP_User':
                # Convert bytes keys if needed
                username = d.get(b'username') or d.get('username')
                if isinstance(username, bytes):
                    username = username.decode('utf-8')
                return User(username)
            raise ValueError(f"Unknown class: {name}")
        
        data = b'O:7:"WP_User":1:{s:8:"username";s:5:"admin";}'
        user = loads(data, object_hook=custom_hook)
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, 'admin')


class TestMemberDict(unittest.TestCase):
    """Test PHP member dict conversion."""

    def test_convert_member_dict(self):
        php_dict = {
            'public_var': 'value1',
            ' * protected_var': 'value2',
            ' ClassName private_var': 'value3'
        }
        converted = convert_member_dict(php_dict)
        
        self.assertEqual(converted['public_var'], 'value1')
        self.assertEqual(converted['protected_var'], 'value2')
        self.assertEqual(converted['private_var'], 'value3')


class TestArrayHooks(unittest.TestCase):
    """Test array hook functionality."""

    def test_array_hook_ordered_dict(self):
        data = b'a:2:{s:3:"foo";i:1;s:3:"bar";i:2;}'
        result = loads(data, array_hook=OrderedDict, decode_strings=True)
        
        self.assertIsInstance(result, OrderedDict)
        self.assertEqual(list(result.keys()), ['foo', 'bar'])
        self.assertEqual(list(result.values()), [1, 2])

    def test_array_hook_custom(self):
        def custom_hook(items):
            # Custom processing
            return {k: v * 2 if isinstance(v, int) else v for k, v in items}
        
        data = b'a:2:{s:3:"foo";i:1;s:3:"bar";i:2;}'
        result = loads(data, array_hook=custom_hook, decode_strings=True)
        
        self.assertEqual(result['foo'], 2)
        self.assertEqual(result['bar'], 4)


class TestFileIO(unittest.TestCase):
    """Test file-like object operations."""

    def test_dump_and_load(self):
        stream = BytesIO()
        data = {'key': 'value', 'num': 42}
        
        dump(data, stream)
        stream.seek(0)
        result = loads(stream.read(), decode_strings=True)
        
        self.assertEqual(result['key'], 'value')
        self.assertEqual(result['num'], 42)

    def test_load_from_stream(self):
        stream = BytesIO(b'a:2:{i:0;i:1;i:1;i:2;}')
        result = load(stream)
        
        self.assertEqual(result, {0: 1, 1: 2})

    def test_chained_serialization(self):
        stream = BytesIO()
        
        # Write multiple objects
        dump([1, 2], stream)
        dump("foo", stream)
        
        # Read them back
        stream.seek(0)
        first = load(stream)
        second = load(stream)
        
        self.assertEqual(first, {0: 1, 1: 2})
        self.assertEqual(second, b'foo')


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios."""

    def test_empty_string(self):
        result = dumps("")
        self.assertEqual(result, b's:0:"";')
        self.assertEqual(loads(result), b'')

    def test_empty_list(self):
        result = dumps([])
        loaded = loads(result)
        self.assertEqual(loaded, {})

    def test_empty_dict(self):
        result = dumps({})
        loaded = loads(result)
        self.assertEqual(loaded, {})

    def test_none_as_key(self):
        # None becomes empty string as key
        result = dumps({None: 'value'})
        loaded = loads(result, decode_strings=True)
        self.assertEqual(loaded[''], 'value')

    def test_bool_as_key(self):
        # Booleans become integers as keys
        result = dumps({True: 'one', False: 'zero'})
        loaded = loads(result, decode_strings=True)
        self.assertEqual(loaded[1], 'one')
        self.assertEqual(loaded[0], 'zero')

    def test_float_as_key(self):
        # Floats become integers as keys
        result = dumps({3.14: 'pi', 2.71: 'e'})
        loaded = loads(result, decode_strings=True)
        self.assertEqual(loaded[3], 'pi')
        self.assertEqual(loaded[2], 'e')


class TestErrorHandling(unittest.TestCase):
    """Test error handling."""

    def test_invalid_data(self):
        with self.assertRaises(ValueError):
            loads(b'invalid')

    def test_unexpected_end(self):
        with self.assertRaises(ValueError):
            loads(b's:10:"short')

    def test_object_without_hook(self):
        data = b'O:7:"WP_User":1:{s:8:"username";s:5:"admin";}'
        with self.assertRaises(ValueError) as cm:
            loads(data)
        self.assertIn('object_hook not given', str(cm.exception))

    def test_unserializable_type(self):
        class CustomClass:
            pass
        
        with self.assertRaises(TypeError):
            dumps(CustomClass())


if __name__ == '__main__':
    unittest.main()
