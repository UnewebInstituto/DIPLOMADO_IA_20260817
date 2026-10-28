import pytest

from main import build_rag_prompt


def test_build_rag_prompt_includes_citation_evidence():
    result = {
        "documents": [["El sistema requiere autenticación mediante la cuenta corporativa."]],
        "metadatas": [[{"fuente": "manual_ti.pdf", "pagina": 12}]],
    }

    prompt = build_rag_prompt("¿Cómo ingreso al sistema?", result)

    assert "manual_ti.pdf" in prompt
    assert "Página: 12" in prompt
    assert "autenticación" in prompt.lower()
