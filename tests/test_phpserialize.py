# -*- coding: utf-8 -*-
"""
Tests for phpserialize-typed
Based on original phpserialize tests
"""
import math
import pytest
from io import BytesIO
from collections import OrderedDict
from typing import Dict, List, Tuple, Union, Any, cast

from phpserialize import (
    dumps, loads, dump, load, phpobject,
    dict_to_list, dict_to_tuple, convert_member_dict
)


class TestBasicSerialization:
    """Test basic serialization and unserialization."""

    def test_serialize_none(self):
        assert dumps(None) == b'N;'
        assert loads(b'N;') is None

    def test_serialize_bool(self):
        assert dumps(True) == b'b:1;'
        assert dumps(False) == b'b:0;'
        assert loads(b'b:1;') is True
        assert loads(b'b:0;') is False

    def test_serialize_int(self):
        assert dumps(42) == b'i:42;'
        assert dumps(-17) == b'i:-17;'
        assert loads(b'i:42;') == 42
        assert loads(b'i:-17;') == -17

    def test_serialize_float(self):
        assert dumps(3.14) == b'd:3.14;'
        assert math.isclose(loads(b'd:3.14;'), 3.14)

    def test_serialize_string(self):
        result = dumps("Hello World")
        assert result == b's:11:"Hello World";'
        assert loads(result) == b'Hello World'

    def test_serialize_bytes(self):
        data = b'binary\x00data'
        result = dumps(data)
        assert loads(result) == data

    def test_serialize_unicode(self):
        text = "Hello Wörld"
        result = dumps(text)
        # Should be UTF-8 encoded
        assert b'W\xc3\xb6rld' in result
        
        # Without decode_strings, returns bytes
        assert loads(result) == text.encode('utf-8')
        
        # With decode_strings, returns str
        assert loads(result, decode_strings=True) == text


class TestCollectionSerialization:
    """Test serialization of lists, tuples, and dicts."""

    def test_serialize_list(self):
        data = [1, 2, 3]
        result = dumps(data)
        # Lists become associative arrays in PHP
        loaded = loads(result)
        assert loaded == {0: 1, 1: 2, 2: 3}
        
        # Can convert back to list
        assert dict_to_list(loaded) == data

    def test_serialize_tuple(self):
        data = (1, 2, 3)
        result = dumps(data)
        loaded = loads(result)
        # Can convert to tuple
        assert dict_to_tuple(loaded) == data

    def test_serialize_dict(self):
        data: Dict[str, Union[str, int]] = {'foo': 'bar', 'baz': 42}
        result = dumps(data)
        loaded = loads(result)
        assert loaded == {b'foo': b'bar', b'baz': 42}
        
        # With decode_strings
        loaded_decoded = loads(result, decode_strings=True)
        assert loaded_decoded == data

    def test_nested_structures(self):
        data: Dict[str, Any] = {
            'users': [
                {'name': 'Alice', 'age': 30},
                {'name': 'Bob', 'age': 25}
            ],
            'count': 2
        }
        result = dumps(data)
        loaded = loads(result, decode_strings=True)
        
        # Check structure (accounting for list->dict conversion)
        assert 'users' in loaded
        assert loaded['count'] == 2


class TestDictConversion:
    """Test dict to list/tuple conversion helpers."""

    def test_dict_to_list_valid(self):
        d = {0: 'a', 1: 'b', 2: 'c'}
        assert dict_to_list(d) == ['a', 'b', 'c']

    def test_dict_to_list_invalid(self):
        # Missing key
        d = {0: 'a', 2: 'c'}
        with pytest.raises(ValueError):
            dict_to_list(d)
        
        # Non-sequential
        d = {0: 'a', 1: 'b', 3: 'd'}
        with pytest.raises(ValueError):
            dict_to_list(d)

    def test_dict_to_tuple(self):
        d = {0: 1, 1: 2, 2: 3}
        assert dict_to_tuple(d) == (1, 2, 3)


class TestObjectSerialization:
    """Test PHP object serialization."""

    def test_phpobject_basic(self):
        obj = phpobject('MyClass', {'foo': 'bar', 'baz': 42})
        assert obj.__name__ == 'MyClass'
        assert obj.foo == 'bar'
        assert obj.baz == 42

    def test_phpobject_setattr(self):
        obj = phpobject('MyClass', {'foo': 'bar'})
        obj.foo = 'new value'
        assert obj.foo == 'new value'
        
        # Setting new attribute
        obj.new_attr = 'test'
        assert obj.new_attr == 'test'

    def test_phpobject_asdict(self):
        obj = phpobject('MyClass', {' * protected': 'value', 'public': 'data'})
        d = convert_member_dict(obj.__php_vars__)
        assert d['protected'] == 'value'
        assert d['public'] == 'data'

    def test_serialize_phpobject(self):
        obj = phpobject('WP_User', {'username': 'admin'})
        result = dumps(obj)
        assert b'WP_User' in result
        assert b'username' in result
        assert b'admin' in result

    def test_unserialize_object(self):
        data = b'O:7:"WP_User":1:{s:8:"username";s:5:"admin";}'
        obj = loads(data, object_hook=phpobject)
        assert isinstance(obj, phpobject)
        assert obj.__name__ == b'WP_User'
        # When decode_strings is False, the keys are bytes
        assert obj.__php_vars__[b'username'] == b'admin'

    def test_unserialize_object_decoded(self):
        data = b'O:7:"WP_User":1:{s:8:"username";s:5:"admin";}'
        obj = loads(data, object_hook=phpobject, decode_strings=True)
        assert obj.__name__ == 'WP_User'
        assert obj.username == 'admin'

    def test_object_hook_custom(self):
        class User:
            def __init__(self, username: str) -> None:
                self.username = username
        
        def custom_hook(name: Union[str, bytes], d: Dict[Union[str, int, bytes], Any]) -> User:
            if name == b'WP_User' or name == 'WP_User':
                # Convert bytes keys if needed
                username = d.get(b'username') or d.get('username')
                if isinstance(username, bytes):
                    username = username.decode('utf-8')
                if not isinstance(username, str):
                    raise ValueError("Invalid username")
                return User(username)
            raise ValueError(f"Unknown class: {name}")
        
        data = b'O:7:"WP_User":1:{s:8:"username";s:5:"admin";}'
        user = loads(data, object_hook=custom_hook)
        assert isinstance(user, User)
        assert user.username == 'admin'


class TestMemberDict:
    """Test PHP member dict conversion."""

    def test_convert_member_dict(self):
        php_dict: Dict[Union[str, int, bytes], Any] = {
            'public_var': 'value1',
            ' * protected_var': 'value2',
            ' ClassName private_var': 'value3'
        }
        converted = convert_member_dict(php_dict)
        
        assert converted['public_var'] == 'value1'
        assert converted['protected_var'] == 'value2'
        assert converted['private_var'] == 'value3'


class TestArrayHooks:
    """Test array hook functionality."""

    def test_array_hook_ordered_dict(self):
        data = b'a:2:{s:3:"foo";i:1;s:3:"bar";i:2;}'
        result = cast(OrderedDict[str, int], loads(data, array_hook=OrderedDict, decode_strings=True))
        
        assert isinstance(result, OrderedDict)
        assert list(result.keys()) == ['foo', 'bar']
        assert list(result.values()) == [1, 2]

    def test_array_hook_custom(self):
        def custom_hook(items: List[Tuple[Union[str, int, bytes], Any]]) -> Dict[Union[str, int, bytes], Any]:
            # Custom processing
            return {k: v * 2 if isinstance(v, int) else v for k, v in items}
        
        data = b'a:2:{s:3:"foo";i:1;s:3:"bar";i:2;}'
        result = loads(data, array_hook=custom_hook, decode_strings=True)
        
        assert result['foo'] == 2
        assert result['bar'] == 4


class TestFileIO:
    """Test file-like object operations."""

    def test_dump_and_load(self):
        stream = BytesIO()
        data: Dict[str, Union[str, int]] = {'key': 'value', 'num': 42}
        
        dump(data, stream)
        stream.seek(0)
        result = loads(stream.read(), decode_strings=True)
        
        assert result['key'] == 'value'
        assert result['num'] == 42

    def test_load_from_stream(self):
        stream = BytesIO(b'a:2:{i:0;i:1;i:1;i:2;}')
        result = load(stream)
        
        assert result == {0: 1, 1: 2}

    def test_chained_serialization(self):
        stream = BytesIO()
        
        # Write multiple objects
        dump([1, 2], stream)
        dump("foo", stream)
        
        # Read them back
        stream.seek(0)
        first = load(stream)
        second = load(stream)
        
        assert first == {0: 1, 1: 2}
        assert second == b'foo'


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_string(self):
        result = dumps("")
        assert result == b's:0:"";'
        assert loads(result) == b''

    def test_empty_list(self):
        result = dumps([])
        loaded = loads(result)
        assert loaded == {}

    def test_empty_dict(self):
        result = dumps({})
        loaded = loads(result)
        assert loaded == {}

    def test_none_as_key(self):
        # None becomes empty string as key
        result = dumps({None: 'value'})
        loaded = loads(result, decode_strings=True)
        assert loaded[''] == 'value'

    def test_bool_as_key(self):
        # Booleans become integers as keys
        result = dumps({True: 'one', False: 'zero'})
        loaded = loads(result, decode_strings=True)
        assert loaded[1] == 'one'
        assert loaded[0] == 'zero'

    def test_float_as_key(self):
        # Floats become integers as keys
        result = dumps({3.14: 'pi', 2.71: 'e'})
        loaded = loads(result, decode_strings=True)
        assert loaded[3] == 'pi'
        assert loaded[2] == 'e'


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_data(self):
        with pytest.raises(ValueError):
            loads(b'invalid')

    def test_unexpected_end(self):
        with pytest.raises(ValueError):
            loads(b's:10:"short')

    def test_object_without_hook(self):
        data = b'O:7:"WP_User":1:{s:8:"username";s:5:"admin";}'
        with pytest.raises(ValueError, match='object_hook not given'):
            loads(data)

    def test_unserializable_type(self):
        class CustomClass:
            pass
        
        with pytest.raises(TypeError):
            dumps(cast(Any, CustomClass()))
