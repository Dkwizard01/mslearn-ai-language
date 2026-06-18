import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
import azure.cognitiveservices.speech as speech
def main():
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        load_dotenv()
        foundry_endpoint = os.getenv('FOUNDRY_ENDPOINT')
        credential = DefaultAzureCredential()
        translation_config = speech.translation.SpeechTranslationConfig(endpoint = foundry_endpoint, token_credential=credential)
        translation_config.speech_recognition_language = "de-DE"
        target_languages = input("Add target language using the ISO-639 code. Seperate the codes by spaces:").split()
        for target in target_languages:
            translation_config.add_target_language(target)
        audio_input_config = speech.AudioConfig(use_default_microphone=True)
        speech_config = speech.SpeechConfig(token_credential=credential, endpoint=foundry_endpoint)
        audio_output_config = speech.AudioConfig(use_default_microphone=True)
        voices = {
            "fr": "fr-FR-HenriNeural",
            "es": "es-ES-ElviraNeural",
            "hi": "hi-IN-MadhurNeural",
        }
        translator = speech.translation.TranslationRecognizer(translation_config=translation_config, audio_config=audio_input_config)
        print("Speak now.")
        translation_results = translator.recognize_once_async().get()
        for translations in translation_results.translations:
            speech_config.speech_synthesis_voice_name = voices.get(translations)
            speech_synthesizer = speech.SpeechSynthesizer(audio_config=audio_output_config, speech_config=speech_config)
            speaking = speech_synthesizer.speak_text_async(translation_results.translations[translations]).get()
            if speaking.reason != speech.ResultReason.SynthesizingAudioCompleted:
                print(speaking.reason.cancellation_details)
    except Exception as ex:
        print(ex)


if __name__ == "__main__":
    main()
