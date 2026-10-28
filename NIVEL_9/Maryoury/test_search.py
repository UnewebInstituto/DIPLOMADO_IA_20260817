import unittest

import main


class PdfSearchTests(unittest.TestCase):
    def test_chunk_text_generates_multiple_chunks(self):
        text = "Palabra " * 500
        chunks = main.chunk_text(text, chunk_size=200, overlap=40)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk.strip()) > 0 for chunk in chunks))

    def test_extract_pdf_text_handles_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            main.extract_text_from_pdf("archivo_inexistente.pdf")

    def test_build_rag_prompt_includes_context_and_question(self):
        prompt = main.build_rag_prompt("¿Cuál es la política?", ["Texto de evidencia 1", "Texto de evidencia 2"])
        self.assertIn("Contexto:", prompt)
        self.assertIn("¿Cuál es la política?", prompt)
        self.assertIn("Texto de evidencia 1", prompt)

    def test_format_citation_builds_source_reference(self):
        citation = main.format_citation("manual_rrhh.pdf", 12, "texto de ejemplo")
        self.assertIn("manual_rrhh.pdf", citation)
        self.assertIn("página 12", citation)
        self.assertIn("texto de ejemplo", citation)


if __name__ == "__main__":
    unittest.main()
