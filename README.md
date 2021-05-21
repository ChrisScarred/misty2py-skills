# Misty2py-skills

Misty2py-skills is a Python 3 library of Misty II skills developed using Misty2py library.

## Documentations

The package `misty2py_skills` contains:

- `misty2py_skills.battery_printer` module - a skill that prints Misty's battery status every 250 ms in the terminal for the duration specified as the second CLI argument in seconds (optional, defaults to 2 seconds).
- `misty2py_skills.listening_expression` module - a simple expression that makes Misty appear to be listening.
- `misty2py_skills.angry_expression` module - a simple expression that makes Misty appear to be angry.
- `misty2py_skills.hey_misty` module - a skill of Misty reacting to the *"Hey Misty"* keyphrase.
- `misty2py_skills.free_memory` module - a skill that removes non-system audio, video, image and recording files from Misty's memory.
- `misty2py_skills.remote_control` module - a skill that lets you control your Misty via a keyboard (please note that Misty is not a remote control race car so the controllability and responsiveness is not on the level of the typical remotelly controlled devices).
- `misty2py_skills.explore` module - a skill that enables SLAM mapping.
- `misty2py_skills.face_recognition` module - a skill that greets people upon face detection with their name if known and prompts a face training session if their face (and therefore their name) is not known.
- `misty2py_skills.utils` sub-packege which contains:

  - `misty2py_skills.utils.template` file - a template file for developing a skill with Misty2py.
  - `misty2py_skills.utils.status` module - contains the class `Status` which can be used to track the execution state of a script.

    - `misty2py_skills.utils.status::Status.__init__` (aka `misty2py.utils.status.Status()`) - initialisation that takes optional parameters `init_status` (str), `init_data` (str) and `init_time` (float).
    - `misty2py_skills.utils.status::Status.update_data_time` - sets `data` to the value of `det_data` (str) and `time` to the value of `det_time` (float).
    - `misty2py_skills.utils.status::Status.set_status` - sets `status` to the value of `det_status` (str). 
    - `misty2py_skills.utils.status::Status.set_time` - sets `time` to the value of `det_time` (float)
    - `misty2py_skills.utils.status::Status.get_data_time` - returns the `data` and `time` in a tuple.
    - `misty2py_skills.utils.status::Status.get_status` - returns the `status`.

## Planned future features

- test all skills
- a new question answering skill
- update the documentation
- refine the explore skill
- add troubleshooting instructions
