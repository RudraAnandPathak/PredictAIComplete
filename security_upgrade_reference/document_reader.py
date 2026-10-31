from pathlib import Path

import pandas as pd
import pymupdf
from docx import Document


def read_document(file_path):
    """
    Read a supported document and return its extracted content.
    """

    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".pdf":
        pages = []

        with pymupdf.open(path) as pdf:
            for page_number, page in enumerate(pdf, start=1):
                text = page.get_text()

                pages.append(
                    {
                        "page": page_number,
                        "text": text,
                    }
                )

        return {
            "type": "pdf",
            "content": pages,
        }

    elif extension == ".docx":
        document = Document(path)

        paragraphs = [
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        return {
            "type": "docx",
            "content": paragraphs,
        }

    elif extension == ".csv":
        dataframe = pd.read_csv(path)

        return {
            "type": "tabular",
            "content": dataframe,
        }

    elif extension == ".xlsx":
        dataframe = pd.read_excel(path)

        return {
            "type": "tabular",
            "content": dataframe,
        }

    else:
        raise ValueError(
            f"Unsupported file format: {extension}"
        )


if __name__ == "__main__":
    print("PredictAI document reader is ready.")
