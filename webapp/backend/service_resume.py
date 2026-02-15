"""Resume PDF parsing and keyword extraction using PyPDF2 + spaCy."""

import logging
from collections import Counter

logger = logging.getLogger(__name__)

# Predefined skill categories for matching
TECH_SKILLS = {
    "python", "sql", "r", "java", "javascript", "typescript", "c++", "scala",
    "tableau", "power bi", "excel", "alteryx", "looker", "qlik",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "spark",
    "aws", "azure", "gcp", "docker", "kubernetes", "git",
    "jira", "confluence", "figma", "miro",
}

DOMAIN_SKILLS = {
    "product analytics", "data analysis", "machine learning", "deep learning",
    "natural language processing", "nlp", "computer vision", "a/b testing",
    "user research", "kpi", "okr", "agile", "scrum", "kanban",
    "data-driven", "cross-functional", "go-to-market", "stakeholder management",
    "product management", "product strategy", "roadmap", "backlog",
    "genai", "generative ai", "llm", "large language model", "agentic",
    "artificial intelligence", "ai", "gpt",
}


def extract_text_from_pdf(pdf_path: str) -> str:
    from PyPDF2 import PdfReader
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def extract_keywords(text: str) -> list[dict]:
    """Extract keywords from resume text using spaCy NLP + pattern matching."""
    keywords = []
    text_lower = text.lower()

    # 1. Match known technical skills
    for skill in TECH_SKILLS:
        if skill.lower() in text_lower:
            keywords.append({"keyword": skill, "category": "boost", "source": "resume"})

    # 2. Match domain skills (multi-word)
    for skill in DOMAIN_SKILLS:
        if skill.lower() in text_lower:
            keywords.append({"keyword": skill, "category": "boost", "source": "resume"})

    # 3. Use spaCy for additional entity extraction
    try:
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found, using pattern matching only")
            return _dedupe_keywords(keywords)

        doc = nlp(text)

        # Extract organizations, skills from noun chunks
        noun_chunks = [chunk.text.strip() for chunk in doc.noun_chunks
                       if 2 <= len(chunk.text.strip()) <= 50]
        chunk_counts = Counter(noun_chunks)
        for chunk, count in chunk_counts.most_common(20):
            if count >= 2 and chunk.lower() not in {k["keyword"].lower() for k in keywords}:
                keywords.append({"keyword": chunk, "category": "boost", "source": "resume"})

    except ImportError:
        logger.warning("spaCy not installed, using pattern matching only")

    return _dedupe_keywords(keywords)


def _dedupe_keywords(keywords: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for kw in keywords:
        key = kw["keyword"].lower()
        if key not in seen:
            seen.add(key)
            result.append(kw)
    return result
