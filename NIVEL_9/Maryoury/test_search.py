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


if __name__ == "__main__":
    unittest.main()
