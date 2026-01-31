import os
from dotenv import load_dotenv

# Absolute Pfade für Zuverlässigkeit sicherstellen
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

class LLMProvider:
    """
    Repräsentiert einen LLM-Anbieter (z.B. Google, OpenAI, OpenRouter).
    
    Attributes:
        id (str): Interne ID des Providers.
        name (str): Anzeigename für Logs/UI.
        api_key_env (str): Name der Umgebungsvariable, die den API-Key hält.
        models (list[str]): Liste der verfügbaren Modell-IDs (wie sie im UI erscheinen).
        base_url (str, optional): Benutzerdefinierte API-Basis-URL (z.B. für OpenRouter).
        litellm_prefix (str, optional): Präfix für LiteLLM (z.B. 'gemini/', 'openrouter/').
        extra_params (dict, optional): Zusätzliche Parameter für den `completion` Aufruf (z.B. drop_params).
    """
    def __init__(self, id, name, api_key_env, models, base_url=None, litellm_prefix="", extra_params=None):
        self.id = id
        self.name = name
        self.api_key_env = api_key_env
        self.models = models 
        self.base_url = base_url
        self.litellm_prefix = litellm_prefix 
        self.extra_params = extra_params or {}

    def get_api_key(self):
        """Holt den API-Key sicher aus den Umgebungsvariablen."""
        return os.getenv(self.api_key_env)

# --- KONFIGURATION DER PROVIDER ---
# Hier können neue Modelle hinzugefügt werden.
# Wichtig: litellm_prefix steuert das Routing in der llm_engine.

PROVIDERS = {
    "google": LLMProvider(
        id="google",
        name="Google Gemini",
        api_key_env="GEMINI_API_KEY",
        litellm_prefix="gemini/", # Zwingt LiteLLM, den Google AI Studio Pfad zu nutzen
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
        litellm_prefix="", # Standard OpenAI benötigt kein Prefix
        models=[
            "gpt-4o-mini",
            "gpt-5-mini" # Platzhalter für zukünftige Modelle
        ],
        extra_params={"drop_params": True} # Wichtig für Modelle, die bestimmte Parameter (wie temperature) nicht unterstützen
    ),
    "openrouter": LLMProvider(
        id="openrouter",
        name="OpenRouter",
        api_key_env="OPENROUTER_API_KEY",
        litellm_prefix="openrouter/", # Natives LiteLLM Routing für OpenRouter
        models=[
            "openai/gpt-oss-120b", 
            "deepseek/deepseek-v3.2",
            "nousresearch/hermes-4-70b"
        ]
    )
}

def get_all_models():
    """Gibt eine flache Liste aller verfügbaren Modell-Namen zurück (für das UI-Dropdown)."""
    all_models = []
    for provider in PROVIDERS.values():
        all_models.extend(provider.models)
    return all_models

def get_provider_for_model(model_name):
    """Ermittelt den zuständigen Provider anhand des Modellnamens."""
    for provider in PROVIDERS.values():
        if model_name in provider.models:
            return provider
    return None