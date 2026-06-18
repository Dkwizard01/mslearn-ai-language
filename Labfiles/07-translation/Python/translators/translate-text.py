from dotenv import load_dotenv
import os
from azure.identity import DefaultAzureCredential
from azure.ai.translation.text import *
from azure.ai.translation.text.models import InputTextItem
# import namespaces



def main():
    try:
        # Clear the console 
        os.system('cls' if os.name == 'nt' else 'clear')

        # Get Configuration Settings
        load_dotenv()
        foundry_endpoint = os.getenv('FOUNDRY_ENDPOINT')
        client = TextTranslationClient(endpoint=foundry_endpoint, credential=DefaultAzureCredential())
        available_languages = client.get_supported_languages(scope="translation")
        # Choose target language
        print("{} languages supported.".format(len(languagesResponse.translation)))
        print("(See https://learn.microsoft.com/azure/ai-services/translator/language-support#translation)")
        print("Enter a target language code for translation (for example, 'en'):")
        supportedLanguage = False
        while supportedLanguage == False:
         targetLanguage = input()
        if  targetLanguage in available_languages.translation.keys():
            supportedLanguage = True
        else:
          print(f"{targetLanguage} is not a supported language.")
    # Translate text
        inputText = ""
        while inputText.lower() != "quit":
          inputText = input("Enter text to translate ('quit' to exit):")
          if inputText != "quit":
           input_text_elements = [InputTextItem(text=inputText)]
           translationResponse = client.translate(body=input_text_elements, to_language=[targetLanguage])
           translation = translationResponse[0] if translationResponse == True else None
           if translation == True:
              sourceLanguage = translation.detected_language
              for translated_text in translation.translations:
                print(f"'{inputText}' was translated from {sourceLanguage.language} to {translated_text.to} as '{translated_text.text}'.")
        


    except Exception as ex:
        print(ex)


if __name__ == "__main__":
    main()