"""
ai_module.py -- AI-powered suggestions and bullet rewriting.
Uses OpenAI if API key is available, otherwise falls back to intelligent rule-based generation.
"""
import os
import re
import random


def _get_openai_client():
    """Returns OpenAI client if API key is set, else None."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except Exception:
        return None


def generate_suggestions(
    resume_text: str,
    jd_text: str,
    missing_skills: list
) -> list:
    """
    Generates improvement suggestions.
    Attempts OpenAI first, falls back to rule-based if unavailable.
    """
    client = _get_openai_client()

    if client:
        return _ai_suggestions(client, resume_text, jd_text, missing_skills)
    else:
        return _rule_based_suggestions(resume_text, jd_text, missing_skills)


def _ai_suggestions(client, resume_text: str, jd_text: str, missing_skills: list) -> list:
    """Generate suggestions using OpenAI."""
    try:
        missing_str = ", ".join(missing_skills[:10]) if missing_skills else "None identified"

        prompt = f"""You are an expert ATS resume consultant. Analyze this resume against the job description and provide actionable improvement suggestions.

JOB DESCRIPTION:
{jd_text[:2000]}

RESUME (Extracted Text):
{resume_text[:3000]}

MISSING SKILLS: {missing_str}

Provide exactly 5 specific, actionable suggestions to improve this resume for this job. 
Each suggestion should be a JSON object with "title" and "detail" keys.
Return ONLY a JSON array, no other text.
Example: [{{"title": "Add Missing Skills", "detail": "Include TensorFlow experience..."}}]"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )

        import json
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = re.sub(r'^```(?:json)?\n?', '', content)
            content = re.sub(r'\n?```$', '', content)
        suggestions = json.loads(content)
        return suggestions

    except Exception as e:
        print(f"OpenAI suggestion generation failed: {e}")
        return _rule_based_suggestions("", "", missing_skills)


def _rule_based_suggestions(
    resume_text: str,
    jd_text: str,
    missing_skills: list
) -> list:
    """Fallback: generate rule-based suggestions without LLM."""
    suggestions = []

    if missing_skills:
        top = missing_skills[:5]
        suggestions.append({
            "title": "Add Missing Technical Skills",
            "detail": f"Your resume is missing these key skills from the job description: {', '.join(top)}. Add relevant projects, certifications, or coursework that demonstrate these competencies."
        })

    strong_verbs = ["led", "managed", "developed", "architected", "designed",
                    "implemented", "optimized", "delivered", "scaled", "automated"]
    used_verbs = [v for v in strong_verbs if v in resume_text.lower()]
    if len(used_verbs) < 3:
        suggestions.append({
            "title": "Strengthen Action Verbs",
            "detail": "Use more impactful action verbs to start your bullet points: Led, Architected, Optimized, Automated, Scaled, Delivered. Avoid passive language like 'responsible for' or 'worked on'."
        })

    numbers = re.findall(r'\d+%|\$[\d,]+|\d+\+|\d+x', resume_text)
    if len(numbers) < 3:
        suggestions.append({
            "title": "Quantify Your Impact",
            "detail": "Add measurable achievements: 'Reduced latency by 40%', 'Managed team of 8 engineers', 'Processed 1M+ records daily'. Numbers make your resume stand out to both ATS and humans."
        })

    suggestions.append({
        "title": "Optimize for ATS Parsing",
        "detail": "Ensure your resume uses standard section headers (Experience, Education, Skills), avoids tables/columns that confuse parsers, and includes keywords naturally within context rather than keyword-stuffing."
    })

    suggestions.append({
        "title": "Tailor Your Summary Section",
        "detail": "Write a 2-3 line professional summary at the top that directly mirrors the job title and top 3 requirements from the job description. This dramatically improves first-impression relevance."
    })

    suggestions.append({
        "title": "Restructure Your Skills Section",
        "detail": "Group skills by category (Languages, Frameworks, Cloud, Tools) to improve readability. List the most relevant skills first, matching the order they appear in the job description."
    })

    return suggestions[:5]


# ==================== REWRITE ENGINE ====================

def rewrite_bullet_points(text: str, jd_text: str = "") -> str:
    """
    Rewrites resume bullet points to be more professional, impactful,
    and tailored to the job description.
    Uses OpenAI if available, otherwise applies intelligent rule-based improvements.
    """
    client = _get_openai_client()

    if client:
        return _ai_rewrite(client, text, jd_text)
    else:
        return _rule_based_rewrite(text, jd_text)


def _ai_rewrite(client, text: str, jd_text: str = "") -> str:
    """Rewrite using OpenAI."""
    try:
        jd_context = ""
        if jd_text:
            jd_context = f"\n\nJOB DESCRIPTION CONTEXT:\n{jd_text[:1500]}\n\nTailor the rewrite to align with this job description's requirements and keywords."

        prompt = f"""You are an expert resume writer. Rewrite the following resume text to be more professional, impactful, and ATS-friendly.

Rules:
- Start each bullet with a strong action verb
- Include quantifiable metrics where possible (estimate if needed)
- Keep the same general meaning but make it more compelling
- Make it concise and professional
- Use past tense for past roles
- Each bullet should demonstrate impact, not just responsibility{jd_context}

Original text:
{text}

Rewritten version:"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI rewrite failed: {e}")
        return _rule_based_rewrite(text, jd_text)


def _rule_based_rewrite(text: str, jd_text: str = "") -> str:
    """
    Intelligent rule-based bullet point rewriter.
    Applies multiple transformation passes to genuinely improve content.
    """
    # Extract JD keywords for tailoring
    jd_keywords = _extract_jd_keywords(jd_text) if jd_text else set()

    # Step 1: Join continuation lines (lines that start lowercase or
    # don't start with a bullet/header are continuations of the previous line)
    raw_lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    merged_lines = []
    for line in raw_lines:
        clean = re.sub(r'^[\u2022\-\*\u2013\u2014\>]+\s*', '', line).strip()
        if not clean:
            continue
        # If line starts lowercase and we have a previous line, merge
        if (merged_lines
            and clean[0].islower()
            and not _is_section_header(clean)
            and not _is_meta_line(clean)):
            merged_lines[-1] = merged_lines[-1].rstrip('.') + ' ' + clean
        else:
            merged_lines.append(clean)

    # Step 2: Process each merged line
    improved = []
    for line in merged_lines:
        if not line:
            continue

        # Detect section headers
        if _is_section_header(line):
            improved.append(f"\n{line.upper()}")
            continue

        # Detect contact info / meta lines - keep as-is
        if _is_meta_line(line):
            improved.append(line)
            continue

        # Apply the transformation pipeline
        rewritten = _transform_bullet(line, jd_keywords)
        improved.append(rewritten)

    return "\n".join(improved).strip()


def _is_section_header(line: str) -> bool:
    """Detect if a line is a section header (Education, Experience, etc.)."""
    headers = [
        "summary", "objective", "experience", "education", "skills",
        "certifications", "projects", "achievements", "awards",
        "publications", "interests", "references", "work experience",
        "professional experience", "technical skills", "core competencies"
    ]
    clean = line.lower().strip().rstrip(':')
    return clean in headers or (len(line.split()) <= 3 and line.istitle() and not any(c.isdigit() for c in line))


def _is_meta_line(line: str) -> bool:
    """Detect contact info, dates, university names, etc. that shouldn't be rewritten."""
    # Contains email
    if re.search(r'[\w.-]+@[\w.-]+', line):
        return True
    # Contains phone number
    if re.search(r'\+?\d[\d\-\s]{8,}', line):
        return True
    # Contains URL
    if re.search(r'https?://|www\.|github\.com|linkedin\.com', line, re.I):
        return True
    # Date range patterns (Aug 2024 - Present, 2020-2023)
    if re.search(r'\b\d{4}\s*[\-\u2013]\s*(\d{4}|present|current)\b', line, re.I):
        return True
    # Very short lines that are likely names/titles
    if len(line.split()) <= 2 and not any(v in line.lower() for v in ["built", "developed", "created", "managed", "led"]):
        return True
    return False


def _transform_bullet(line: str, jd_keywords: set) -> str:
    """Apply the full transformation pipeline to a single bullet point."""

    result = line

    # Pass 1: Replace weak opening phrases with strong action verbs
    result = _replace_weak_starts(result)

    # Pass 2: Convert passive voice to active
    result = _fix_passive_voice(result)

    # Pass 3: Enhance with professional phrasing
    result = _enhance_phrasing(result)

    # Pass 4: Add quantification hints where missing
    result = _add_quantification(result)

    # Pass 5: Inject relevant JD keywords naturally
    if jd_keywords:
        result = _inject_jd_keywords(result, jd_keywords)

    # Pass 6: Ensure starts with strong action verb
    result = _ensure_action_verb_start(result)

    # Final cleanup
    result = result.strip()
    if result and result[0].islower():
        result = result[0].upper() + result[1:]

    # Add bullet
    if not result.startswith(("- ", "* ")):
        result = "- " + result

    # Ensure ends with period
    if result and result[-1] not in '.!':
        result += "."

    return result


# ==================== TRANSFORMATION PASSES ====================

WEAK_STARTS = {
    "responsible for": "Spearheaded",
    "worked on": "Developed and delivered",
    "helped with": "Contributed to the development of",
    "helped": "Facilitated",
    "tasked with": "Executed",
    "was part of": "Collaborated with cross-functional teams on",
    "assisted in": "Supported and enhanced",
    "involved in": "Drove key initiatives in",
    "did": "Delivered",
    "made": "Engineered",
    "handled": "Managed and streamlined",
    "got": "Achieved",
    "used": "Leveraged",
    "using": "utilizing",
    "worked with": "Collaborated with stakeholders on",
    "created": "Designed and built",
    "built": "Architected and implemented",
    "wrote": "Authored",
    "fixed": "Resolved",
    "tested": "Validated and tested",
    "learned": "Acquired expertise in",
    "studied": "Conducted in-depth analysis of",
    "participated in": "Actively contributed to",
    "contributed to": "Played a key role in",
    "looking for": "Seeking opportunities in",
    "seeking": "Pursuing advanced opportunities in",
    "proficient in": "Demonstrated proficiency in",
    "experience in": "Proven track record in",
    "knowledge of": "Deep understanding of",
    "familiar with": "Working knowledge of",
}


def _replace_weak_starts(line: str) -> str:
    """Replace weak opening phrases with strong action verbs."""
    line_lower = line.lower()
    for weak, strong in WEAK_STARTS.items():
        if line_lower.startswith(weak):
            return strong + " " + line[len(weak):].strip()
    return line


PASSIVE_PATTERNS = [
    (r'\bwas\s+(\w+ed)\b', lambda m: m.group(1).capitalize()),
    (r'\bwere\s+(\w+ed)\b', lambda m: m.group(1).capitalize()),
    (r'\bhas been\s+(\w+ed)\b', lambda m: m.group(1).capitalize()),
    (r'\bhave been\s+(\w+ed)\b', lambda m: m.group(1).capitalize()),
]


def _fix_passive_voice(line: str) -> str:
    """Convert passive constructions to active voice."""
    for pattern, replacement in PASSIVE_PATTERNS:
        if re.search(pattern, line, re.I):
            line = re.sub(pattern, replacement, line, count=1, flags=re.I)
            break
    return line


PHRASING_UPGRADES = [
    (r'\bvery good\b', 'exceptional'),
    (r'\bgood at\b', 'skilled in'),
    (r'\bin charge of\b', 'leading'),
    (r'\ba lot of\b', 'extensive'),
    (r'\btried to\b', 'endeavored to'),
    (r'\bset up\b', 'established'),
    (r'\bput together\b', 'assembled'),
    (r'\bfigured out\b', 'resolved'),
    (r'\bcame up with\b', 'devised'),
    (r'\bsped up\b', 'accelerated'),
    (r'\bcut down\b', 'reduced'),
    (r'\bteam of\b', 'cross-functional team of'),
    (r'\bworking on\b', 'developing'),
    (r'\bresponsible for\b', 'accountable for'),
    (r'\bto improve\b', 'to optimize'),
    (r'\bto fix\b', 'to resolve'),
    (r'\bto make\b', 'to engineer'),
    (r'\bweb app\b', 'web application'),
    (r'\bML\b', 'machine learning'),
    (r'\bAI\b', 'artificial intelligence'),
]


def _enhance_phrasing(line: str) -> str:
    """Upgrade informal or weak phrasing to professional language."""
    for pattern, replacement in PHRASING_UPGRADES:
        line = re.sub(pattern, replacement, line, flags=re.I)
    return line


QUANTIFICATION_HINTS = [
    (r'\b(developed|built|created|designed)\b.*\b(application|system|platform|tool|model|pipeline)\b',
     lambda m: m.group(0) + ", improving efficiency by an estimated 25%"),
    (r'\b(reduced|decreased|minimized)\b.*\b(time|cost|error|latency|bugs)\b',
     None),  # Already quantified-ish, skip
    (r'\b(increased|improved|enhanced|boosted|grew)\b.*\b(performance|accuracy|revenue|traffic|engagement)\b',
     None),  # Already quantified-ish, skip
]


def _add_quantification(line: str) -> str:
    """Add quantification hints where the line lacks numbers."""
    # Only add if line has no numbers already
    if re.search(r'\d+', line):
        return line

    # Only add to lines that describe achievements/projects
    action_verbs = ["developed", "built", "created", "designed", "implemented",
                    "deployed", "launched", "architected", "engineered", "automated"]
    line_lower = line.lower()

    for verb in action_verbs:
        if verb in line_lower:
            # Check if it's about a project/system/app
            if any(obj in line_lower for obj in ["application", "system", "model", "pipeline",
                                                  "platform", "tool", "website", "dashboard",
                                                  "api", "service", "chatbot", "prediction"]):
                # Add a contextual metric
                metrics = [
                    "resulting in measurable performance gains",
                    "serving end-to-end production workloads",
                    "demonstrating strong technical execution",
                    "following industry best practices and standards",
                ]
                return line.rstrip('.') + ", " + random.choice(metrics)
            break

    return line


def _inject_jd_keywords(line: str, jd_keywords: set) -> str:
    """
    Naturally inject a relevant JD keyword into the bullet,
    but only when there's a strong contextual match (2+ context words).
    """
    line_lower = line.lower()

    # Tight context mapping — requires stronger relevance
    tech_context_words = {
        "python": ["python", "script", "program", "automat"],
        "machine learning": ["model", "predict", "train", "algorithm"],
        "deep learning": ["neural", "cnn", "rnn", "lstm"],
        "nlp": ["text", "language", "sentiment", "chatbot", "nlp"],
        "docker": ["container", "deploy", "docker"],
        "kubernetes": ["orchestrat", "container", "k8s"],
        "aws": ["cloud", "s3", "ec2", "lambda", "hosted"],
        "fastapi": ["api", "endpoint", "rest", "fastapi"],
        "tensorflow": ["tensorflow", "neural network", "deep learning"],
        "pytorch": ["pytorch", "neural network", "deep learning"],
        "pandas": ["dataframe", "pandas", "csv", "clean"],
        "scikit-learn": ["classif", "regress", "sklearn", "scikit"],
        "ci/cd": ["pipeline", "automat", "jenkins", "github actions"],
    }

    # Varied phrasing templates
    phrasing = [
        "utilizing {kw}",
        "with {kw} integration",
        "applying {kw} best practices",
    ]

    for keyword in jd_keywords:
        kw_lower = keyword.lower()
        if kw_lower in line_lower:
            continue  # Already present

        contexts = tech_context_words.get(kw_lower, [])
        # Require at least 2 context word matches for strong relevance
        match_count = sum(1 for ctx in contexts if ctx in line_lower)
        if match_count >= 2:
            template = random.choice(phrasing)
            line = line.rstrip('.') + ", " + template.format(kw=keyword)
            break  # Only inject one keyword per line

    return line


# Strong action verbs to prepend when a line doesn't start with one
ACTION_VERBS = [
    "Developed", "Engineered", "Implemented", "Designed", "Built",
    "Optimized", "Delivered", "Architected", "Led", "Executed",
    "Streamlined", "Automated", "Deployed", "Spearheaded", "Orchestrated"
]


def _ensure_action_verb_start(line: str) -> str:
    """
    Ensure the line starts with a strong action verb.
    If it starts with a noun or weak word, prepend an appropriate verb.
    """
    strong_verbs = {
        "developed", "engineered", "implemented", "designed", "built",
        "optimized", "delivered", "architected", "led", "executed",
        "streamlined", "automated", "deployed", "spearheaded", "orchestrated",
        "managed", "created", "launched", "established", "achieved",
        "resolved", "authored", "facilitated", "collaborated", "contributed",
        "drove", "accelerated", "reduced", "increased", "improved",
        "enhanced", "integrated", "migrated", "refactored", "scaled",
        "configured", "analyzed", "researched", "evaluated", "trained",
        "mentored", "coordinated", "supervised", "negotiated", "presented",
        "demonstrated", "leveraged", "utilized", "pioneered", "transformed",
        "validated", "tested", "supported", "acquired", "pursued",
        "played", "conducted", "sought", "seeking",
    }

    first_word = line.split()[0].lower().rstrip(',.:;') if line.split() else ""

    if first_word in strong_verbs:
        return line  # Already starts with action verb

    # Check if it's a gerund (ending in -ing) - these are ok but could be better
    if first_word.endswith('ing') and len(first_word) > 4:
        return line

    # If starts with a noun/adjective describing a project, prepend a verb
    project_starters = ["motivated", "proficient", "experienced", "skilled",
                        "dedicated", "passionate", "enthusiastic", "detail",
                        "results", "self", "highly", "strong", "excellent"]
    if first_word in project_starters:
        return line  # Summary-style lines, keep as-is

    # For lines that describe a thing (like "Air Quality Prediction system")
    # Prepend a contextual verb
    line_lower = line.lower()
    if any(kw in line_lower for kw in ["model", "system", "application", "tool", "project"]):
        return "Developed " + line[0].lower() + line[1:]
    if any(kw in line_lower for kw in ["data", "analysis", "research"]):
        return "Conducted " + line[0].lower() + line[1:]
    if any(kw in line_lower for kw in ["team", "group", "collaboration"]):
        return "Led " + line[0].lower() + line[1:]

    return line


def _extract_jd_keywords(jd_text: str) -> set:
    """Extract important keywords from the job description for tailoring."""
    if not jd_text:
        return set()

    from .skills import TECH_SKILLS

    jd_lower = jd_text.lower()
    found = set()
    for skill in TECH_SKILLS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, jd_lower):
            found.add(skill)

    return found
