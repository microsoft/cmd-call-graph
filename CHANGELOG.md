# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added

- Added a Chengelog, that retroactively covers all versions.

### Fixed

- Issue #15 (Fix handling of nodes with %)
- Issue #17 (Create a ChangeLog)

## [0.4] - 2018-12-12

### Added

- Add an option to hide some nodes (--nodes-to-hide)

### Fixed

- Allow connections to non-existing nodes
- Fix comment detection logic
- Issue #11 (Fix connection type for nodes ending in goto)

## [0.3] - 2018-12-08

### Added

- Show number of external calls with --show-node-stats (fixes Issue #9)

### Fixed

- Issue #8 (Fix treating the last block as exit node if it's not)


## [0.2] - 2018-12-06

### Added

- Improved unit test coverage to ~90% (fixes Issue #4)
- Add an option to show per-node statistics (--show-node-stats)
- Automatic pruning of the EOF node if it's not used

### Fixed

- Execution under Python 2.x
- Issue #10 (Make the ordering of the resulting graph deterministic)
- Logic for the generation of nested connections

## [0.1.2] - 2018-11-18

### Added

- Most of the core functionality :)
- First release pushed to PyPI

### Fixed

- Fixed overflow error in tokenization of the exit command (by @refack)
