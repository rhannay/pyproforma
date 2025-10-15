# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `LineItemResults.move()` method for repositioning single line items using `Model.reorder_line_items()` arguments
- `LineItemsResults.move()` method for repositioning multiple line items as a group while preserving their relative order

### Changed
- `LineItemsTotalRow` label now always appears in the first cell regardless of `included_cols` configuration

### Fixed
- `Tables.line_items()` now properly handles multiple `included_cols` with `include_totals=True` and `group_by_category=True`
- Fixed column count inconsistencies in `LineItemsTotalRow` and `LabelRow` when using multiple included columns

## [0.1.15] - 2025-10-14

### Changed
- Renamed `MultiLineItem` class to `Generator` (breaking change - no backward compatibility)
- Removed tuple access pattern `model['name', year]` for getting values
  - Use `model.value('name', year)` instead for getting specific values
- Updated approach to `Tables.line_items()` method with improved table generation and new result class methods

## [0.1.14] - 2025-10-02

### Changed
- Removed pattern where line items are created for category totals

## [0.1.13] - Previous Release

### Added
- Support for `category_total:category_name` formula pattern for dynamic category totals

---

*Note: This changelog was added in version 0.1.14. Previous versions may not have detailed change logs.*
