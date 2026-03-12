from langsmith import utils
from dotenv import load_dotenv
load_dotenv()

# Check and print whether LangSmith tracing is currently enabled
print(f"LangSmith tracing is enabled: {utils.tracing_is_enabled()}")