import re
import pymupdf

def extract_chunks(pdf_path, max_chars=800, overlap=100):
    remove_images = [".tif"]

    chunks = []
    current_chunk = ""

    doc = pymupdf.open(pdf_path)
    for i, page in enumerate(doc):
        blocks = page.get_text("blocks")

        for block in blocks:
            if block[6] != 0: # Only process text blocks
                continue

            text = block[4].strip()
            if any(text.endswith(ext) for ext in remove_images):
                continue

            if len(text) > max_chars:
                subchunks = chunk_text(text, max_chars=max_chars, overlap=overlap)
                # if len(subchunks[-1]) < max_chars // 2:
                #     chunks.extend(subchunks[:-1])
                #     current_chunk = subchunks[-1]
                # else:
                chunks.extend(subchunks)
                current_chunk = ""
                continue

            if len(current_chunk) + len(text) + 1 <= max_chars:
                current_chunk += "\n\n" + text if current_chunk else text
                continue

            chunks.append(current_chunk)
            current_chunk = text

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def chunk_text(text, max_chars=800, overlap=100):
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + max_chars, len(text))
            chunk = text[start:end]
            chunks.append(chunk)
            start += max_chars - overlap
        return chunks
    