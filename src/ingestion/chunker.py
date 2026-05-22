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


def extract_headings(pdf_path, size_multiplier=1.25, min_abs_size=11):
    doc = pymupdf.open(pdf_path)

    # 1) Try TOC / bookmarks first
    toc = doc.get_toc(simple=True)
    if toc:
        # toc entries: (level, title, page)
        return [entry[1].strip() for entry in toc if entry[1].strip()]

    # 2) Gather all spans with their font sizes and names
    spans = []
    for page in doc:
        info = page.get_text("dict")  # blocks -> lines -> spans
        for b in info.get("blocks", []):
            for line in b.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue
                    spans.append({
                        "text": text,
                        "size": span.get("size", 0),
                        "font": span.get("font", "").lower(),
                        "bbox": span.get("bbox", None),
                        "page": page.number + 1
                    })

    if not spans:
        return []

    # 3) Compute a dynamic threshold: > median * multiplier or > min_abs_size
    sizes = [s["size"] for s in spans if s["size"] > 0]
    median = sorted(sizes)[len(sizes)//2]
    threshold = max(median * size_multiplier, min_abs_size)

    # 4) Heuristics: big size OR font name contains 'bold' OR all-caps short line
    candidates = []
    for s in spans:
        t = s["text"]
        votes = 0
        is_big = s["size"] >= threshold
        is_bold = "bold" in s["font"] or "black" in s["font"]
        is_caps = t.upper() == t
        is_correct_length = 5 <= len(t) <= 100

        if is_big and is_correct_length or is_bold and is_correct_length or is_caps and is_correct_length:
            clean = " ".join(t.split())
            if len(clean) > 1 and not clean.endswith(":"):
                candidates.append(clean)

    # 5) De-duplicate while preserving order, optional frequency filter
    seen = set()
    unique = []
    for c in candidates:
        key = c.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(c)

    return unique
    

if __name__ == "__main__":
    pdf_path = r"C:\Development\Sola\NLP\ul-fri-nlp-course-project-2025-2026-123456\data\pdfs\lexus\Lexus_US LS_2025.pdf"
    headings = extract_headings(pdf_path)
    print("Extracted Headings:")
    for h in headings:
        print(f"  {h}")