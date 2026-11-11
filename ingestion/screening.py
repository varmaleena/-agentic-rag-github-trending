import re
import unicodedata

# Limit this heuristic to direct attempts to alter the model's instructions.
INJECTION_PATTERNS = re.compile(
    r"\b(?:ignore|disregard|override|forget)\b.{0,80}\b(?:previous|prior|system|developer|above)\b"
    r".{0,40}\b(?:instructions?|prompts?|messages?)\b"
    r"|\b(?:reveal|print|exfiltrate)\b.{0,60}\b(?:system prompt|api keys?|credentials?)\b",
    re.IGNORECASE | re.DOTALL,
)


def contains_prompt_injection(text):
    normalized = unicodedata.normalize("NFKC", text)
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Cf")
    return bool(INJECTION_PATTERNS.search(normalized))
