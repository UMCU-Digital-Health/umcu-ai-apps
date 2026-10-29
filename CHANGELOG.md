# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.6] - 2026-10-29

### Fixed
- Javascript callbacks was not loaded correctly, because dash still looked in the old dash folder.

## [1.1.5] - 2026-10-21

### Changed
- Renamed folder dash/ to dashboard/ to prevent package errors regarding the dash package


## [1.1.4] - 2026-10-14

### Added
- Added a workflow for publishing the docs to GitHub Pages

## [1.1.3] - 2026-10-13

### Added
- Added documentation as mkdocs to help users with the dashboard
- Added developer documentation for the CLI tools (docs/developer-guide/cli.md)

### Changed
- Updated README with quick start, CLI overview, development and deployment instructions

### Removed
- Removed datasetcard and modelcard since this is not applicable to this repo
## [1.1.2] - 2026-10-09

### Changed
- Changed the size of the model name from 10 to 50
- Increased the max size of the csv ready to be loaded into the database via cli. 
- Fixed the new line showing in the llm_evaluation app
- Made the height of the textboxes adjustable by the user.
- Created a production environment

## [1.1.1] - 2026-10-07

### Changed
- Updated files needed for deployment (write_manifest, deploy, manifest files etc.)
- requirements.txt is no longer kept in version control, but created and removed during deployment based on uv.lock
- Updated logging for posit connect

### Added
- Added dependency for MS SQL server now that we have a working service account
- Updated other dependencies

## [1.1.0] - 2026-09-16

### Added
- Added authorization for users based on project and department combination(s)
- Added a new command (add_eval_user) to add new users to the DB

### Changed
- Only read (and create) the user when the dashboard initially loads, subsequent functions read it from the state

## [1.0.0] - 2026-08-28

### Added
- Added the MVP of the llm evaluation app


## [0.1.0] - 2026-08-26

### Added
- Created project and repository
