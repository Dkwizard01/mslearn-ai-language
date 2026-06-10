import os
from pathlib import Path
from playsound3 import playsound
from dotenv import load_dotenv
import base64
from urllib.parse import urlparse, urlunparse
# Import namespaces
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

def main():
    try:
        # Clear the console
        os.system('cls' if os.name == 'nt' else 'clear')

        # Get Configuration Settings
        load_dotenv()
        endpoint = os.getenv("MODEL_ENDPOINT")
        model_deployment = os.getenv("MODEL_NAME")
        speech_file_path = Path(__file__).parent / "speech.mp3"

        # Create the Azure OpenAI client
        token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://ai.azure.com/.default")
        client = AzureOpenAI(azure_endpoint=endpoint, azure_ad_token_provider=token_provider, api_version="2025-03-01-preview")

        # Generate speech and save to file
        response = client.chat.completions.create(
            model=model_deployment,
            modalities=["text", "audio"],
            audio={"voice": "echo", "format": "mp3"},
            messages=[
                {"role": "user", "content": "This is an implementation of the lab for Use speech-capable generative AI models."}
            ],
        )
        res = response.choices[0].message.audio.data
        audio = base64.b64decode(res)
        with open(speech_file_path, "wb") as audio_file:
            audio_file.write(audio)

        print(f"Saved generated speech to: {speech_file_path}")

        # Play the generated speech file
       # playsound(speech_file_path)

    except Exception as ex:
        print(ex)

if __name__ == "__main__":
    main() 
