"""
scoring.py -- Combined scoring engine.

Score Formula:
  Overall = 0.40 * semantic_similarity + 0.35 * keyword_match + 0.25 * skill_overlap

The semantic similarity is now calibrated (see matcher.py) so scores
are meaningful and aligned with human expectations.
"""
from .matcher import compute_semantic_similarity, compute_keyword_match
import re


def compute_skill_overlap_score(matched_skills: list, jd_skills: list) -> float:
    """
    Computes skill overlap as a percentage.
    Returns 0-100.
    """
    if not jd_skills:
        return 0.0
    overlap = len(matched_skills) / len(jd_skills) * 100
    return round(min(overlap, 100), 1)


def compute_final_score(
    resume_text: str,
    jd_text: str,
    matched_skills: list,
    jd_skills: list
) -> dict:
    """
    Computes the final composite score with full breakdown.
    """
    semantic = compute_semantic_similarity(resume_text, jd_text)
    keywords = compute_keyword_match(resume_text, jd_text)
    skills = compute_skill_overlap_score(matched_skills, jd_skills)

    # Weighted formula (adjusted: less weight on semantic, more on direct evidence)
    overall = round(
        0.40 * semantic +
        0.35 * keywords +
        0.25 * skills,
        1
    )

    return {
        "overall": min(overall, 100),
        "semantic": semantic,
        "keywords": keywords,
        "skills": skills
    }


def generate_explanations(
    score: dict,
    matched_skills: list,
    missing_skills: list,
    resume_text: str,
    jd_text: str
) -> list:
    """
    Generates human-readable explanations for WHY the score is what it is.
    Thresholds are calibrated for the calibrated similarity scores.
    """
    explanations = []
    overall = score["overall"]

    # Overall assessment
    if overall >= 75:
        explanations.append({
            "type": "positive",
            "title": "Strong Match",
            "detail": f"Your resume is a strong match at {overall}%. You're well-aligned with this role."
        })
    elif overall >= 55:
        explanations.append({
            "type": "positive",
            "title": "Good Match",
            "detail": f"Your resume scores {overall}%. You have solid alignment with some room for improvement."
        })
    elif overall >= 35:
        explanations.append({
            "type": "warning",
            "title": "Moderate Match",
            "detail": f"Your resume scores {overall}%. There are clear areas where optimization would help."
        })
    else:
        explanations.append({
            "type": "critical",
            "title": "Weak Match",
            "detail": f"Your resume scores {overall}%. Significant gaps exist between your profile and this role."
        })

    # Semantic analysis (calibrated: 70+ is strong)
    if score["semantic"] >= 70:
        explanations.append({
            "type": "positive",
            "title": "Strong Content Relevance",
            "detail": "Your resume's language and context strongly mirrors the job description. Great thematic alignment."
        })
    elif score["semantic"] >= 45:
        explanations.append({
            "type": "positive",
            "title": "Good Content Alignment",
            "detail": "Your resume shows decent contextual overlap with the job description. Minor refinements in phrasing could push this higher."
        })
    elif score["semantic"] >= 25:
        explanations.append({
            "type": "warning",
            "title": "Moderate Content Alignment",
            "detail": "Your resume partially aligns with the JD's context. Consider restructuring your summary and experience to mirror the job description's language."
        })
    else:
        explanations.append({
            "type": "critical",
            "title": "Low Content Relevance",
            "detail": "The overall language of your resume diverges significantly from the job description. Consider restructuring your experience to mirror the JD's terminology."
        })

    # Keyword analysis
    if score["keywords"] >= 70:
        explanations.append({
            "type": "positive",
            "title": "Strong Keyword Coverage",
            "detail": "Most important keywords from the job description are present in your resume. ATS systems should parse your application well."
        })
    elif score["keywords"] >= 45:
        explanations.append({
            "type": "warning",
            "title": "Keyword Gaps Detected",
            "detail": "Some relevant keywords are missing. Adding them naturally into your experience bullets will improve your ATS pass rate."
        })
    else:
        explanations.append({
            "type": "critical",
            "title": "Missing Critical Keywords",
            "detail": "Many important keywords from the job description are absent from your resume. ATS systems will likely filter your application."
        })

    # Skills analysis
    if missing_skills:
        severity = "critical" if len(missing_skills) > 5 else "warning"
        top_missing = missing_skills[:5]
        explanations.append({
            "type": severity,
            "title": f"{len(missing_skills)} Skills Not Found",
            "detail": f"The following skills from the JD were not found in your resume: {', '.join(top_missing)}{'...' if len(missing_skills) > 5 else ''}. Consider adding relevant experience or certifications."
        })

    if matched_skills:
        detail_skills = ', '.join(matched_skills[:8])
        if len(matched_skills) > 8:
            detail_skills += '...'
        explanations.append({
            "type": "positive",
            "title": f"{len(matched_skills)} Skills Matched",
            "detail": f"Your resume demonstrates: {detail_skills}."
        })

    # Action verbs check
    exp_keywords = ["managed", "led", "developed", "built", "designed",
                    "implemented", "optimized", "increased", "reduced", "delivered"]
    exp_count = sum(1 for kw in exp_keywords if kw in resume_text.lower())
    if exp_count < 3:
        explanations.append({
            "type": "warning",
            "title": "Weak Action Verbs",
            "detail": "Your resume uses few strong action verbs (managed, led, built, optimized, etc.). ATS and recruiters look for impact-driven language."
        })

    # Quantification check
    numbers = re.findall(r'\d+%|\$\d+|\d+\+', resume_text)
    if len(numbers) < 2:
        explanations.append({
            "type": "warning",
            "title": "Lack of Quantified Achievements",
            "detail": "Your resume has very few quantified metrics (e.g., 'increased revenue by 30%'). Adding measurable impact dramatically improves perception."
        })

    return explanations
