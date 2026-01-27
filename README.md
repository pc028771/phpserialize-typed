# phpserialize-typed

A PHP serializer/unserializer for Python with comprehensive type annotations.

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](LICENSE)
[![Python Versions](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Type Checked](https://img.shields.io/badge/type--checked-mypy-blue.svg)](https://mypy.readthedocs.io/)

## Overview

This project is based on [phpserialize](https://github.com/mitsuhiko/phpserialize) by Armin Ronacher, licensed under BSD 3-Clause. The primary enhancement in `phpserialize-typed` is the addition of comprehensive type annotations to support static type checking with tools like mypy.

### Key Features

- **Full Type Annotations**: Complete type hints for all functions, classes, and methods
- **Static Type Checking**: Compatible with mypy, pyright, and other type checkers
- **PEP 561 Compliant**: Includes `py.typed` marker for distribution of type information
- **Backward Compatible**: Maintains full API compatibility with the original phpserialize
- **PHP Serialize/Unserialize**: Port of PHP's serialize() and unserialize() functions to Python
- **Object Support**: Serialization and unserialization of PHP objects
- **Array Hooks**: Custom array converters (e.g., OrderedDict)
- **Python 3.7+**: Modern Python support with proper typing

## Installation

```bash
pip install phpserialize-typed
```

Or install from source:

```bash
git clone https://github.com/pc028771/phpserialize-typed.git
cd phpserialize-typed
pip install -e .
```

## Quick Start

```python
from phpserialize import dumps, loads

# Serialize Python objects to PHP format
serialized = dumps({"name": "Alice", "age": 30})
print(serialized)  # b'a:2:{s:4:"name";s:5:"Alice";s:3:"age";i:30;}'

# Unserialize PHP data back to Python
data = loads(b'a:2:{s:3:"foo";s:3:"bar";s:3:"baz";i:42;}')
print(data)  # {'foo': 'bar', 'baz': 42}
```

## Usage Examples

### Basic Serialization

```python
from phpserialize import dumps, loads

# Simple values
dumps("Hello World")  # b's:11:"Hello World";'
loads(b's:11:"Hello World";')  # b'Hello World'

# Numbers
dumps(42)  # b'i:42;'
dumps(3.14)  # b'd:3.14;'

# Lists (converted to PHP arrays with numeric keys)
dumps([1, 2, 3])  # b'a:3:{i:0;i:1;i:1;i:2;i:2;i:3;}'
```

### Working with Dictionaries

```python
from phpserialize import loads, dict_to_list

# PHP doesn't distinguish between lists and arrays
# So lists are returned as dicts with integer keys
result = loads(dumps([1, 2, 3]))
print(result)  # {0: 1, 1: 2, 2: 3}

# Convert back to list
dict_to_list(result)  # [1, 2, 3]
```

### Unicode Strings

```python
from phpserialize import dumps, loads

# Encoding
dumps("Hello Wörld")  # Encodes to UTF-8 by default

# Decoding
loads(dumps("Hello Wörld"), decode_strings=True)  # Decodes back to str
```

### Object Serialization

```python
from phpserialize import dumps, loads, phpobject

# Unserializing PHP objects
data = b'O:7:"WP_User":1:{s:8:"username";s:5:"admin";}'
user = loads(data, object_hook=phpobject)
print(user.username)  # 'admin'
print(user.__name__)  # 'WP_User'

# Custom object hook
class User:
    def __init__(self, username: str):
        self.username = username

def my_object_hook(name: str, d: dict):
    if name == b'WP_User' or name == 'WP_User':
        return User(**d)
    raise ValueError(f"Unknown class: {name}")

user = loads(data, object_hook=my_object_hook)
```

### Using Array Hooks

```python
from collections import OrderedDict
from phpserialize import loads

# Preserve order with OrderedDict
data = b'a:2:{s:3:"foo";i:1;s:3:"bar";i:2;}'
result = loads(data, array_hook=OrderedDict)
print(result)  # OrderedDict([('foo', 1), ('bar', 2)])
```

### File-like Objects

```python
from io import BytesIO
from phpserialize import dump, load

# Writing to stream
stream = BytesIO()
dump([1, 2, 3], stream)
print(stream.getvalue())  # b'a:3:{i:0;i:1;i:1;i:2;i:2;i:3;}'

# Reading from stream
stream = BytesIO(b'a:2:{i:0;i:1;i:1;i:2;}')
data = load(stream)
print(data)  # {0: 1, 1: 2}
```

## Type Checking

This library is fully typed and can be used with static type checkers:

```python
from typing import Dict, Any
from phpserialize import loads, dumps

# Type checker understands return types
data: bytes = dumps({"key": "value"})
result: Any = loads(data)  # Returns Any since PHP types are dynamic

# For more specific typing, use type narrowing or casts
from typing import cast
typed_result: Dict[str, str] = cast(Dict[str, str], loads(data))
```

### Running mypy

```bash
mypy your_script.py
```

The library itself passes strict mypy checks:

```bash
mypy phpserialize.py --strict
```

## API Reference

### Functions

- `dumps(data, charset='utf-8', errors='surrogateescape', object_hook=None) -> bytes`
  - Serialize Python object to PHP format
  
- `loads(data, charset='utf-8', errors='surrogateescape', decode_strings=False, object_hook=None, array_hook=None) -> Any`
  - Unserialize PHP data to Python object
  
- `dump(data, fp, charset='utf-8', errors='surrogateescape', object_hook=None) -> None`
  - Serialize to file-like object
  
- `load(fp, charset='utf-8', errors='surrogateescape', decode_strings=False, object_hook=None, array_hook=None) -> Any`
  - Unserialize from file-like object
  
- `dict_to_list(d) -> list`
  - Convert dict with sequential integer keys to list
  
- `dict_to_tuple(d) -> tuple`
  - Convert dict with sequential integer keys to tuple
  
- `convert_member_dict(d) -> dict`
  - Convert PHP member names to Python identifiers

### Classes

- `phpobject(name, d=None)`
  - Represents a PHP object
  - `__name__`: PHP class name
  - `__php_vars__`: Dictionary of object properties
  - `_asdict()`: Convert to regular dict

## Development

### Setting up development environment

```bash
# Clone the repository
git clone https://github.com/pc028771/phpserialize-typed.git
cd phpserialize-typed

# Install development dependencies
pip install -e ".[dev]"
```

### Running tests

```bash
pytest tests/
```

### Type checking

```bash
mypy phpserialize.py --strict
```

## Credits

This project is based on [phpserialize](https://github.com/mitsuhiko/phpserialize) by Armin Ronacher.

**Original Author**: Armin Ronacher  
**Original License**: BSD 3-Clause  
**Original Project**: https://github.com/mitsuhiko/phpserialize

The modifications in `phpserialize-typed` add comprehensive type annotations while maintaining full backward compatibility with the original library.

## License

BSD 3-Clause License. See [LICENSE](LICENSE) file for details.

This project maintains the original BSD 3-Clause license from phpserialize and adds appropriate copyright notices for the modifications.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Changelog

### 1.4.0 (phpserialize-typed)
- Added comprehensive type annotations for all functions and classes
- Added Protocol types for file-like objects
- Improved type safety with Generic types
- Added py.typed marker for PEP 561 compliance
- Maintained full backward compatibility with phpserialize 1.3

### Previous versions
See the [original phpserialize changelog](https://github.com/mitsuhiko/phpserialize) for version history before 1.4.0.