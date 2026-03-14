# ============================================================
# llm.py
# Clean LLM Factory (OpenAI / Gemini / Groq via OpenAI API)
# ============================================================

from langchain_openai import ChatOpenAI
from config.settings import settings


def get_llm():
    provider = settings.LLM_PROVIDER.lower()

    # ================= OPENAI =================
    if provider == "openai":
        return ChatOpenAI(
            model=settings.LLM_MODEL_OPENAI,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
        )

    # ================= GROQ (OpenAI Compatible) =================
    elif provider == "groq":
        return ChatOpenAI(
            model="llama-3.1-8b-instant",
            openai_api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            temperature=settings.LLM_TEMPERATURE,
        )

    # ================= GEMINI =================
    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL_GEMINI,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
        )

    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER: '{provider}'. "
            "Choose 'openai', 'gemini', or 'groq'."
        )
