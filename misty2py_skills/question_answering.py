from typing import Dict, List, Tuple
from misty2py.utils.base64 import *
from pymitter import EventEmitter
from misty2py.utils.generators import get_random_string
import os
import datetime
from num2words import num2words
from enum import Enum

from misty2py_skills.utils.utils import get_misty, get_abs_path, get_files_in_dir, get_base_fname_without_ext, get_wit_ai_key, cancel_skills
from misty2py_skills.utils.status import Status, ActionLog
from misty2py_skills.utils.converse import success_parser_from_list
from misty2py_skills.essentials.speech_transcripter import SpeechTranscripter


ee = EventEmitter()
misty = get_misty()
status = Status()
action_log = ActionLog()
event_name = "user_speech_" + get_random_string(6)
speech_transcripter = SpeechTranscripter(get_wit_ai_key())

SAVE_DIR = get_abs_path("data")
SPEECH_FILE = "capture_Dialogue.wav"

class StatusLabels(Enum):
    REINIT = "reinit"
    LISTEN = "listening"
    PREP = "prepare_reply"
    INFER = "infering"
    STOP = "stop"
    SPEAK = "ready_to_speak"


@ee.on(event_name)
def listener(data: Dict):   
    if data.get("errorCode", -1) == 0:
        status.set_(status = StatusLabels.INFER)

    if data.get("errorCode", -1) == 3:
        status.set_(status = StatusLabels.REINIT)


def get_next_file_name(dir_ : str) -> str:
    files = get_files_in_dir(dir_)
    highest = 0
    if len(files) > 0:
        highest = max([int(get_base_fname_without_ext(f).lstrip("0")) for f in files])
    return os.path.join(dir_, "%s.wav" % str(highest+1).zfill(4))


def get_all_audio_file_names() -> List[str]:
    dict_list = misty.get_info("audio_list").get("result", [])
    audio_list = []
    for d in dict_list:
        audio_list.append(d.get("name"))
    return audio_list


def speech_capture() -> None:
    print("Listening")

    audio_status = misty.get_info("audio_status")
    action_log.append_({"audio_status": audio_status})

    if not audio_status.get("result"):
        enable_audio = misty.perform_action("audio_enable")
        if not enable_audio.get("result"):
            action_log.append_({"enable_audio": enable_audio})
            status.set_(status = StatusLabels.STOP)
            return

    set_volume = misty.perform_action("volume_settings", data="low_volume")
    action_log.append_({"set_volume": set_volume})

    capture_speech = misty.perform_action("speech_capture", data={"RequireKeyPhrase": False})
    action_log.append_({"capture_speech": capture_speech})
    status.set_(status=StatusLabels.LISTEN)
    

def perform_inference() -> None:
    print("Analysing")
    label = StatusLabels.REINIT
    data = ""

    if SPEECH_FILE in get_all_audio_file_names():
        speech_json = misty.get_info(
            "audio_file", 
            params = {
                "FileName": SPEECH_FILE,
                "Base64": "true"
            }
        )
        speech_base64 = speech_json.get("result", {}).get("base64", "")
        if len(speech_base64) > 0:
            f_name = get_next_file_name(SAVE_DIR)
            base64_to_content(
                speech_base64, 
                save_path = f_name
            )
            speech_wav = speech_transcripter.load_wav(f_name)
            speech_text = speech_transcripter.audio_to_text(speech_wav, show_all=True)
            label = StatusLabels.PREP
            data = speech_text

    status.set_(status = label, data = data)


def get_intents_keywords(entities: Dict) -> Tuple[List[str], List[str]]:
    intents = []
    keywords = []
    for key, val in entities.items():
        if key == "intent":
            intents.extend([dct.get("value") for dct in val])
        else:
            keywords.append(key)
    return intents, keywords


def choose_reply() -> None:
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
    

    status.set_(status = StatusLabels.SPEAK, data = utterance_type)


def speak(utterance: str) -> None:
    print(utterance)

    speaking = misty.perform_action(
        "speak",
        data={
            "Text": utterance, 
            "Flush": "true"
        },
    )
    action_log.append_({"speaking": speaking})
    
    label = StatusLabels.REINIT
    if status.get_("data") == "goodbye":
        label = StatusLabels.STOP

    status.set_(status = label)


def perform_reply() -> None:
    print("Replying")
    utterance_type = status.get_("data")
    
    if utterance_type == "test":
        speak("I received your test.")
    
    elif utterance_type == "unknown":
        speak("I am sorry, I do not understand.")
    
    elif utterance_type == "hello":
        speak("Hello!")
    
    elif utterance_type == "goodbye":
        speak("Goodbye!")
    
    elif utterance_type == "year":
        now = datetime.datetime.now()
        speak("It is the year %s." % num2words(now.year))
    
    elif utterance_type == "month":
        now = datetime.datetime.now()
        speak("It is the month of %s." % now.strftime("%B"))
    
    elif utterance_type == "date":
        now = datetime.datetime.now()
        speak(             
            "It is the %s of %s, year %s." % (
                num2words(now.day, to='ordinal'), 
                now.strftime("%B"), 
                num2words(now.year)
            )
        )


def subscribe():
    subscribe_voice_record = misty.event("subscribe", type = "VoiceRecord", name = event_name, event_emitter = ee)
    action_log.append_({"subscribe_voice_record": subscribe_voice_record})


def unsubscribe():
    unsubscribe_voice_record = misty.event("unsubscribe", name = event_name)
    action_log.append_({"unsubscribe_voice_record": unsubscribe_voice_record})


def question_answering() -> Dict:
    cancel_skills(misty)
    subscribe()
    status.set_(status = StatusLabels.REINIT)

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
    return success_parser_from_list(action_log.get_())

if __name__=="__main__":
    print(question_answering())
