# Provenance Guard — planning.md

## Architecture Narrative

A piece of text enters the system via `POST /submit`. It is passed simultaneously to two detection signals: an LLM-based semantic classifier (Groq) and a stylometric heuristic analyzer (pure Python). Each signal returns a score between 0 and 1, where 1 = strongly AI-like. The pipeline module combines these into a single confidence score using a weighted average. That score is mapped to one of three transparency label variants and an attribution result (`AI-generated`, `Human-written`, or `Uncertain`). The full decision — both signal scores, the combined score, the label, and a content preview — is written to the SQLite audit log. The structured JSON response is returned to the caller.

For appeals, a creator submits `POST /appeal` with their `content_id` and reasoning. The system updates the audit log entry's status to `under_review`, writes a new row to the appeals table, and returns a confirmation. No automated re-classification occurs.

---

## Architecture Diagram

SUBMISSION FLOW
===============

POST /submit (raw text)
        |
        v
+-------------------+       +------------------------+
|  LLM Signal       |       |  Stylometric Signal    |
|  (Groq)           |       |  (pure Python)         |
|  -> semantic score|       |  -> heuristic score    |
+-------------------+       +------------------------+
        |                           |
        +----------+----------------+
                   |
                   v
        +---------------------+
        |  Pipeline Combiner  |
        |  weighted average   |
        |  -> confidence score|
        +---------------------+
                   |
                   v
        +---------------------+
        |  Label Generator    |
        |  -> transparency    |
        |    label text       |
        +---------------------+
                   |
                   v
        +---------------------+
        |  Audit Log (SQLite) |
        |  -> write entry     |
        +---------------------+
                   |
                   v
        JSON response to caller


APPEAL FLOW
===========

POST /appeal (content_id + reasoning)
        |
        v
+-------------------------+
|  Look up content_id     |
|  in audit_log           |
+-------------------------+
        |
        v
+-------------------------+
|  Update status to       |
|  "under_review"         |
+-------------------------+
        |
        v
+-------------------------+
|  Write appeal row       |
|  to appeals table       |
+-------------------------+
        |
        v
JSON confirmation to caller

---

## Detection Signals

### Signal 1: LLM-Based Semantic Classification (Groq)

What it measures: Whether the text reads as AI-generated based on semantic coherence, phrasing patterns, structural predictability, and stylistic uniformity. Groq's llama-3.3-70b-versatile is prompted to assess the text and return a score from 0.0 (strongly human) to 1.0 (strongly AI).

Why it differs between human and AI writing: AI-generated text tends to be grammatically clean, well-organized, and stylistically consistent in ways that human writing rarely is. Humans make irregular word choices, shift tone, and produce uneven structure. The LLM can detect these patterns holistically.

Output format: Float between 0.0 and 1.0, parsed from a structured prompt response.

Blind spots: Will struggle with highly polished human writing (edited essays, professional authors) and with deliberately degraded AI output. Vulnerable to prompt injection if a user embeds adversarial instructions in the submitted text.

---

### Signal 2: Stylometric Heuristics (Pure Python)

What it measures: Statistical properties of the text that differ structurally between human and AI writing:
- Sentence length variance: AI text tends toward uniform sentence lengths; human writing is more irregular.
- Type-token ratio (TTR): Vocabulary diversity — AI text reuses common words more predictably.
- Punctuation density: Humans use punctuation (em dashes, ellipses, colons mid-sentence) more idiosyncratically.

Each sub-metric is normalized to a 0-1 range. Lower variance and lower TTR push the score toward 1.0 (AI-like).

Why it differs: AI models are trained to optimize for readability and coherence, which produces measurable statistical regularity. Human writing reflects cognitive variability — fatigue, emphasis, personality.

Output format: Float between 0.0 and 1.0.

Blind spots: Short texts (under ~100 words) produce unreliable heuristics — not enough data to compute meaningful variance. Also fails on deliberately stylized human writing (minimalist poetry, stream-of-consciousness prose) which may look statistically uniform.

---

## Confidence Scoring and Uncertainty Representation

Combining signals:

  confidence_score = (0.60 x llm_score) + (0.40 x stylometric_score)

LLM signal is weighted higher because it captures semantic and holistic properties that heuristics miss. Stylometric signal acts as a structural check.

Score interpretation:

  Score range   | Meaning                        | Label tier
  0.00 - 0.35   | Strongly human-like signals    | High-confidence human
  0.36 - 0.64   | Mixed or inconclusive signals  | Uncertain
  0.65 - 1.00   | Strongly AI-like signals       | High-confidence AI

False positive asymmetry: Misclassifying a human writer's work as AI is a worse outcome than missing an AI submission. The uncertain band (0.36-0.64) is intentionally wide to avoid false positives.

Validation approach: Test with known inputs — clearly AI-generated text (raw ChatGPT output), clearly human text (published literary excerpts), and edge cases (a simple human poem, a highly polished human essay). Scores should spread meaningfully across the three tiers.

---

## Transparency Label Variants

### High-confidence AI (score >= 0.65)

  Attribution Notice
  Our system found strong indicators that this content may have been AI-generated.
  This is based on an analysis of writing patterns and style — not a definitive
  judgment. If you created this work yourself, you can submit an appeal below.
  Confidence: High

### Uncertain (score 0.36-0.64)

  Attribution Notice
  Our system could not confidently determine whether this content was written by a
  person or generated by AI. The signals were mixed or inconclusive. No action has
  been taken. If you have concerns, you can submit an appeal.
  Confidence: Low

### High-confidence human (score <= 0.35)

  Attribution Notice
  Our system found no strong indicators of AI generation in this content.
  It appears consistent with human-written work.
  Confidence: High

---

## Appeals Workflow

Who can appeal: Any creator who submitted content and has the content_id returned by the API.

What they provide: Their content_id and a free-text explanation of why they believe the classification is incorrect.

What the system does on receipt:
1. Looks up the content_id in audit_log.
2. Updates the row's status field from "reviewed" to "under_review".
3. Inserts a new row into the appeals table with content_id, appealed_at timestamp, creator_reasoning, and status = under_review.
4. Returns a JSON confirmation with the updated status.

What a human reviewer sees: A query joining audit_log and appeals on content_id, showing the original classification, confidence score, both signal scores, and the creator's stated reasoning side by side.

Anticipated edge cases:
1. Appeal submitted for a non-existent content_id: System should return a 404 with a clear error — no partial writes.
2. A minimalist poem scored as AI-generated: Short, simple, rhythmic human writing will produce low sentence length variance and a low TTR — both stylometric markers of AI text. The LLM may also rate it highly AI-like due to its clean structure. This is a known false positive risk. The wide uncertain band partially mitigates it, but short creative work remains a documented limitation.
3. Duplicate appeal submissions: If a creator submits the same appeal twice, the system should not double-insert. Check for an existing open appeal on the same content_id before writing.

---

## AI Tool Plan

### M3 — Submission Endpoint + First Signal
Sections provided to AI: Detection Signals (Signal 1 only), Architecture Diagram, POST /submit contract
What to request: Flask app skeleton with POST /submit route + llm_signal.py function that calls Groq and returns a 0-1 score
Verification: Run the endpoint with 3 test inputs (clear AI text, clear human text, ambiguous text). Check that the LLM score varies meaningfully and that the JSON response structure matches the contract.

### M4 — Second Signal + Confidence Scoring
Sections provided to AI: Detection Signals (Signal 2), Confidence Scoring section, Architecture Diagram
What to request: stylometric.py function + pipeline.py combiner that applies the weighted average and returns score + attribution result
Verification: Test the same 3 inputs from M3. Confirm that combined scores differ from LLM-only scores and that the three label tiers are reachable.

### M5 — Production Layer
Sections provided to AI: Transparency Label Variants, Appeals Workflow, Architecture Diagram
What to request: Label generation logic in pipeline.py + POST /appeal route + rate limiting on /submit
Verification: Hit all three label tiers with test inputs. Submit an appeal and confirm status updates to under_review in the DB. Trigger rate limit and confirm 429 response.