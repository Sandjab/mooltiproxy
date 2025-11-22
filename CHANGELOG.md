# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive code review documentation (CODE_REVIEW.md)
- Architecture documentation (ARCHITECTURE.md)
- Improvement proposals documentation (IMPROVEMENTS.md)
- This CHANGELOG file to track project changes

### Changed
- Documentation improvements throughout README.md

### Security
- Identified YAML loading vulnerability (utils.py) - to be fixed
- Identified weak random ID generation (mappers.py) - to be fixed

## [1.0.0] - 2023

### Added
- Initial release of Mooltiproxy
- HTTP proxy with URL mapping
- OpenAI to TGI request/response translation
- Bearer token authentication
- IP-based security (whitelist, blacklist, auto-ban)
- Flexible routing system
- Prompt template system
- Support for Llama2-Chat specific prompts
- Configuration validation using voluptuous
- SSL/TLS support
- CORS handling

### Features
- `main.py`: Core HTTP server and request handler
- `cerbere.py`: Security and access control
- `mappers.py`: Payload translation functions
- `prompters.py`: Prompt formatting functions
- `utils.py`: Configuration loading and utilities
- `config_template.yaml`: Configuration template
- `test_chat.py`: Example chatbot implementation

## Release Notes

### Version 1.0.0

This is the initial release of Mooltiproxy, a lightweight HTTP proxy designed for API translation. The primary use case is exposing OpenAI-compatible endpoints while proxying to alternative backends like Hugging Face TGI.

**Key Features:**
- Minimal dependencies (pyyaml, requests, voluptuous)
- Configuration-driven behavior
- Extensible mapper and prompter system
- Basic security features
- Experimental/development focus

**Known Limitations:**
- No streaming support
- In-memory state only (no persistence)
- Not designed for production traffic
- No metrics or monitoring
- Basic error handling

**Security Considerations:**
- Requires MOOLTIPROXY_KEY environment variable
- Supports IP whitelisting and blacklisting
- Automatic IP banning after failed auth attempts
- Optional SSL/TLS support

---

[Unreleased]: https://github.com/Sandjab/mooltiproxy/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Sandjab/mooltiproxy/releases/tag/v1.0.0
