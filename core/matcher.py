from rapidfuzz import process, fuzz


def match_skins(candidates: list[str], skin_names: list[str], threshold: int = 65) -> list[tuple[str, int]]:
    """
    Fuzzy-match OCR candidate strings against known skin full_names.
    Returns list of (matched_full_name, score) tuples above threshold.
    Deduplicates within a single call.
    """
    if not skin_names or not candidates:
        return []

    seen = set()
    results = []
    for text in candidates:
        result = process.extractOne(
            text,
            skin_names,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=threshold,
        )
        if result is not None:
            matched_name, score, _ = result
            if matched_name not in seen:
                seen.add(matched_name)
                results.append((matched_name, score))

    return results
