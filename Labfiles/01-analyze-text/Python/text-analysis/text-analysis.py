from dotenv import load_dotenv
import os
from azure.identity import DefaultAzureCredential
from azure.ai.textanalytics import TextAnalyticsClient

def main():
    try:
        # Clear the console
        os.system('cls' if os.name == 'nt' else 'clear')

        # Get Configuration Settings
        load_dotenv()
        foundry_endpoint = os.getenv('FOUNDRY_ENDPOINT')
        

        credential = DefaultAzureCredential(exclude_managed_identity_credential=True)
        ai_client = TextAnalyticsClient(foundry_endpoint, credential)

        reviews_folder = 'reviews'
        for file_name in os.listdir(reviews_folder):
            # Read the file contents
            print('\n-------------\n' + file_name)
            text = open(os.path.join(reviews_folder, file_name), encoding='utf8').read()
            print('\n' + text)

        detected_language = ai_client.detect_language([text])[0]
        print("\nLanguage: {}".format(detected_language.primary_language.name))
        enteties = ai_client.recognize_entities([text])[0].entities
        if(len(enteties) > 0):
            print("\nEnteties")
            for entity in enteties:
             print("\t{} ({})".format(entity.text, entity.category))
        pii_entities = ai_client.recognize_pii_entities([text])[0]
        if (len(pii_entities.entities) > 0):
            print("\nPIIEntities:")
            for pii_entity in pii_entities.entities:
                print("\t{} ({})".format(pii_entity.text, pii_entity.category))
            print("Redacted Text:\n{}".format(pii_entities.redacted_text))
    except Exception as ex:
        print(ex)


if __name__ == "__main__":
    main()