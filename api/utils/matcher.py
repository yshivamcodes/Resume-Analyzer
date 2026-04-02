"""
matcher.py -- TF-IDF + Cosine Similarity engine for resume-to-JD matching.

NOTE: Raw cosine similarity between resumes and JDs is typically 10-40%
even for strong matches, because they are structurally different document
types (resume format vs JD format). We apply calibration to produce
scores that align with human expectations.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import math


def _preprocess_for_similarity(text: str) -> str:
    """
    Strip structural noise from text before computing similarity.
    Removes section headers, dates, formatting artifacts, etc.
    so TF-IDF focuses on actual content words.
    """
    text = text.lower()

    # Remove common resume structural words that add noise
    noise_words = [
        r'\b(summary|objective|experience|education|skills|projects|'
        r'certifications|achievements|awards|references|'
        r'responsibilities|requirements|qualifications|preferred|required|'
        r'looking for|we are|join our|ideal candidate|'
        r'jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|'
        r'present|current)\b',
    ]
    for pattern in noise_words:
        text = re.sub(pattern, '', text, flags=re.I)

    # Remove dates, phone numbers, emails, URLs
    text = re.sub(r'\d{4}', '', text)  # years
    text = re.sub(r'[\w.-]+@[\w.-]+', '', text)  # emails
    text = re.sub(r'https?://\S+', '', text)  # urls
    text = re.sub(r'\+?\d[\d\-\s]{8,}', '', text)  # phones

    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _calibrate_similarity(raw_score: float) -> float:
    """
    Calibrate raw cosine similarity to a human-expectation scale.

    Raw TF-IDF cosine similarity between resume and JD:
    - 0-10%  = No match → maps to 0-20%
    - 10-25% = Weak match → maps to 20-50%
    - 25-45% = Good match → maps to 50-80%
    - 45-60% = Strong match → maps to 80-95%
    - 60%+   = Near-perfect → maps to 95-100%

    Uses a sigmoid-like curve for smooth mapping.
    """
    if raw_score <= 0:
        return 0.0

    # Piecewise linear calibration
    breakpoints = [
        (0,  0),
        (8,  15),
        (15, 35),
        (25, 55),
        (35, 72),
        (45, 85),
        (55, 92),
        (65, 96),
        (80, 99),
        (100, 100),
    ]

    for i in range(1, len(breakpoints)):
        raw_lo, cal_lo = breakpoints[i - 1]
        raw_hi, cal_hi = breakpoints[i]
        if raw_score <= raw_hi:
            # Linear interpolation within this segment
            ratio = (raw_score - raw_lo) / (raw_hi - raw_lo)
            return round(cal_lo + ratio * (cal_hi - cal_lo), 1)

    return 100.0


def compute_semantic_similarity(resume_text: str, jd_text: str) -> float:
    """
    Computes calibrated cosine similarity between resume and job description
    using TF-IDF vectorization.

    Pre-processes text to remove structural noise, then calibrates the
    raw score to align with human expectations (a 35% raw TF-IDF
    cosine similarity = genuinely strong match for resume vs JD).

    Returns a calibrated score from 0 to 100.
    """
    if not resume_text.strip() or not jd_text.strip():
        return 0.0

    # Pre-process to remove structural noise
    clean_resume = _preprocess_for_similarity(resume_text)
    clean_jd = _preprocess_for_similarity(jd_text)

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=5000,
        ngram_range=(1, 2),   # unigrams + bigrams for richer matching
        sublinear_tf=True     # apply log normalization
    )

    try:
        tfidf_matrix = vectorizer.fit_transform([clean_resume, clean_jd])
        raw_similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        raw_percent = raw_similarity * 100

        # Apply calibration
        calibrated = _calibrate_similarity(raw_percent)
        return calibrated

    except Exception:
        return 0.0


def compute_keyword_match(resume_text: str, jd_text: str) -> float:
    """
    Computes keyword overlap between resume and JD.
    Extracts meaningful words (length > 2) removing stopwords,
    calculates what percentage of JD keywords appear in the resume.
    Returns a score from 0 to 100.
    """
    STOPWORDS = {
        "the", "and", "for", "are", "but", "not", "you", "all", "can",
        "had", "her", "was", "one", "our", "out", "has", "have", "been",
        "will", "with", "that", "this", "from", "they", "were", "what",
        "when", "who", "how", "which", "their", "about", "would", "there",
        "could", "other", "into", "more", "some", "than", "them", "very",
        "just", "also", "should", "must", "may", "each", "where", "most",
        "such", "both", "between", "after", "before", "over", "under",
        "work", "working", "experience", "ability", "team", "strong",
        "including", "using", "years", "role", "responsibilities",
        "requirements", "preferred", "required", "knowledge", "skills",
        "looking", "join", "company", "well", "etc", "use", "used"
    }

    def extract_keywords(text):
        words = re.findall(r'[a-z][a-z+#.]+', text.lower())
        return set(w for w in words if len(w) > 2 and w not in STOPWORDS)

    resume_kw = extract_keywords(resume_text)
    jd_kw = extract_keywords(jd_text)

    if not jd_kw:
        return 0.0

    overlap = resume_kw & jd_kw
    score = (len(overlap) / len(jd_kw)) * 100
    return round(min(score, 100), 1)
