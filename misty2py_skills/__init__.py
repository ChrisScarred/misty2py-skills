"""Misty2py-skills is a Python 3 library of Misty II skills developed using Misty2py library.

## Running the skills

Copy the `.env.example` from the root directory of this repository into `.env` and replace the values of `MISTY_IP_ADDRESS` and `PROJECT_DIR` with appropriate values.

If you are running the skills from the source, run commands `pip install poetry` and `poetry install` to get the dependencies.

If you are running speech recognition-related skills, follow the directions below.

## Running speech recognition-related skills

Set up an account at [Wit.ai](https://wit.ai/).

Create a new app at [Wit.ai](https://wit.ai/). If you wish to run the skill `misty2py_skills.question_answering`, select the option "Import From a Backup" and use the file in `accompanying_data` in the root directory of this package's [repository](https://github.com/ChrisScarred/misty2py-skills) as a backup file.

Go to the dashboard of the new app, select Settings under Management and get the Server Access Token.

Replace the value of `WIT_AI_KEY` in your `.env` file with the Server Access Token.
"""
