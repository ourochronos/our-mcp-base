# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- `MCPServerBase` abstract base class with injectable startup_hook and health_check
- `ToolRouter` decorator-based tool dispatch
- Response helpers: `success_response`, `error_response`, `not_found_response`
- Custom error handler support via `error_handlers` parameter
