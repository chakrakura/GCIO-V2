import json

from django.conf import settings


class GeminiConfigError(Exception):
    pass


class GeminiRequestError(Exception):
    pass


BASE_SYSTEM_INSTRUCTION = (
    'You are a financial research analyst writing for an investment research portal called '
    'The Global CIO Office. Given the request below, write a report draft. '
    'Respond ONLY with JSON in this exact shape: {"title": "...", "body_html": "..."}. '
    'body_html must be well-formatted HTML using only <p>, <h2>, <h3>, <ul>, <li>, <strong>, <em> tags '
    '(no <html> or <body> wrapper, no markdown, no code fences, no extra commentary).'
)


def provider_status():
    """Connection status for every configured AI provider, for display in the report editor.
    Only Gemini is actually wired into generate_draft() below — the others are shown so an
    admin can see what's configured, not because they're usable for drafting yet."""
    from modules.ai_integration.models import AIProviderConfig

    configs = {c.provider: c for c in AIProviderConfig.objects.all()}
    gemini_key, _ = _gemini_config()

    return [
        {'key': 'gemini', 'label': 'Gemini', 'connected': bool(gemini_key), 'usable': True},
        {
            'key': 'openai', 'label': 'ChatGPT',
            'connected': bool(configs.get('openai') and configs['openai'].is_connected),
            'usable': False,
        },
        {
            'key': 'anthropic', 'label': 'Claude',
            'connected': bool(configs.get('anthropic') and configs['anthropic'].is_connected),
            'usable': False,
        },
    ]


def _gemini_config():
    """DB-stored key (set via AI Integration settings) takes priority over .env,
    so admins can update it from the UI without touching the server."""
    from modules.ai_integration.models import AIProviderConfig

    db_config = AIProviderConfig.objects.filter(provider=AIProviderConfig.PROVIDER_GEMINI).first()
    api_key = (db_config.api_key if db_config and db_config.api_key else '') or settings.GEMINI_API_KEY
    model_name = (db_config.default_model if db_config and db_config.default_model else '') or settings.GEMINI_MODEL
    return api_key, model_name


def generate_draft(prompt):
    from modules.ai_integration.models import AIGenerationDefaults

    api_key, model_name = _gemini_config()
    if not api_key:
        raise GeminiConfigError(
            'No Gemini API key configured. Add one under AI Integration, or set GEMINI_API_KEY in your .env file.'
        )

    defaults = AIGenerationDefaults.load()
    system_instruction = BASE_SYSTEM_INSTRUCTION
    if defaults.house_style_instructions:
        system_instruction += f'\n\nHouse style: {defaults.house_style_instructions}'

    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    try:
        response = model.generate_content(
            f'{system_instruction}\n\nRequest: {prompt}',
            generation_config={
                'response_mime_type': 'application/json',
                'temperature': defaults.temperature,
            },
        )
    except Exception as exc:
        raise GeminiRequestError(str(exc)) from exc

    try:
        data = json.loads(response.text)
        title = data['title']
        body_html = data['body_html']
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise GeminiRequestError('Gemini returned an unexpected response format.') from exc

    return title, body_html
