import pytest

from main import build_rag_prompt, fallback_answer_from_context, get_embedding_model


def test_build_rag_prompt_includes_citation_evidence():
    result = {
        "documents": [["El sistema requiere autenticación mediante la cuenta corporativa."]],
        "metadatas": [[{"fuente": "manual_ti.pdf", "pagina": 12}]],
    }

    prompt = build_rag_prompt("¿Cómo ingreso al sistema?", result)

    assert "manual_ti.pdf" in prompt
    assert "Página: 12" in prompt
    assert "autenticación" in prompt.lower()


def test_fallback_answer_works_without_gemini_key():
    result = {
        "documents": [["El sistema requiere autenticación mediante la cuenta corporativa."]],
        "metadatas": [[{"fuente": "manual_ti.pdf", "pagina": 12}]],
    }

    answer = fallback_answer_from_context("¿Cómo ingreso al sistema?", result)

    assert "manual_ti.pdf" in answer
    assert "autenticación" in answer.lower()


def test_get_embedding_model_is_cached():
    model_1 = get_embedding_model()
    model_2 = get_embedding_model()

    assert model_1 is model_2
