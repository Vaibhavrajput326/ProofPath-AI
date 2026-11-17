
# ProofPath AI
# Main Flask Application - Version 4
# GitHub Analysis + AI/ML Skill Intelligence

from flask import Flask, render_template, request
from engine import (
    analyze_skills,
    ROLE_REQUIREMENTS,
    detect_repository_signals,
    calculate_ai_relevance
)

import requests
import base64
import re
import os

app = Flask(__name__)


def fetch_github_evidence(url):

    match = re.match(
        r"https?://github\.com/([^/]+)/([^/]+)/?$",
        url.strip().removesuffix(".git").rstrip("/")
    )

    if not match:
        raise ValueError(
            "Please enter a valid public GitHub repository URL."
        )

    owner, repo = match.groups()

    headers = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "ProofPath-AI",
    "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN', '')}"
}

    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    response = requests.get(
        api_url,
        headers=headers,
        timeout=15
    )

    if response.status_code == 404:
        raise ValueError(
            "Repository not found or not publicly accessible."
        )

    response.raise_for_status()
    repo_data = response.json()

    if repo_data.get("private"):
        raise ValueError("Only public repositories are supported.")

    # Detect programming languages
    languages_response = requests.get(
        api_url + "/languages",
        headers=headers,
        timeout=15
    )
    languages_response.raise_for_status()
    languages = languages_response.json()

    # Fetch repository file tree
    branch = repo_data.get("default_branch", "main")

    tree_response = requests.get(
        f"{api_url}/git/trees/{branch}?recursive=1",
        headers=headers,
        timeout=20
    )
    tree_response.raise_for_status()

    tree_data = tree_response.json()

    allowed_extensions = (
        ".py", ".js", ".ts", ".java",
        ".cpp", ".c", ".sql", ".ipynb"
    )

    source_files = []

    for item in tree_data.get("tree", []):

        path = item.get("path", "")

        if (
            item.get("type") == "blob"
            and path.lower().endswith(allowed_extensions)
            and len(source_files) < 8
        ):
            source_files.append(path)

    # Fetch selected source files
    inspected_files = []

    for path in source_files:

        try:
            file_url = (
                f"https://raw.githubusercontent.com/"
                f"{owner}/{repo}/{branch}/{path}"
            )

            file_response = requests.get(
                file_url,
                headers={"User-Agent": "ProofPath-AI"},
                timeout=10
            )

            if file_response.status_code == 200:

                content = file_response.text

                inspected_files.append({
                    "file": path,
                    "content_preview": content[:3000]
                })

        except requests.RequestException:
            continue

    return {
        "repository": repo_data.get("full_name", repo),
        "description": repo_data.get("description") or "",
        "languages": list(languages.keys()),
        "source_files": source_files,
        "inspected_files": inspected_files,
        "file_note": (
            "File listing truncated."
            if tree_data.get("truncated")
            else "File listing retrieved successfully."
        )
    }


@app.route("/", methods=["GET", "POST"])
def home():

    analysis = None
    error = None
    github_message = None
    github_data = None
    repository_signals = []
    ai_relevance = []

    if request.method == "POST":

        skills = request.form.get("skills", "").strip()
        evidence = request.form.get("evidence", "").strip()
        role = request.form.get("role", "").strip()
        github_url = request.form.get("github_url", "").strip()

        if not skills or not evidence or not role:

            error = "Please complete all fields."

        else:

            
            try:

                # 1. CORE ANALYSIS - Always runs independently
                analysis = analyze_skills(
                    claimed_skills=skills,
                    evidence=evidence,
                    verified_skills=[],
                    role=role
                )

                # 2. AI RELEVANCE - Always runs independently
                ai_relevance = calculate_ai_relevance(
                    evidence=evidence,
                    role=role
                )

                # 3. OPTIONAL GITHUB ANALYSIS
                if github_url:

                    try:
                        github_data = fetch_github_evidence(
                            github_url
                        )

                        repository_signals = detect_repository_signals(
                            github_data["inspected_files"]
                        )

                        github_message = (
                            "GitHub repository analyzed successfully."
                        )

                    except Exception as exc:

                        print("GITHUB ANALYSIS ERROR:", repr(exc))

                        github_data = None
                        repository_signals = []

                        github_message = (
                            f"GitHub analysis unavailable: {exc}. "
                            "Core skill analysis completed successfully."
                        )


            except Exception as exc:

                print("CORE ANALYSIS ERROR:", repr(exc))
                analysis = None
                ai_relevance = []
                error = f"Core analysis failed: {exc}"

    return render_template(
        "index.html",
        roles=list(ROLE_REQUIREMENTS.keys()),
        analysis=analysis,
        error=error,
        github_message=github_message,
        github_data=github_data,
        repository_signals=repository_signals,
        ai_relevance=ai_relevance
    )


if __name__ == "__main__":
    app.run(debug=False)