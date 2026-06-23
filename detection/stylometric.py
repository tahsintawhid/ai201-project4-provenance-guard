import re
import math


def get_stylometric_score(text: str) -> dict:
    sentences = _split_sentences(text)
    words = _tokenize(text)

    if len(sentences) < 2 or len(words) < 20:
        return {
            "score": 0.5,
            "reasoning": "Text too short for reliable stylometric analysis.",
            "metrics": {
                "sentence_length_variance": None,
                "type_token_ratio": None,
                "punctuation_density": None
            }
        }

    slv_score = _sentence_length_variance_score(sentences)
    ttr_score = _type_token_ratio_score(words)
    punct_score = _punctuation_density_score(text, words)

    combined = (0.40 * slv_score) + (0.35 * ttr_score) + (0.25 * punct_score)
    combined = max(0.0, min(1.0, combined))

    return {
        "score": round(combined, 4),
        "reasoning": f"SLV={round(slv_score,3)}, TTR={round(ttr_score,3)}, PUNCT={round(punct_score,3)}",
        "metrics": {
            "sentence_length_variance": round(slv_score, 4),
            "type_token_ratio": round(ttr_score, 4),
            "punctuation_density": round(punct_score, 4)
        }
    }


def _split_sentences(text: str) -> list:
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 0]


def _tokenize(text: str) -> list:
    return re.findall(r'\b[a-zA-Z]+\b', text.lower())


def _sentence_length_variance_score(sentences: list) -> float:
    lengths = [len(s.split()) for s in sentences]
    if len(lengths) < 2:
        return 0.5
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    # High variance = human-like (toward 0), low variance = AI-like (toward 1)
    normalized = 1.0 - min(variance / 40.0, 1.0)
    return normalized


def _type_token_ratio_score(words: list) -> float:
    if not words:
        return 0.5
    ttr = len(set(words)) / len(words)
    # High TTR = diverse vocab = human-like (toward 0)
    score = 1.0 - ((ttr - 0.3) / 0.6)
    return max(0.0, min(1.0, score))


def _punctuation_density_score(text: str, words: list) -> float:
    if not words:
        return 0.5
    # Count all punctuation characters
    punct_chars = re.findall(r'[^\w\s]', text)
    density = len(punct_chars) / len(words)
    # Higher punctuation density = more human-like (toward 0)
    # Normalize: density > 0.2 is very punctuation-rich (human), < 0.05 is sparse (AI)
    score = 1.0 - min((density - 0.05) / 0.15, 1.0)
    return max(0.0, min(1.0, score))


if __name__ == "__main__":
    test_inputs = [
        ("Clearly AI", "Artificial intelligence represents a transformative paradigm shift in modern society. It is important to note that while the benefits of AI are numerous, it is equally essential to consider the ethical implications. Furthermore, stakeholders across various sectors must collaborate to ensure responsible deployment."),
        ("Clearly human", "ok so i finally tried that new ramen place downtown and honestly? underwhelming. the broth was fine but they put WAY too much sodium in it and i was thirsty for like three hours after. my friend got the spicy version and said it was better. probably wont go back unless someone drags me there"),
        ("Borderline formal", "The relationship between monetary policy and asset price inflation has been extensively studied in the literature. Central banks face a fundamental tension between their mandate for price stability and the unintended consequences of prolonged low interest rates on equity and real estate valuations."),
        ("Borderline edited AI", "Ive been thinking a lot about remote work lately. There are genuine tradeoffs — flexibility and no commute on one side, isolation and blurred work-life boundaries on the other. Studies show productivity varies widely by individual and role type.")
    ]

    for label, text in test_inputs:
        print(f"\n--- {label} ---")
        result = get_stylometric_score(text)
        print(f"Score: {result['score']}")
        print(f"Metrics: {result['metrics']}")
