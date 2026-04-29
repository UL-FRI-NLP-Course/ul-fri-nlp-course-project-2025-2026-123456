#Work in progress: automatic specs extraction from PDF brochures using pdfplumber.

import json
import os
import re
from typing import List, Dict, Any, Optional
import pdfplumber


def _detect_brand(pdf_path: str) -> Optional[str]:  
    basename = os.path.basename(pdf_path).lower()
    dirpath = os.path.dirname(pdf_path).lower()

    return dirpath


def _clean_value(value: str) -> str:
    if not isinstance(value, str):
        value = str(value)
    return value.strip()




def extract_tables_from_pdf(pdf_path: str) -> List[List[Dict[str, str]]]:
    tables = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables()
                if page_tables:
                    for table in page_tables:
                        tables.append(table)
    except Exception as e:
        print(f"Error extracting tables from {pdf_path}: {e}")

    return tables


def extract_specs_from_pdf(pdf_path: str) -> Optional[Dict[str, Any]]:
    brand = _detect_brand(pdf_path)
 
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Search specified pages for tables
            for i, page in enumerate(pdf.pages):
                page_tables = page.extract_tables()

                if not page_tables:
                    continue

                # Process each table on the page
                for table in page_tables:
                    if not table:
                        continue

                    print(table)

    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}")
        return None

    return None


def extract_all_specs(pdf_dir: str = "data/pdfs") -> List[Dict[str, Any]]:
    specs_list = []

    for root, dirs, files in os.walk(pdf_dir):
        for fname in files:
            if fname.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, fname)
                print(f"Processing {pdf_path}...")

                specs = extract_specs_from_pdf(pdf_path)
                if specs:
                    specs_list.append(specs)
                    print(f"Extracted: {specs.get('brand')} {specs.get('model')}")
                else:
                    print(f"No specs extracted")

    return specs_list


if __name__ == "__main__":
    extracted = extract_specs_from_pdf("data/pdfs/audi/Audi_US A4_2019.pdf")
    print(extracted)
