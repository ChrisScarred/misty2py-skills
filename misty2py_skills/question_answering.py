from typing import Dict, List, Tuple
from misty2py.utils.base64 import *
from pymitter import EventEmitter
from misty2py.utils.generators import get_random_string
import os
import datetime
from num2words import num2words

from misty2py_skills.utils.utils import get_misty, get_abs_path, get_files_in_dir, get_base_fname_without_ext, get_wit_ai_key
from misty2py_skills.utils.status import Status, ActionLog
from misty2py_skills.utils.converse import success_parser_from_dicts, success_parser_from_list
from misty2py_skills.essentials.speech_transcripter import SpeechTranscripter


ee = EventEmitter()
misty = get_misty()
status = Status()
action_log = ActionLog()
user_speech_event = "user_speech_" + get_random_string(6)
speech_transcripter = SpeechTranscripter(get_wit_ai_key())

SAVE_DIR = get_abs_path("data")
SPEECH_FILE = "capture_Dialogue.wav"


def _next_name(dir_ : str) -> str:
    files = get_files_in_dir(dir_)
    highest = 0
    if len(files) > 0:
        highest = max([int(get_base_fname_without_ext(f).lstrip("0")) for f in files])
    return os.path.join(dir_, "%s.wav" % str(highest+1).zfill(4))


def _get_audio_names() -> List[str]:
    dict_list = misty.get_info("audio_list").get("result", [])
    audio_list = []
    for d in dict_list:
        audio_list.append(d.get("name"))
    return audio_list


@ee.on(user_speech_event)
def listener(data: Dict):   
    if data.get("errorCode", -1) == 0:
        status.set_(status="inference")

    if data.get("errorCode", -1) == 3:
        status.set_(status="reinit")
    

def speech_capture_init() -> None:
    capture_speech = misty.perform_action("speech_capture", data={"RequireKeyPhrase": False})
    action_log.append_({"capture_speech": capture_speech})


def perform_inference() -> None:
    if SPEECH_FILE in _get_audio_names():
        speech_json = misty.get_info(
            "audio_file", 
            params = {
                "FileName": SPEECH_FILE,
                "Base64": "true"
            }
        )
        speech_base64 = speech_json.get("result", {}).get("base64", "")
        if len(speech_base64) > 0:
            f_name = _next_name(SAVE_DIR)
            base64_to_content(
                speech_base64, 
                save_path = f_name
            )
            speech_wav = speech_transcripter.load_wav(f_name)
            speech_text = speech_transcripter.audio_to_text(speech_wav, show_all=True)
            status.set_(status="prepare_reply", data=speech_text)
        else:
            status.set_(status="reinit")
    else:
        status.set_(status="reinit")


def _get_intents_keywords(entities: Dict) -> Tuple[List[str], List[str]]:
    intents = []
    keywords = []
    for key, val in entities.items():
        if key == "intent":
            intents.extend([dct.get("value") for dct in val])
        else:
            keywords.append(key)
    return intents, keywords


def choose_reply() -> None:
    data = status.get("data").get("content", {})    
    intents, keywords = _get_intents_keywords(data.get("entities"))
    
    if "greet" in intents:
        if "hello" in keywords:
            status.set_(status="ready_to_speak", data="hello")
        elif "goodbye" in keywords:
            status.set_(status="ready_to_speak", data="goodbye")
        else:
            status.set_(status="ready_to_speak", data="hello")
    
    elif "datetime" in intents:
        if "date" in keywords:
            status.set_(status="ready_to_speak", data="date")
        elif "month" in keywords:
            status.set_(status="ready_to_speak", data="month")
        elif "year" in keywords:
            status.set_(status="ready_to_speak", data="year")
        else:
            status.set_(status="ready_to_speak", data="unknown")
    
    elif "test" in intents:
        status.set_(status="ready_to_speak", data="test")
    
    else:
        status.set_(status="ready_to_speak", data="unknown")


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
    
    if status.get("data") == "goodbye":
        status.set_(status="stop")
    else:
        status.set_(status="reinit")


def perform_reply() -> None:
    _type = status.get("data")
    
    if _type == "test":
        speak("I received your test.")
    
    elif _type == "unknown":
        speak("I am sorry, I do not understand.")
    
    elif _type == "hello":
        speak("Hello!")
    
    elif _type == "goodbye":
        speak("Goodbye!")
    
    elif _type == "year":
        now = datetime.datetime.now()
        speak("It is the year %s." % now.year)
    
    elif _type == "month":
        now = datetime.datetime.now()
        speak("It is the month of %s." % now.strftime("%B"))
    
    elif _type == "date":
        now = datetime.datetime.now()
        speak(             
            "It is the %s of %s, year %s." % (
                num2words(now.day, to='ordinal'), 
                now.strftime("%B"), 
                now.year
            )
        )


def question_answering() -> Dict:
    audio_status = misty.get_info("audio_status")
    action_log.append_({"audio_status": audio_status})

    if not audio_status.get("result"):
        enable_audio = misty.perform_action("audio_enable")
        if not enable_audio.get("result"):
            return success_parser_from_dicts(audio_status=audio_status, enable_audio=enable_audio)
        action_log.append_({"enable_audio": enable_audio})

    set_volume = misty.perform_action("volume_settings", data="low_volume")
    action_log.append_({"set_volume": set_volume})

    subscribe_voice_record = misty.event("subscribe", type = "VoiceRecord", name = user_speech_event, event_emitter = ee)
    action_log.append_({"subscribe_voice_record": subscribe_voice_record})
    
    print("Listening")
    speech_capture_init()

    while status.get("status") != "stop":
        current_status = status.get("status")

        if current_status == "reinit":
            status.set_(status="initialised")
            print("Listening")
            speech_capture_init()

        elif current_status == "inference":
            print("Analysing")
            perform_inference()

        elif current_status == "prepare_reply":
            print("Preparing the reply")
            choose_reply()

        elif current_status == "ready_to_speak":
            print("Replying")
            perform_reply()

    unsubscribe_voice_record = misty.event("unsubscribe", name = user_speech_event)
    action_log.append_({"unsubscribe_voice_record": unsubscribe_voice_record})

    return success_parser_from_list(action_log.get_())

if __name__=="__main__":
    print(question_answering())
