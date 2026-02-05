# Changelog

All notable changes to phpserialize-typed will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-02-05

### Fixed

- Fixed `py.typed` not being included in wheel distributions
- Converted from single-file module to src layout package structure for proper PEP 561 compliance

## [1.0.0] - 2026-01-31

First release of phpserialize-typed as an independent fork of [phpserialize](https://github.com/mitsuhiko/phpserialize).

### Added

- Comprehensive type annotations for all functions, classes, and methods
- Protocol types (`SupportsRead`, `SupportsWrite`) for file-like objects
- PEP 561 compliance with `py.typed` marker for type distribution
- Full pytest test suite with 37 tests (migrated from unittest)
- Development dependencies: pytest, pytest-cov, mypy
- Class-based serializer/unserializer architecture (`_PHPSerializer`, `_PHPUnserializer`)
- Type aliases: `PHPValue`, `PHPKey`, `PHPDict`, `PHPArray`
- Strict mypy configuration with comprehensive type checking

### Changed

- Migrated test framework from unittest to pytest
- Refactored serialization/unserialization into class-based design
- Improved type safety with Generic types and stricter type hints
- Enhanced error handling with better type narrowing
- Updated protocol definitions to use position-only parameters

### Maintained

- Full backward compatibility with phpserialize 1.3 API
- All original functionality and behavior
- BSD 3-Clause license with proper attribution
- Support for Python 3.7+

### Credits

Based on [phpserialize](https://github.com/mitsuhiko/phpserialize) by Armin Ronacher, licensed under BSD 3-Clause.

---

## Previous Versions (phpserialize)

For the changelog of the original phpserialize library (versions prior to this fork), see:
https://github.com/mitsuhiko/phpserialize

[1.0.1]: https://github.com/pc028771/phpserialize-typed/releases/tag/v1.0.1
[1.0.0]: https://github.com/pc028771/phpserialize-typed/releases/tag/v1.0.0
