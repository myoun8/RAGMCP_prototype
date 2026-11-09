"""Model discovery and provider routing without application startup side effects."""

import json
from urllib.error import URLError
from urllib.request import Request, urlopen

RCHAT_BASE_URL = "https://rchat.nist.gov/api/v1"
DEFAULT_RCHAT_MODEL = "Muse-Glimmer-30B"
MODEL_CATALOG = {
    "openai": ["gpt-4o"],
    "anthropic": ["claude-3-5-sonnet-20241022"],
    "google": ["gemini-3.5-flash"],
    "rchat": [DEFAULT_RCHAT_MODEL, "Muse-Spark-Open-816B-A42B-NVFP4"],
}


def provider_for_model(model: str, provider: str | None = None) -> str:
    # Explicit routing allows newly discovered RChat IDs without guessing their
    # provider from a vendor-like prefix (RChat can also serve gpt-* IDs).
    if provider is not None:
        if provider not in MODEL_CATALOG:
            raise ValueError(f"Unsupported provider '{provider}'.")
        return provider
    for name, models in MODEL_CATALOG.items():
        if model in models:
            return name
    if model.startswith(("gpt-", "o1", "o3")):
        return "openai"
    if model.startswith("claude-"):
        return "anthropic"
    if model.startswith("gemini-"):
        return "google"
    raise ValueError(f"Unrecognized model '{model}'. Cannot determine provider.")


def discover_models(api_key: str = "") -> tuple[dict[str, list[str]], bool]:
    """Return a per-request catalog; never cache a user's key or model access.

    The boolean indicates successful RChat discovery. Missing credentials,
    upstream errors and unusable catalogs retain the current fallback models.
    """
    catalog = {provider: list(models) for provider, models in MODEL_CATALOG.items()}
    if not api_key.strip():
        return catalog, False
    try:
        request = Request(
            f"{RCHAT_BASE_URL}/models",
            headers={"Authorization": f"Bearer {api_key.strip()}"},
        )
        with urlopen(request, timeout=10) as response:
            payload = json.load(response)
        models = []
        for entry in payload["data"]:
            model = entry.get("id") if isinstance(entry, dict) else None
            # RChat's embeddinggemma endpoint cannot participate in chat/tool
            # requests. Exclude embedding models from the chat picker.
            if isinstance(model, str) and model.strip() and "embed" not in model.lower():
                if model not in models:
                    models.append(model)
        if models:
            catalog["rchat"] = models
            return catalog, True
    except (URLError, OSError, ValueError, KeyError, TypeError):
        pass
    return catalog, False
