"""Lightweight "is this API key valid" pings for each provider — list models rather than
generate content, to avoid token cost during a connection test.
"""


def test_openai(api_key):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        client.models.list()
        return True, None
    except Exception as exc:
        return False, str(exc)


def test_anthropic(api_key):
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        client.models.list()
        return True, None
    except Exception as exc:
        return False, str(exc)


def test_gemini(api_key):
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        list(genai.list_models())
        return True, None
    except Exception as exc:
        return False, str(exc)


TESTERS = {
    'openai': test_openai,
    'anthropic': test_anthropic,
    'gemini': test_gemini,
}
