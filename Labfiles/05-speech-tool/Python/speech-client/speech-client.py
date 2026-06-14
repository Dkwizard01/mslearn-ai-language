from dotenv import load_dotenv
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from pathlib import Path
def main():
    try:
        os.system("cls" if os.name == "nt" else "clear")
        load_dotenv()
        foundry_endpoint = os.getenv("FOUNDRY_ENDPOINT")
        agent_name = os.getenv("AGENT_NAME")
        project_client = AIProjectClient(endpoint = foundry_endpoint, credential= DefaultAzureCredential())
        openai_client = project_client.get_openai_client()
        while True:
            prompt = input("Enter your prompt:\n")
            if prompt.lower() == "quit" or len(prompt) == 0:
                break
            else:
             response = openai_client.responses.create(input = [{"role": "user", "content": prompt}], 
                                       extra_body= {"agent_reference": {"name": agent_name, "type": "agent_reference"}})
             with  open(Path(__file__).parent/"agent_response.txt", "a") as file:
              file.write(f"User: {prompt}\n {agent_name}: {response.output_text}" )
            
    except Exception as ex:
        print(ex)
                  

if __name__ == "__main__":
   main()