import openai
import os
from dotenv import load_dotenv
load_dotenv()

def init_Generative_Agent():
    openai.api_key = os.getenv("AZURE_OPENAI_KEY")
    openai.api_base = os.getenv(
        "AZURE_OPENAI_ENDPOINT")  # your endpoint should look like the following https://YOUR_RESOURCE_NAME.openai.azure.com/
    openai.api_type = 'azure'
    openai.api_version = "2023-07-01-preview"#'2023-05-15'  # this may change in the future
    azure_openai_engine = os.getenv(
        "AZURE_OPENAI_DEPLOYMENT_NAME")  # This will correspond to the custom name you chose for your deployment when you deployed a model.
    return azure_openai_engine
