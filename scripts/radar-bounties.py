#!/usr/bin/env python3
"""Multi-platform bounty radar.

Collects actionable bounty opportunities from GitHub/Algora-style issues and
prints a prioritized shortlist. The script is intentionally conservative:
platforms with no stable public API are represented by useful search URLs rather
than brittle scraping.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from urllib.parse import quote_plus

# Raiz do projeto: derivada da localizacao deste arquivo (pai de scripts/),
# com override opcional via variavel de ambiente BOUNTY_HUNTER_DIR.
BH_DIR = os.environ.get("BOUNTY_HUNTER_DIR") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
RESULTS_DIR = os.path.join(BH_DIR, "results")
OUT_PATH = os.path.join(RESULTS_DIR, "radar-latest.json")

SUSPECT_REPOS = {
    "UnsafeLabs/Bounty-Hunters",
    "SecureBananaLabs/bug-bounty",
    "Scottcjn/rustchain-bounties",
    "orchestration-agent/AgentOrchestration",
    "kolotikwoan/robot-001",
    "Sagargajare/probot-test-repo",
    "alvaroechevarriacuesta/sync-test",
    "mitchm11/my-repo",
}

TRUSTED_ORGS = {
    "algora-io",
    "archestra-ai",
    "coollabsio",
    "openstreetmap-ng",
    "Expensify",
    "permitio",
    "tscircuit",
    "jhipster",
}

CATEGORY_BOOST = {
    "bugfix": 35,
    "security": 30,
    "docs": 25,
    "test": 20,
    "feature": 15,
    "other": 0,
}


def gh_api_search(query: str, per_page: int = 30) -> list[dict]:
    cmd = [
        "gh",
        "api",
        f"search/issues?q={query}&sort=updated&order=desc&per_page={per_page}",
        "--jq",
        '.items[] | {platform:"GitHub/Algora", repo:(.repository_url | split("/") | .[-2] + "/" + .[-1]), number, title, url:.html_url, comments, labels:[.labels[].name], created:.created_at, updated:.updated_at, body:(.body // "")}',
    ]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
    except subprocess.TimeoutExpired:
        return []
    if p.returncode != 0:
        return []
    out = []
    for line in p.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def extract_value(text: str, labels: list[str]) -> float | None:
    candidates = list(labels) + [text]
    for s in candidates:
        m = re.search(r"\$\s*([0-9]+(?:[.,][0-9]+)?)(\s*[kK])?", s)
        if not m:
            continue
        val = float(m.group(1).replace(",", "."))
        if m.group(2):
            val *= 1000
        return val
    return None


def categorize(title: str, labels: list[str]) -> str:
    t = (title + " " + " ".join(labels)).lower()
    if any(x in t for x in ["security", "vuln", "xss", "auth", "audit", "cve"]):
        return "security"
    if any(x in t for x in ["bug", "fix", "crash", "broken", "error", "validate"]):
        return "bugfix"
    if any(x in t for x in ["doc", "tutorial", "guide", "readme", "template", "blog"]):
        return "docs"
    if any(x in t for x in ["test", "coverage", "spec"]):
        return "test"
    if any(x in t for x in ["feature", "add", "implement", "support", "integrate"]):
        return "feature"
    return "other"


def trust(repo: str, title: str, labels: list[str], value: float | None) -> str:
    org = repo.split("/", 1)[0]
    text = (title + " " + " ".join(labels)).lower()
    if repo in SUSPECT_REPOS:
        return "red"
    if org in TRUSTED_ORGS:
        return "green"
    if any(x in text for x in ["urgent", "quick money", "fortran", "cobol", "mumps"]):
        return "red"
    if value and value >= 1000:
        return "yellow"
    if value:
        return "green"
    return "yellow"


def score(item: dict) -> float:
    val = item.get("value") or 0
    comments_penalty = min(item.get("comments") or 0, 80) * 1.5
    trust_key = str(item.get("trust") or "")
    category_key = str(item.get("category") or "other")
    trust_boost = {"green": 60, "yellow": 15, "red": -500}.get(trust_key, 0)
    return (min(val, 500) * 0.8) + CATEGORY_BOOST.get(category_key, 0) + trust_boost - comments_penalty


def collect_github_algora() -> list[dict]:
    queries = [
        # Algora-style issues are currently the most actionable for PR bounties.
        'commenter:algora-pbc[bot]+is:open+is:issue',
        'is:open+is:issue+label:"💎 Bounty"',
        'is:open+is:issue+label:"$50"',
        'is:open+is:issue+label:"$75"',
        'is:open+is:issue+label:"$100"',
        'is:open+is:issue+label:"$150"',
        'is:open+is:issue+label:"$200"',
        'is:open+is:issue+label:"$$ bug-bounty $$"',
        'is:open+is:issue+label:bounty',
    ]
    seen: set[str] = set()
    results: list[dict] = []
    for q in queries:
        for it in gh_api_search(q, per_page=25):
            if it["url"] in seen:
                continue
            seen.add(it["url"])
            labels = it.get("labels") or []
            val = extract_value(it.get("title", ""), labels)
            cat = categorize(it.get("title", ""), labels)
            tr = trust(it.get("repo", ""), it.get("title", ""), labels, val)
            row = {
                "platform": it["platform"],
                "repo": it["repo"],
                "title": it["title"],
                "url": it["url"],
                "value": val,
                "category": cat,
                "trust": tr,
                "comments": it.get("comments") or 0,
                "labels": labels,
                "updated": it.get("updated"),
            }
            row["score"] = round(score(row), 2)
            results.append(row)
    return results


def discovery_links() -> list[dict]:
    """Useful platform searches that require browser/login/manual filtering."""
    return [
        {
            "platform": "Algora",
            "url": "https://console.algora.io/bounties",
            "note": "Primary OSS bounty feed; GitHub-native; verify issue comments before claiming.",
        },
        {
            "platform": "OnlyDust",
            "url": "https://app.onlydust.com/projects",
            "note": "Web3/OSS rewards; choose projects with good-first-issue and active maintainers.",
        },
        {
            "platform": "Superteam Earn",
            "url": "https://earn.superteam.fun/listings/?type=bounty",
            "note": "Solana/ecosystem bounties; includes code, docs, content, design.",
        },
        {
            "platform": "Gitcoin",
            "url": "https://app.gitcoin.co/explorer",
            "note": "Grants/hackathons/bounties; requires filtering for concrete engineering tasks.",
        },
        {
            "platform": "DoraHacks",
            "url": "https://dorahacks.io/hackathon",
            "note": "Hackathons and bounty campaigns, often larger submissions.",
        },
        {
            "platform": "Polar",
            "url": "https://polar.sh/discover",
            "note": "OSS funding/backers; useful for finding funded repos, less direct bounty flow.",
        },
        {
            "platform": "Code4rena",
            "url": "https://code4rena.com/audits",
            "note": "Smart-contract audit contests; high upside, requires security expertise.",
        },
        {
            "platform": "Sherlock",
            "url": "https://audits.sherlock.xyz/contests",
            "note": "Web3 audit contests; findings-based payout.",
        },
        {
            "platform": "Cantina",
            "url": "https://cantina.xyz/competitions",
            "note": "Security competitions and bounties; findings-based payout.",
        },
    ]


def main() -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    rows = collect_github_algora()
    rows.sort(key=lambda x: x["score"], reverse=True)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "count": len(rows),
        "top": rows[:30],
        "all": rows,
        "discovery_links": discovery_links(),
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Radar bounty — {len(rows)} oportunidades coletadas")
    print(f"Salvo em: {OUT_PATH}\n")
    print("Top oportunidades GitHub/Algora:")
    for i, b in enumerate(rows[:15], 1):
        val = f"${b['value']:.0f}" if b.get("value") else "$?"
        print(f"{i:2}. [{b['trust']}] {val:>5} score={b['score']:>6} {b['category']:<8} {b['comments']:>3}c  {b['repo']}")
        print(f"    {b['title']}")
        print(f"    {b['url']}")
    print("\nDiscovery links:")
    for d in discovery_links():
        print(f"- {d['platform']}: {d['url']} — {d['note']}")


if __name__ == "__main__":
    main()
