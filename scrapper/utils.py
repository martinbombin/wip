# Helper function to extract text from <dl> tags, including dt and dd items.
def extract_dl_text(dl_tag):
    texts = []

    for item in dl_tag.find_all(["dt", "dd"]):
        texts.append(item.get_text(strip=True))

    return "\n".join(texts)
