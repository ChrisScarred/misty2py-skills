"""This module implements a skill that allows a person to have a simple dialogue with Misty.
"""
import datetime
import os
from enum import Enum
from typing import Dict, List, Tuple

import speech_recognition as sr
from dotenv import dotenv_values
from misty2py.basic_skills.cancel_skills import cancel_skills
from misty2py.response import success_of_action_list
from misty2py.utils.base64 import *
from misty2py.utils.generators import get_random_string
from misty2py.utils.status import ActionLog, Status
from misty2py.utils.utils import (
    get_abs_path,
    get_base_fname_without_ext,
    get_files_in_dir,
    get_misty,
)
from num2words import num2words
from pymitter import EventEmitter


class SpeechTranscripter:
    """Represents the speech transcribing component of Wit.ai."""

    def __init__(self, wit_ai_key: str) -> None:
        """Initialises the speech transcripyer.

        Args:
            wit_ai_key (str): The API key for Wit.ai.
        """
        self.key = wit_ai_key
        self.recogniser = sr.Recognizer()

    def load_wav(self, audio_path: str) -> sr.AudioFile:
        """Loads an audio (.wav) file.

        Args:
            audio_path (str): The absolute path to the audio file in .wav format to transcribe.

        Returns:
            sr.AudioFile: The speech_recognition package representation of an audio file.
        """
        with sr.AudioFile(audio_path) as source:
            return self.recogniser.record(source)

    def audio_to_text(self, audio: sr.AudioSource, show_all: bool = False) -> Dict:
        """Transcribes an audio of a valid speech_recognition package defined format to plaintext.

        Args:
            audio (sr.AudioSource): The audio to transcribe.
            show_all (bool, optional): Whether to return all possible transcriptions (`True`) or the one in which Wit.ai is most confident (`False`). Defaults to `False`.

        Returns:
            Dict: [description]
        """
        try:
            transcription = self.recogniser.recognize_wit(
                audio, key=self.key, show_all=show_all
            )
            return {"success": True, "content": transcription}

        except sr.UnknownValueError:
            return {"success": True, "content": "unknown"}

        except sr.RequestError as e:
            return {
                "success": False,
                "content": "Invalid request.",
                "error_details": str(e),
            }


ee = EventEmitter()
misty = get_misty()
status = Status()
action_log = ActionLog()
event_name = "user_speech_" + get_random_string(6)
values = dotenv_values(".env")
speech_transcripter = SpeechTranscripter(values.get("WIT_AI_KEY", ""))

SAVE_DIR = get_abs_path("data")
"""The location where a speech file is saved."""
SPEECH_FILE = "capture_Dialogue.wav"
"""The name od a speech file on Misty's server."""


class StatusLabels(Enum):
    """Respresentes states in which the dialogue skill can be."""

    REINIT = "reinit"
    """The re-initialisation state when waiting for the person to talk."""
    LISTEN = "listening"
    """The state of listening to a person."""
    PREP = "prepare_reply"
    """The state of preparing a reply, including choosing the fitting reply."""
    INFER = "infering"
    """The state of infering the meaning of a person's speech."""
    STOP = "stop"
    """The terminating state."""
    SPEAK = "ready_to_speak"
    """The speaking state."""


@ee.on(event_name)
def listener(data: Dict):
    """Reacts to a capture speech event by commencing inferrence if speech was captured or by re-initialising the process in case of an initialisation error."""
    if data.get("errorCode", -1) == 0:
        status.set_(status=StatusLabels.INFER)

    if data.get("errorCode", -1) == 3:
        status.set_(status=StatusLabels.REINIT)


def get_next_file_name(dir_: str) -> str:
    """Generates the next file name in a directory whose files are named incrementally with strings representing integers, zero-padded to four characters."""
    files = get_files_in_dir(dir_)
    highest = 0
    if len(files) > 0:
        highest = max([int(get_base_fname_without_ext(f).lstrip("0")) for f in files])
    return os.path.join(dir_, "%s.wav" % str(highest + 1).zfill(4))


def get_all_audio_file_names() -> List[str]:
    """Obtains the list of audio files on Misty's server."""
    dict_list = (
        misty.get_info("audio_list")
        .parse_to_dict()
        .get("rest_response", {})
        .get("result", [])
    )
    audio_list = []
    for d in dict_list:
        audio_list.append(d.get("name"))
    return audio_list


def speech_capture() -> None:
    """Captures speech."""
    print("Listening")

    audio_status = misty.get_info("audio_status").parse_to_dict()
    action_log.append_({"audio_status": audio_status})

    if not audio_status.get("result"):
        enable_audio = misty.perform_action("audio_enable").parse_to_dict()
        if not enable_audio.get("rest_response", {}).get("result"):
            action_log.append_({"enable_audio": enable_audio})
            status.set_(status=StatusLabels.STOP)
            return

    set_volume = misty.perform_action(
        "volume_settings", data="low_volume"
    ).parse_to_dict()
    action_log.append_({"set_volume": set_volume})

    capture_speech = misty.perform_action(
        "speech_capture", data={"RequireKeyPhrase": False}
    ).parse_to_dict()
    action_log.append_({"capture_speech": capture_speech})
    status.set_(status=StatusLabels.LISTEN)


def perform_inference() -> None:
    """Transcribes the newest obtained captured speech."""
    print("Analysing")
    label = StatusLabels.REINIT
    data = ""

    if SPEECH_FILE in get_all_audio_file_names():
        speech_json = misty.get_info(
            "audio_file", params={"FileName": SPEECH_FILE, "Base64": "true"}
        )
        speech_base64 = speech_json.get("result", {}).get("base64", "")
        if len(speech_base64) > 0:
            f_name = get_next_file_name(SAVE_DIR)
            base64_to_content(speech_base64, save_path=f_name)
            speech_wav = speech_transcripter.load_wav(f_name)
            speech_text = speech_transcripter.audio_to_text(speech_wav, show_all=True)
            label = StatusLabels.PREP
            data = speech_text

    status.set_(status=label, data=data)


def get_intents_keywords(entities: Dict) -> Tuple[List[str], List[str]]:
    """Obtains the list of intents and the list of keywords from an Wit.ai entity."""
    intents = []
    keywords = []
    for key, val in entities.items():
        if key == "intent":
            intents.extend([dct.get("value") for dct in val])
        else:
            keywords.append(key)
    return intents, keywords


def choose_reply() -> None:
    """Chooses the reply to the newest recorded speech by inferring the keywords and intents of the speech and matching the fitting reply to them."""
    print("Preparing the reply")

    data = status.get_("data")
    if isinstance(data, Dict):
        data = data.get("content", {})

    intents, keywords = get_intents_keywords(data.get("entities", {}))
    utterance_type = "unknown"

    if "greet" in intents:
        if "hello" in keywords:
            utterance_type = "hello"
        elif "goodbye" in keywords:
            utterance_type = "goodbye"
        else:
            utterance_type = "hello"

    elif "datetime" in intents:
        if "date" in keywords:
            utterance_type = "date"
        elif "month" in keywords:
            utterance_type = "month"
        elif "year" in keywords:
            utterance_type = "year"

    elif "test" in intents:
        utterance_type = "test"

    status.set_(status=StatusLabels.SPEAK, data=utterance_type)


def speak(utterance: str) -> None:
    """Misty speaks the `utterance`."""
    print(utterance)

    speaking = misty.perform_action(
        "speak",
        data={"Text": utterance, "Flush": "true"},
    ).parse_to_dict()
    action_log.append_({"speaking": speaking})

    label = StatusLabels.REINIT
    if status.get_("data") == "goodbye":
        label = StatusLabels.STOP

    status.set_(status=label)


def perform_reply() -> None:
    """Formulates and speaks the reply based on the reply type obtained in the previous step (choosing a reply)."""
    print("Replying")
    reply_type = status.get_("data")

    if reply_type == "test":
        speak("I received your test.")

    elif reply_type == "unknown":
        speak("I am sorry, I do not understand.")

    elif reply_type == "hello":
        speak("Hello!")

    elif reply_type == "goodbye":
        speak("Goodbye!")

    elif reply_type == "year":
        now = datetime.datetime.now()
        speak("It is the year %s." % num2words(now.year))

    elif reply_type == "month":
        now = datetime.datetime.now()
        speak("It is the month of %s." % now.strftime("%B"))

    elif reply_type == "date":
        now = datetime.datetime.now()
        speak(
            "It is the %s of %s, year %s."
            % (
                num2words(now.day, to="ordinal"),
                now.strftime("%B"),
                num2words(now.year),
            )
        )


def subscribe():
    """Subscribes to VoiceRecord event."""
    subscribe_voice_record = misty.event(
        "subscribe", type="VoiceRecord", name=event_name, event_emitter=ee
    ).parse_to_dict()
    action_log.append_({"subscribe_voice_record": subscribe_voice_record})


def unsubscribe():
    """Unsubscribes from VoiceRecord event."""
    unsubscribe_voice_record = misty.event(
        "unsubscribe", name=event_name
    ).parse_to_dict()
    action_log.append_({"unsubscribe_voice_record": unsubscribe_voice_record})


def question_answering() -> Dict:
    """A skill that allows a person to have a simple dialogue with Misty.

    Returns:
        Dict: The dictionary with `"overall_success"` key (bool) and keys for every action performed (dictionarised Misty2pyResponse).
    """
    cancel_skills(misty)
    subscribe()
    status.set_(status=StatusLabels.REINIT)

    while status.get_("status") != StatusLabels.STOP:
        current_status = status.get_("status")

        if current_status == StatusLabels.REINIT:
            speech_capture()

        elif current_status == StatusLabels.INFER:
            perform_inference()

        elif current_status == StatusLabels.PREP:
            choose_reply()

        elif current_status == StatusLabels.SPEAK:
            perform_reply()

    unsubscribe()
    return success_of_action_list(action_log.get_())


if __name__ == "__main__":
    print(question_answering())
