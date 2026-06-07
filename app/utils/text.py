import re

_QUESTION_SUFFIX_RE = re.compile(r"\s*(นะครับ|นะคะ|ครับ|ค่ะ|คะ)\s*$")
_TRAILING_PUNCT_RE = re.compile(r"[\s?？!！.。…]+$")


def normalize_question(question: str) -> str:
    normalized = question.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = _TRAILING_PUNCT_RE.sub("", normalized)
    normalized = _QUESTION_SUFFIX_RE.sub("", normalized).strip()
    return normalized or question.strip()
