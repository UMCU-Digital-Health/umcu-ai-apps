# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
