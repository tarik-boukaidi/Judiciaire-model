from huggingface_hub import HfApi
from dotenv import load_dotenv
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env", override=True)
TOKEN = os.getenv("HF_TOKEN")

REPO_ID = "moaaddaoudi/judiciaire-model"
LOCAL_FOLDER = PROJECT_DIR / "atlas-deploy"

if not TOKEN:
    raise SystemExit("HF_TOKEN is empty. Add a Hugging Face write token to the project .env file.")

api = HfApi()
identity = api.whoami(token=TOKEN)
print(f"Authenticated to Hugging Face as: {identity.get('name', 'unknown account')}")

print("Uploading deployment folder to Hugging Face Space...")
result = api.upload_folder(
    folder_path=LOCAL_FOLDER,
    repo_id=REPO_ID,
    repo_type="space",
    token=TOKEN,
    create_pr=False,
    commit_message="Add missing text splitter dependency"
)
print(f"Upload submitted. Review the Hugging Face result: {result}")
