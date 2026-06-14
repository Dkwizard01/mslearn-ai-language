from dotenv import load_dotenv
import os
from playsound3 import playsound
from azure.identity import DefaultAzureCredential
import azure.cognitiveservices.speech as speech
from pathlib import Path
# Import namespaces
def main():
    try:
        # Clear the console
        os.system('cls' if os.name == 'nt' else 'clear')
        load_dotenv()
        foundry_endpoint = os.getenv('FOUNDRY_ENDPOINT')
        # Create speech_config using Entra ID authentication
        speech_config = speech.SpeechConfig(token_credential=DefaultAzureCredential(), endpoint = foundry_endpoint)

        inputText = ""
        while inputText.lower() != "3":
            inputText = input("Choose an option:\n1: Record a greeting\n2: Transcribe messages\n3: Exit\n")
            if inputText != "3":
                if inputText == "1":
                    record_greeting(speech_config)
                elif inputText == "2":
                    transcribe_messages(speech_config)
                elif inputText == "3":
                    print("Exiting...")
                    return
                else:
                    print("Invalid option, please try again.")
    except Exception as ex:
        print(ex)

# record_greeting function
def record_greeting(speech_config):
    print("Recording greeting...")

    # Get message from user
    greeting_message = input("Enter your greeting message: ")
    # Synthesize the message to an audio file
    out_path = Path(__file__).parent /"message.wav"
    audio_config = speech.audio.AudioOutputConfig(filename=out_path)
    speech_config.speech_synthesis_voice_name = "en-US-Serena:DragonHDLatestNeural"
    speech_synthesizer = speech.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    result = speech_synthesizer.speak_text_async(greeting_message).get()
    if result.reason == speech.ResultReason.SynthesizingAudioCompleted:
        print(f"Greeting saved to  {out_path}")
        speech_synthesizer = None
    else:
        print(f"Error generating greeting {result.cancellation_details.error_details}")


# transcribe_messages function
def transcribe_messages(speech_config):
    print("Transcribing messages...")
    messages_folder = Path(__file__).parent/'messages'
    for file_name in os.listdir(messages_folder):
        if file_name.endswith('.wav'):
            print(f"\nTranscribing {file_name}...")
            file_path = os.path.join(messages_folder, file_name)
            playsound(file_path)
            # Transcribe the audio file
            audio_config = speech.audio.AudioConfig(filename=file_path)
            speech_recognizer = speech.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config,)
            result = speech_recognizer.recognize_once_async().get()
            if result.reason == speech.ResultReason.RecognizedSpeech:
             with open(Path(__file__).parent/"transcriptions.txt", "a") as file:
              file.write(file_name + "\n" + result.text + "\n")
            else:
                 print(f"Error: {result.cancellation_details.error_details}")
if __name__ == "__main__":
    main()
