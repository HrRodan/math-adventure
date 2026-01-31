import os
from dotenv import load_dotenv

# Absolute Pfade für Zuverlässigkeit
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

class LLMProvider:
    def __init__(self, id, name, api_key_env, models, base_url=None, litellm_prefix="", extra_params=None):
        self.id = id
        self.name = name
        self.api_key_env = api_key_env
        self.models = models
        self.base_url = base_url
        self.litellm_prefix = litellm_prefix 
        self.extra_params = extra_params or {}

    def get_api_key(self):
        return os.getenv(self.api_key_env)

PROVIDERS = {
    "google": LLMProvider(
        id="google",
        name="Google Gemini",
        api_key_env="GEMINI_API_KEY",
        litellm_prefix="gemini/",
        models=[
            "gemini-3-flash-preview",
            "gemini-2.0-flash",
            "gemini-1.5-flash"
        ]
    ),
    "openai": LLMProvider(
        id="openai",
        name="OpenAI",
        api_key_env="OPENAI_API_KEY",
        litellm_prefix="", # Standard OpenAI braucht kein Präfix
        models=[
            "gpt-4o-mini",
            "gpt-5-mini"
        ],
        extra_params={"drop_params": True}
    ),
    "openrouter": LLMProvider(
        id="openrouter",
        name="OpenRouter",
        api_key_env="OPENROUTER_API_KEY",
        # Wir nutzen das native LiteLLM Präfix für OpenRouter
        litellm_prefix="openrouter/", 
        models=[
            "openai/gpt-oss-120b",
            "deepseek/deepseek-chat",
            "nousresearch/hermes-3-llama-3.1-405b"
        ]
    )
}

def get_all_models():
    all_models = []
    for provider in PROVIDERS.values():
        all_models.extend(provider.models)
    return all_models

def get_provider_for_model(model_name):
    for provider in PROVIDERS.values():
        if model_name in provider.models:
            return provider
    return None
