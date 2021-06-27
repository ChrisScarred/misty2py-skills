# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 2.0.0 - 27-06-2021

### Changed

- Updated all content to be compatible with misty2py 5.0.0.
- Updated the documentation.


## 1.0.0 - 15-06-2021

### Added

- `videoclip_sources` for scripts used for videoclips
- `skills_without_misty2py` for the same skills implemented without using Misty2py library

### Changed

- moved the template file into `accompanying_data`
- import statements to fit the changes in architecture

### Removed

- all utility functions as those were implemented in Misty2py
- unnecessary sub-packages

## 0.0.2 - 24-05-2021

### Added

- path-related helper functions and `cancel_skills` function in `misty2py_skills.utils.utils`
- `misty2py_skills.essentials.movement`
- `misty2py_skills.essentials.speech_transcripter` which uses Wit.ai and SpeechRecognition to transcribe audio
- the `misty2py_skills.question_answering` skill
- the Wit.ai app back-up data for reproducibility purposes

### Fixed

- Issues arising when skills of this library were run in parallel with skills uploaded to Misty

### Changed

- Wrong date in the previous changelog entry
- README
- the style of some skills
- refined `misty2py_skills.face_recognition` to contain enumerations where appropriate
- refined `misty2py_skills.remote_control` to be separate from `misty2py_skills.essentials.movement`

## 0.0.1 - 22-05-2021

### Added

- This CHANGELOG to track changes.
- README with basic information.
- The package misty2py-skills itself, including:
  - skills `battery_printer`, `listening_expression`, `angry_expression`, `hey_misty`, `free_memory`, `remote_control`, `explore` and `face_recognition`
  - `misty2py-skills.utils` sub-package with the `status` module and `template` file for skill development
