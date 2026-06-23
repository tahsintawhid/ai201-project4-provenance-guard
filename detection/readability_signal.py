import re


def get_readability_score(text: str) -> dict:
    sentences = _split_sentences(text)
    words = _tokenize(text)
    syllables = sum(_count_syllables(w) for w in words)

    if len(sentences) < 1 or len(words) < 10:
        return {
            "score": 0.5,
            "reasoning": "Text too short for reliable readability analysis.",
            "metrics": {
                "flesch_reading_ease": None,
                "avg_words_per_sentence": None,
                "avg_syllables_per_word": None
            }
        }

    avg_words_per_sentence = len(words) / len(sentences)
    avg_syllables_per_word = syllables / len(words)

    # Flesch Reading Ease: higher = easier to read
    # AI text tends to score in the 40-60 range (formal but readable)
    # Human casual text scores 60-80+, human academic text scores 20-40
    flesch = 206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)
    flesch = max(0.0, min(100.0, flesch))

    # AI text clusters in the mid-range (40-65): not too simple, not too complex
    # We score distance from the AI-typical range as human-like
    # Mid-range (40-65) -> AI-like (toward 1.0)
    # Very high (>65, casual) or very low (<40, dense academic) -> human-like (toward 0.0)
    if 40.0 <= flesch <= 65.0:
        # Linearly map 40-65 to 1.0-0.5 (center of range = most AI-like)
        midpoint = 52.5
        distance_from_mid = abs(flesch - midpoint)
        score = 1.0 - (distance_from_mid / 12.5) * 0.5
    elif flesch > 65.0:
        # Very easy/casual -> human-like
        score = max(0.0, 0.5 - ((flesch - 65.0) / 35.0) * 0.5)
    else:
        # Very dense/complex -> human-like (academic writing)
        score = max(0.0, 0.5 - ((40.0 - flesch) / 40.0) * 0.5)

    score = round(max(0.0, min(1.0, score)), 4)

    return {
        "score": score,
        "reasoning": f"Flesch={round(flesch,1)}, avg_words/sent={round(avg_words_per_sentence,1)}, avg_syll/word={round(avg_syllables_per_word,2)}",
        "metrics": {
            "flesch_reading_ease": round(flesch, 2),
            "avg_words_per_sentence": round(avg_words_per_sentence, 2),
            "avg_syllables_per_word": round(avg_syllables_per_word, 2)
        }
    }


def _split_sentences(text: str) -> list:
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 0]


def _tokenize(text: str) -> list:
    return re.findall(r'\b[a-zA-Z]+\b', text.lower())


def _count_syllables(word: str) -> int:
    word = word.lower()
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


if __name__ == "__main__":
    test_inputs = [
        ("Clearly AI", "Artificial intelligence represents a transformative paradigm shift in modern society. It is important to note that while the benefits of AI are numerous, it is equally essential to consider the ethical implications. Furthermore, stakeholders across various sectors must collaborate to ensure responsible deployment."),
        ("Clearly human", "ok so i finally tried that new ramen place downtown and honestly? underwhelming. the broth was fine but they put WAY too much sodium in it and i was thirsty for like three hours after. my friend got the spicy version and said it was better. probably wont go back unless someone drags me there"),
        ("Borderline formal", "The relationship between monetary policy and asset price inflation has been extensively studied in the literature. Central banks face a fundamental tension between their mandate for price stability and the unintended consequences of prolonged low interest rates on equity and real estate valuations."),
        ("Borderline edited AI", "Ive been thinking a lot about remote work lately. There are genuine tradeoffs — flexibility and no commute on one side, isolation and blurred work-life boundaries on the other. Studies show productivity varies widely by individual and role type.")
    ]

    for label, text in test_inputs:
        print(f"\n--- {label} ---")
        result = get_readability_score(text)
        print(f"Score: {result['score']}")
        print(f"Reasoning: {result['reasoning']}")
