import requests
import json
import os

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}

# A manually curated spread of 15-30 active public repos, mixing languages/domains
# so you're not just sampling one project's commit-message style. Swap these for
# whatever you like — the only requirement is "active" (recent commits) and "public".
REPOS = [
    "psf/requests", "pallets/flask", "fastapi/fastapi", "django/django",
    "expressjs/express", "facebook/react", "vuejs/vue", "sveltejs/svelte",
    "rails/rails", "laravel/laravel", "golang/go", "rust-lang/rust",
    # add more up to 15-30 total
]

def fetch_commits(owner, repo, per_page=30):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    resp = requests.get(url, headers=HEADERS, params={"per_page": per_page})
    resp.raise_for_status()
    return [c["commit"]["message"] for c in resp.json()]

def fetch_pr_bodies(owner, repo, per_page=30):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    resp = requests.get(url, headers=HEADERS, params={"state": "all", "per_page": per_page})
    resp.raise_for_status()
    return [pr["body"] for pr in resp.json() if pr["body"]]

def main():
    all_texts = []
    for repo_full in REPOS:
        owner, repo = repo_full.split("/")
        print(f"Fetching {repo_full}...")
        try:
            for msg in fetch_commits(owner, repo):
                all_texts.append({"source": f"{repo_full}:commit", "text": msg})
            for body in fetch_pr_bodies(owner, repo):
                all_texts.append({"source": f"{repo_full}:pr", "text": body})
        except requests.HTTPError as e:
            print(f"  skipped ({e})")

    with open("raw_samples.json", "w", encoding="utf-8") as f:
        json.dump(all_texts, f, indent=2)
    print(f"Collected {len(all_texts)} text samples -> raw_samples.json")

if __name__ == "__main__":
    main()