def test_angry_expression(capsys):
    from misty2py_skills.expressions.angry import angry_expression
    from misty2py_skills.utils.utils import get_misty

    with capsys.disabled():
        result = angry_expression(get_misty())
        print(result)
        assert result.get("overall_success")


def test_battery_printer(capsys):
    from misty2py_skills.demonstrations.battery_printer import battery_printer
    from misty2py_skills.utils.utils import get_misty

    with capsys.disabled():
        result = battery_printer(get_misty(), 2)
        print(result)
        assert result.get("overall_success")


def test_explore(capsys):
    from misty2py_skills.demonstrations import explore

    with capsys.disabled():
        explore.explore()
        # assert True to show that the program does not crash during the interaction
        assert True


def test_face_recognition(capsys):
    from misty2py_skills import face_recognition
    from misty2py_skills.utils.utils import get_misty

    with capsys.disabled():
        result = face_recognition.face_recognition(get_misty())
        print(result)
        assert result.get("overall_success")


def test_free_memory(capsys):
    from misty2py_skills.essentials.free_memory import free_memory
    from misty2py_skills.utils.utils import get_misty

    with capsys.disabled():
        result = free_memory(get_misty(), "data")
        print(result)
        assert result.get("overall_success")


def test_hey_misty(capsys):
    from misty2py_skills import hey_misty

    with capsys.disabled():
        result = hey_misty.greet()
        print(result)
        assert result.get("overall_success")


def test_remote_control(capsys):
    from misty2py_skills import remote_control

    with capsys.disabled():
        result = remote_control.remote_control()
        print(result)
        assert result.get("overall_success")


def test_listening_expression(capsys):
    from misty2py_skills.expressions.listening import listening_expression
    from misty2py_skills.utils.utils import get_misty

    with capsys.disabled():
        result = listening_expression(get_misty())
        print(result)
        assert result.get("overall_success")


def test_speech_transcripter(capsys):
    from misty2py_skills.utils.utils import get_abs_path, get_wit_ai_key, get_files_in_dir, get_base_fname_without_ext
    from misty2py_skills.essentials.speech_transcripter import SpeechTranscripter
    from misty2py_skills.utils.converse import success_parser_from_list

    potential_audios = get_files_in_dir(get_abs_path("tests/data"))
    speech_transcripter = SpeechTranscripter(get_wit_ai_key())
    results = []
    for potential_audio in potential_audios:
        if potential_audio.endswith(".wav"):
            audio = speech_transcripter.load_wav(potential_audio)
            results.append(
                {
                    get_base_fname_without_ext(potential_audio): speech_transcripter.audio_to_text(audio)
                }                
            )
    
    with capsys.disabled():
        result = success_parser_from_list(results)
        print(result)
        # note that here, the speech transcription is considered successful if it is performed; not when it is accurate
        assert result.get("overall_success")
