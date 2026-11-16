
# ProofPath AI
# Evidence Intelligence Engine V2

import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


ROLE_REQUIREMENTS = {
    "Data Analyst": [
        "Python", "SQL", "Excel", "Statistics",
        "Pandas", "Data Visualization", "Power BI"
    ],
    "Software Developer": [
        "Python", "Java", "C++", "SQL",
        "Data Structures", "Algorithms", "Git"
    ],
    "AI/ML Engineer": [
        "Python", "Machine Learning", "Deep Learning",
        "Statistics", "NumPy", "Pandas", "TensorFlow"
    ]
}


SKILL_DESCRIPTIONS = {
    "Python": "Python programming functions modules scripts classes",
    "SQL": "SQL database queries select insert update joins tables",
    "Excel": "Excel spreadsheets formulas workbook openpyxl",
    "Statistics": "statistics probability mean median variance scipy stats",
    "Pandas": "pandas dataframe read_csv data cleaning manipulation",
    "Data Visualization": "matplotlib seaborn plotly charts graphs visualization",
    "Power BI": "Power BI business intelligence dashboards reports DAX",
    "Java": "Java programming classes methods object oriented",
    "C++": "C++ programming classes pointers algorithms",
    "Data Structures": "arrays linked lists stacks queues trees hash maps",
    "Algorithms": "sorting searching recursion algorithms complexity",
    "Git": "git version control commits branches repository",
    "Machine Learning": "machine learning model training prediction scikit learn",
    "Deep Learning": "deep learning neural networks backpropagation",
    "NumPy": "numpy arrays numerical computing linear algebra",
    "TensorFlow": "tensorflow keras neural network model training"
}


# Evidence patterns: stronger signals than generic keyword mentions
CODE_PATTERNS = {
    "Python": [
        r"^\s*(import\s+\w+|from\s+\w+\s+import)",
        r"^\s*def\s+\w+\s*\("
    ],
    "Pandas": [
        r"^\s*import\s+pandas\b",
        r"^\s*from\s+pandas\b",
        r"\bpd\.(DataFrame|Series|read_csv|read_excel|concat|merge)\b"
    ],
    "SQL": [
        r"\bSELECT\b.+\bFROM\b",
        r"\bINSERT\s+INTO\b",
        r"\bCREATE\s+TABLE\b",
        r"\bJOIN\b.+\bON\b"
    ],
    "Excel": [
        r"\bopenpyxl\b",
        r"\bread_excel\s*\(",
        r"\bto_excel\s*\("
    ],
    "Statistics": [
        r"\bscipy\.stats\b",
        r"\bstatsmodels\b",
        r"\b(mean|median|variance|standard_deviation)\s*\("
    ],
    "Data Visualization": [
        r"\bmatplotlib\b",
        r"\bseaborn\b",
        r"\bplotly\b",
        r"\bplt\.(plot|bar|hist|scatter)\s*\("
    ],
    "Power BI": [
        r"\.pbix\b",
        r"\bDAX\b"
    ],
    "NumPy": [
        r"^\s*import\s+numpy\b",
        r"^\s*from\s+numpy\b",
        r"\bnp\.(array|mean|sum|reshape|dot)\s*\("
    ],
    "Machine Learning": [
        r"\bsklearn\b",
        r"\btrain_test_split\b",
        r"\bfit_predict\s*\(",
        r"\bmodel\.fit\s*\("
    ],
    "Deep Learning": [
        r"\btensorflow\b",
        r"\btorch\.nn\b",
        r"\bkeras\b"
    ],
    "TensorFlow": [
        r"\btensorflow\b",
        r"\btf\.keras\b"
    ],
    "Java": [
        r"\bpublic\s+static\s+void\s+main\b",
        r"\bSystem\.out\.println\b"
    ],
    "C++": [
        r"#include\s*<iostream>",
        r"\bstd::cout\b"
    ],
    "Git": [
        r"\.gitignore\b"
    ],
    "Algorithms": [
        r"\b(binary_search|quick_sort|merge_sort)\b"
    ],
    "Data Structures": [
        r"\b(class\s+Node|LinkedList|Stack|Queue|HashMap)\b"
    ]
}


def normalize_text(text):
    return str(text or "").strip().lower()


def contains_skill(text, skill):
    pattern = (
        r"(?<!\w)" + re.escape(skill.lower()) + r"(?!\w)"
    )
    return bool(re.search(pattern, normalize_text(text)))


def analyze_skills(
    claimed_skills,
    evidence,
    verified_skills=None,
    role="Data Analyst"
):
    if role not in ROLE_REQUIREMENTS:
        raise ValueError("Invalid job role")

    claimed = {
        item.strip().lower()
        for item in claimed_skills.split(",")
        if item.strip()
    }

    verified = {
        str(item).lower()
        for item in (verified_skills or [])
    }

    evidence_text = normalize_text(evidence)
    results = []

    for skill in ROLE_REQUIREMENTS[role]:
        is_claimed = skill.lower() in claimed
        has_evidence = contains_skill(evidence_text, skill)

        if skill.lower() in verified:
            status = "Verified Evidence"
        elif is_claimed and has_evidence:
            status = "Evidence Submitted"
        elif is_claimed:
            status = "Self-Reported"
        else:
            status = "Missing"

        results.append({
            "skill": skill,
            "status": status
        })

    return results


def detect_repository_signals(inspected_files):
    results = []
    seen = set()

    for file_data in inspected_files or []:
        file_path = file_data.get("file", "")
        content = file_data.get("content_preview", "")

        for skill, patterns in CODE_PATTERNS.items():
            for pattern in patterns:

                match = re.search(
                    pattern,
                    content,
                    re.IGNORECASE | re.MULTILINE
                )

                if match:
                    key = (skill, file_path)

                    if key not in seen:
                        seen.add(key)

                        line_start = content.rfind(
                            "\n", 0, match.start()
                        ) + 1

                        line_end = content.find(
                            "\n", match.end()
                        )

                        if line_end == -1:
                            line_end = len(content)

                        snippet = content[
                            line_start:line_end
                        ].strip()[:250]

                        results.append({
                            "skill": skill,
                            "file": file_path,
                            "snippet": snippet,
                            "status": "Repository-backed Signal"
                        })

                    break

    return results


def calculate_ai_relevance(evidence, role="Data Analyst"):
    if role not in ROLE_REQUIREMENTS:
        raise ValueError("Invalid job role")

    if not evidence.strip():
        return []

    skills = ROLE_REQUIREMENTS[role]

    descriptions = [
        SKILL_DESCRIPTIONS.get(skill, skill)
        for skill in skills
    ]

    try:
        documents = [evidence] + descriptions

        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2)
        )

        matrix = vectorizer.fit_transform(documents)

        scores = cosine_similarity(
            matrix[0:1],
            matrix[1:]
        )[0]

        results = []

        for skill, score in zip(skills, scores):
            results.append({
                "skill": skill,
                "score": round(float(score) * 100, 1),
                "method": "TF-IDF + Cosine Similarity"
            })

        return sorted(
            results,
            key=lambda item: item["score"],
            reverse=True
        )

    except ValueError:
        return [
            {
                "skill": skill,
                "score": 0.0,
                "method": "TF-IDF + Cosine Similarity"
            }
            for skill in skills
        ]
