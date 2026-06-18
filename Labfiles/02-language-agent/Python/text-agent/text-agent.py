from dotenv import load_dotenv
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

def main():
    try:
        # Clear the console
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Get Configuration Settings
        load_dotenv()
        foundry_endpoint = os.getenv('FOUNDRY_ENDPOINT')
        agent_name = os.getenv('AGENT_NAME')
        
        project_client = AIProjectClient(endpoint=foundry_endpoint, credential=DefaultAzureCredential())
        openai_client = project_client.get_openai_client()
        prompt = """Identify the PII entities in this article, and generate a redacted version:

    Microsoft was founded on April 4, 1975, by childhood friends Bill Gates (then 19) and Paul Allen (22) after they were inspired by the Altair 8800, one of the first personal computers, featured on the cover of Popular Electronics. They contacted the Altair’s maker, MITS, and successfully developed a version of the BASIC programming language, despite initially not owning the machine themselves. The pair formed a partnership called “Micro‑Soft” in Albuquerque, New Mexico, close to MITS’s headquarters, with the goal of writing software for emerging microcomputers.
    
    In the late 1970s, Microsoft grew by supplying programming languages to multiple hardware vendors, then relocated to the Seattle area in 1979. A pivotal moment came in 1980 when Microsoft partnered with IBM to provide an operating system for the IBM PC, leading to MS‑DOS and establishing the company’s dominance in personal computing. Gates guided the company’s long-term strategy as CEO, while Allen contributed key technical vision in its early years, setting Microsoft on a path that would reshape the software industry."""
        
        response = openai_client.responses.create(input=[{"role": "user", "content": prompt}], extra_body={"agent_reference":{"name": agent_name, "type": "agent_reference"}})

        print(f"Response:{response.output_text}")
        
    except Exception as ex:
        print(ex)

if __name__ == "__main__":
    main()