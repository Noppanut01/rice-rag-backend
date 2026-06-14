import re

_TRAILING_PUNCT_RE = re.compile(r"[\s?？!！.。…]+$")
_QUOTES_RE = re.compile(r'^["\'“”‘’«»]+|["\'“”‘’«»]+$')

_LEADING_FILLER_RE = re.compile(
    r"^(?:"
    r"อยากทราบว่า|อยากถามว่า|ขอถามว่า|ขอสอบถามว่า|"
    r"ช่วยบอกหน่อย|ช่วยอธิบายหน่อย|ช่วยแนะนำหน่อย|ช่วยตอบหน่อย|"
    r"สอบถามว่า|ถามว่า"
    r")\s*"
)

# ตัดเฉพาะคำลงท้ายสุภาพ/เติมเสียง — ไม่ตัด "ไหม"/"มั้ย" ล้วนๆ เพราะอาจเป็นส่วนสำคัญของคำถาม
_QUESTION_SUFFIX_RE = re.compile(
    r"\s*(?:"
    r"นะ(?:ครับ|คะ|จ้า|จ๊ะ|จ้ะ)?|"
    r"หน่อย(?:ครับ|ค่ะ|นะ)?|"
    r"ด้วย(?:ครับ|ค่ะ)?|"
    r"(?:ไหม|มั้ย|มั๊ย)(?:ครับ|คะ|ค่ะ)|"
    r"ได้(?:ไหม|มั้ย)(?:ครับ|คะ|ค่ะ)?|"
    r"ครับ(?:ผม)?|"
    r"ค่ะ|คะ|"
    r"จ้า|จ๊ะ|จ้ะ"
    r")\s*$"
)


def normalize_question(question: str) -> str:
    normalized = question.strip()
    normalized = normalized.lower()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = _QUOTES_RE.sub("", normalized)
    normalized = _TRAILING_PUNCT_RE.sub("", normalized)
    normalized = _LEADING_FILLER_RE.sub("", normalized).strip()

    for _ in range(3):
        stripped = _QUESTION_SUFFIX_RE.sub("", normalized).strip()
        if stripped == normalized:
            break
        normalized = stripped

    normalized = _TRAILING_PUNCT_RE.sub("", normalized).strip()
    return normalized or question.strip()
