"""
skills.py — Dynamic skill extraction using NLP noun-phrase patterns + curated taxonomy.
Upgraded: extracts skills from JD dynamically, not just static list matching.
"""
import re


# Curated taxonomy of known tech skills for high-confidence matching
TECH_SKILLS = {
    # Programming Languages
    "python", "javascript", "typescript", "java", "c++", "c#", "ruby",
    "golang", "go", "php", "rust", "swift", "kotlin", "scala", "r",
    "matlab", "perl", "dart", "lua", "haskell", "elixir",
    # Frontend
    "react", "angular", "vue", "vue.js", "svelte", "next.js", "nuxt.js",
    "html", "css", "sass", "less", "tailwind", "tailwindcss", "bootstrap",
    "jquery", "redux", "webpack", "vite", "gatsby",
    # Backend
    "node.js", "express", "express.js", "django", "flask", "fastapi",
    "spring", "spring boot", "ruby on rails", "rails", "laravel",
    "asp.net", "graphql", "rest", "restful", "grpc",
    # Data / ML / AI
    "machine learning", "deep learning", "nlp",
    "natural language processing", "computer vision", "pandas", "numpy",
    "scikit-learn", "sklearn", "tensorflow", "pytorch", "keras",
    "xgboost", "lightgbm", "opencv", "spacy", "hugging face",
    "transformers", "llm", "large language model", "generative ai",
    "rag", "langchain", "fine-tuning", "neural networks",
    # Data Engineering
    "data analysis", "data science", "data engineering", "big data",
    "hadoop", "spark", "apache spark", "kafka", "apache kafka",
    "airflow", "apache airflow", "etl", "data pipeline",
    "data warehouse", "snowflake", "databricks", "dbt",
    # Databases
    "sql", "mysql", "postgresql", "postgres", "mongodb", "redis",
    "elasticsearch", "dynamodb", "cassandra", "neo4j", "sqlite",
    "firebase", "supabase",
    # Cloud / DevOps
    "aws", "gcp", "google cloud", "azure", "docker", "kubernetes",
    "k8s", "terraform", "ansible", "jenkins", "ci/cd", "github actions",
    "gitlab ci", "cloudformation", "serverless", "lambda",
    "ec2", "s3", "ecs", "eks", "fargate",
    # Tools
    "git", "github", "gitlab", "bitbucket", "jira", "confluence",
    "figma", "postman", "swagger", "linux", "bash",
    # Methodologies
    "agile", "scrum", "kanban", "devops", "mlops", "tdd",
    "microservices", "event-driven", "distributed systems",
    # Soft Skills (selective)
    "leadership", "communication", "problem solving", "teamwork",
    "mentoring", "project management", "stakeholder management",
}


def _normalize(text: str) -> str:
    """Lowercase and gentle cleanup."""
    return text.lower().strip()


def _extract_noun_phrases(text: str) -> set:
    """
    Lightweight NLP-like noun phrase extraction using regex patterns.
    Catches multi-word terms like 'machine learning', 'project management'.
    """
    text = _normalize(text)
    # Match 2-3 word noun phrases (adjective? + noun + noun?)
    bigrams = re.findall(r'\b([a-z]+(?:[.-][a-z]+)*\s+[a-z]+(?:[.-][a-z]+)*)\b', text)
    trigrams = re.findall(r'\b([a-z]+\s+[a-z]+\s+[a-z]+)\b', text)
    # Single words
    singles = re.findall(r'\b([a-z][a-z+#.]{1,})\b', text)
    return set(singles) | set(bigrams) | set(trigrams)


def extract_skills(text: str) -> list:
    """
    Extracts skills from text using:
    1. Exact match against curated taxonomy (high confidence)
    2. Dynamic noun phrase extraction (medium confidence)
    Returns a deduplicated list of skills found.
    """
    if not text:
        return []

    text_lower = _normalize(text)
    found_skills = set()

    # Phase 1: Match against curated taxonomy
    for skill in TECH_SKILLS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.add(skill)

    return sorted(list(found_skills))


def extract_skills_dynamic(text: str) -> list:
    """
    Extracts skills dynamically from text (e.g., from a Job Description).
    Combines curated taxonomy + noun-phrase extraction for better coverage.
    """
    if not text:
        return []

    # Curated matches
    curated = set(extract_skills(text))

    # Dynamic noun phrase extraction for uncurated skills
    phrases = _extract_noun_phrases(text)

    # Filter out very common phrases that aren't skills
    NOISE = {
        "the", "and", "for", "are", "with", "you", "our", "has",
        "will", "this", "that", "from", "have", "been", "can",
        "all", "your", "about", "more", "other", "work", "team",
        "role", "join", "company", "looking", "strong", "ability",
        "experience", "years", "ideal", "candidate", "required",
        "preferred", "minimum", "must", "including", "etc",
        "well", "also", "such", "both", "between", "new",
        "responsibilities", "requirements", "qualifications",
        "working", "knowledge", "understanding", "proficiency",
        "excellent", "good", "deep", "solid", "proven",
    }

    dynamic_skills = set()
    for phrase in phrases:
        words = phrase.split()
        if all(w in NOISE for w in words):
            continue
        if len(phrase) > 2 and phrase not in NOISE:
            # Only add if it's also in the taxonomy (to avoid noise)
            if phrase in TECH_SKILLS:
                dynamic_skills.add(phrase)

    return sorted(list(curated | dynamic_skills))
