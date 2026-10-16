import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "envio-cvs")

ADZUNA_APP_ID: str = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY: str = os.getenv("ADZUNA_APP_KEY", "")
INFOJOBS_CLIENT_ID: str = os.getenv("INFOJOBS_CLIENT_ID", "")
INFOJOBS_CLIENT_SECRET: str = os.getenv("INFOJOBS_CLIENT_SECRET", "")

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILES_DIR: str = os.path.join(_BASE_DIR, "data", "profiles")
MOCK_JOBS_PATH: str = os.path.join(_BASE_DIR, "data", "mock_jobs.json")


def setup_langsmith() -> None:
    tracing_disabled = os.getenv("LANGSMITH_TRACING", "").lower() == "false"
    if tracing_disabled or not LANGSMITH_API_KEY:
        os.environ["LANGSMITH_TRACING"] = "false"
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        return
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGSMITH_PROJECT"] = LANGSMITH_PROJECT
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
