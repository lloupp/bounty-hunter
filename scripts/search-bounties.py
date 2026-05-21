#!/usr/bin/env python3
"""
Bounty Hunter - Busca de bounties open-source
Procura issues remuneradas no GitHub via gh API.
Filtra por confiabilidade, competencia e valor.
"""

import subprocess
import re
import json
import os
import sys
from datetime import datetime

BH_DIR = os.path.expanduser("~/bounty-hunter")
RESULTS_DIR = os.path.join(BH_DIR, "results")

# --- Confiabilidade ---
# Repos com pagamento comprovado (empresa real ou historico de payouts)
TRUSTED_ORGS = {
    "archestra-ai",      # $5-$7.5K bounties, 3720 stars, active
    "coollabsio",        # Coolify - $50 bounties via Algora
    "openstreetmap-ng",  # Zaczero pays reliably, 18+ bounties paid
    "Expensify",
    "permitio",
}

# Repos suspeitos (valor alto sem historico, criados recentemente, possivel scam)
SUSPECT_REPOS = {
    "UnsafeLabs/Bounty-Hunters",        # scam: 0 PRs merged, requires Fortran/Cobol/MUMPS
    "SecureBananaLabs/bug-bounty",       # 100+ AI agent comments per issue, spam
    "Scottcjn/rustchain-bounties",       # joke bounties (Amiga/68K Mac), token $0.10
    "orchestration-agent/AgentOrchestration",
    "kolotikwoan/robot-001",             # spam/test repo
    "Sagargajare/probot-test-repo",      # test issue
    "alvaroechevarriacuesta/sync-test",  # test bounty notifications, not real
    "mitchm11/my-repo",                  # personal test repo
}

# Sinais de suspeita no titulo/labels
SUSPECT_SIGNALS = [
    "urgent", "immediate", "quick money", "easy $",
    "fortran", "cobol", "mumps", "prolog", "pl/i", "ada",
]


def run_gh_api(query, limit=30):
    """Roda gh api search/issues e retorna parsed JSON."""
    cmd = [
        "gh", "api", f"search/issues?q={query}&sort=updated&order=desc&per_page={limit}",
        "--jq", '.items[] | {repo: (.repository_url | split("/") | .[-2] + "/" + .[-1]), number, title: .title, url: .html_url, comments, labels: [.labels[].name], created: .created_at, updated: .updated_at}'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"  [warn] Search failed: {result.stderr[:100]}", file=sys.stderr)
        return []

    items = []
    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return items


def extract_bounty_value(labels, title=""):
    """Extrai valor monetario de labels como '$150', '$1.5k', etc."""
    # Check labels first (most reliable)
    for label in labels:
        m = re.match(r'\$([0-9]+(?:\.[0-9]+)?)\s*(k|K)?', label)
        if m:
            val = float(m.group(1))
            if m.group(2) and m.group(2).lower() == "k":
                val *= 1000
            return val
    # Fallback: check title
    m = re.search(r'\$\s*([0-9,]+)\s*(k|K)?', title)
    if m:
        val_str = m.group(1).replace(",", "")
        if val_str:
            val = float(val_str)
            if m.group(2) and m.group(2).lower() == "k":
                val *= 1000
            return val
    return None


def get_trust_level(repo, value, title, labels):
    """
    Classifica confiabilidade da bounty.
    VERDE = confiavel (pagamento provavel)
    AMARELO = cautela (precisa verificar)
    VERMELHO = suspeito (provavelmente nao paga ou e scam)
    """
    text = (title + " " + " ".join(labels)).lower()
    org = repo.split("/")[0] if "/" in repo else ""

    # Hard-coded suspeitos
    if repo in SUSPECT_REPOS:
        return "VERMELHO"

    # Hard-coded confiaveis
    if org in TRUSTED_ORGS or repo in TRUSTED_ORGS:
        return "VERDE"

    # Sinais de scam no titulo
    if any(sig in text for sig in SUSPECT_SIGNALS):
        return "VERMELHO"

    # Valor muito alto em repo desconhecido = cautela
    if value and value >= 1000:
        return "AMARELO"

    # Valor razoavel com label de bounty = provavelmente ok
    if value and value >= 1:
        return "VERDE"

    # Sem valor definido = cautela
    return "AMARELO"


def categorize_bounty(title, labels):
    """Categoriza o tipo de bounty."""
    text = (title + " " + " ".join(labels)).lower()
    if any(w in text for w in ["security", "vuln", "audit", "cve", "xss", "inject", "auth", "jwt", "hook", "destructive", "block"]):
        return "seguranca"
    if any(w in text for w in ["doc", "document", "readme", "tutorial", "guide", "content", "template"]):
        return "documentacao"
    if any(w in text for w in ["bug", "fix", "crash", "error", "broken", "prevent", "reject", "validate", "verify", "enforce"]):
        return "bugfix"
    if any(w in text for w in ["feature", "add", "implement", "support", "create", "enable", "convert"]):
        return "feature"
    if any(w in text for w in ["test", "coverage", "spec"]):
        return "teste"
    if any(w in text for w in ["typo", "refactor", "clean", "triage", "review"]):
        return "triage"
    return "outro"


def is_ai_friendly(labels):
    """Verifica se a bounty e amigavel para agentes AI."""
    return any(tag in " ".join(labels).lower() for tag in ["ai agent", "ai only", "ai friendly", "ai-friendly"])


def search_all_bounties():
    """Busca bounties de multiplas fontes via GitHub API."""
    queries = [
        # Algora bounties (most reliable)
        'commenter:algora-pbc[bot]+is:open+is:issue',
        # Direct $ labels
        'is:open+is:issue+label:"$10"+comments:0..10',
        'is:open+is:issue+label:"$20"+comments:0..10',
        'is:open+is:issue+label:"$30"+comments:0..10',
        'is:open+is:issue+label:"$50"+comments:0..10',
        'is:open+is:issue+label:"$75"+comments:0..10',
        'is:open+is:issue+label:"$100"+comments:0..10',
        'is:open+is:issue+label:"$150"+comments:0..10',
        # Generic bounty labels
        'is:open+is:issue+label:bounty+comments:0..5',
    ]

    all_results = []
    seen_urls = set()

    for i, query in enumerate(queries):
        source = "algora" if "algora" in query else "label"
        print(f"  [{i+1}/{len(queries)}] Searching: {query[:60]}...", file=sys.stderr)
        items = run_gh_api(query, limit=20)

        for item in items:
            url = item.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)

            title = item.get("title", "")
            labels = item.get("labels", [])
            repo = item.get("repo", "")
            comments = item.get("comments", 0)

            value = extract_bounty_value(labels, title)
            ai_friendly = is_ai_friendly(labels)
            category = categorize_bounty(title, labels)
            trust = get_trust_level(repo, value, title, labels)

            all_results.append({
                "title": title,
                "repo": repo,
                "url": url,
                "value": value,
                "category": category,
                "ai_friendly": ai_friendly,
                "labels": labels,
                "trust": trust,
                "comments": comments,
                "source": source,
            })

    return all_results


def display_bounties(bounties):
    """Exibe bounties agrupadas por confiabilidade, qualquer valor."""
    if not bounties:
        print("Nenhuma bounty encontrada.")
        return

    trust_icons = {
        "VERDE": "[OK] ",
        "AMARELO": "[???]",
        "VERMELHO": "[!!!]",
    }
    trust_order = {"VERDE": 0, "AMARELO": 1, "VERMELHO": 2}
    trust_sections = {
        "VERDE": "CONFIAVEIS — pagamento provavel",
        "AMARELO": "CAUTELA — verificar antes de trabalhar",
        "VERMELHO": "SUSPEITAS — NAO recomendadas (possivel scam)",
    }

    # Ordenar: VERDE primeiro (por valor desc), depois AMARELO, depois VERMELHO
    bounties.sort(key=lambda x: (
        trust_order.get(x["trust"], 1),
        -(x["value"] or 0)
    ))

    total = len(bounties)

    print(f"\n{'='*82}")
    print(f" BOUNTY HUNTER - {total} bounties encontradas")
    print(f" {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f" [OK]=confiavel [???]=cautela [!!!]=suspeito")
    print(f"{'='*82}")

    current_trust = None
    global_idx = 0

    for b in bounties:
        if b["trust"] != current_trust:
            current_trust = b["trust"]
            count = sum(1 for x in bounties if x["trust"] == current_trust)
            section = trust_sections.get(current_trust, "OUTRAS")
            separator = "=" if current_trust == "VERDE" else "-" if current_trust == "AMARELO" else "~"
            print(f"\n {separator*40}")
            print(f" {section} ({count})")
            print(f" {separator*40}")

        global_idx += 1
        value_str = f"${b['value']:,.0f}" if b['value'] else "$?"
        trust_icon = trust_icons.get(b["trust"], "[???]")
        ai_tag = " AI" if b["ai_friendly"] else "  "
        cat = b["category"].upper()[:12]
        comments = b.get("comments", "?")

        print(f" {global_idx:2d}. {trust_icon} {value_str:>8s} {cat:<13s}{ai_tag} {comments}c")
        print(f"     {b['title'][:74]}")
        print(f"     {b['repo']} → {b['url']}")
        print()

    # Resumo
    verde = sum(1 for b in bounties if b["trust"] == "VERDE")
    amarelo = sum(1 for b in bounties if b["trust"] == "AMARELO")
    vermelho = sum(1 for b in bounties if b["trust"] == "VERMELHO")
    potencial_verde = sum(b["value"] or 0 for b in bounties if b["trust"] == "VERDE")
    potencial_total = sum(b["value"] or 0 for b in bounties if b["value"])

    print(f" {'='*82}")
    print(f" RESUMO: {verde} confiaveis | {amarelo} cautela | {vermelho} suspeitas")
    print(f" POTENCIAL CONFiAVEL: ${potencial_verde:,.0f} | Total: ${potencial_total:,.0f}")
    print(f"{'='*82}\n")


def save_results(bounties):
    """Salva resultados em JSON."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    filepath = os.path.join(RESULTS_DIR, "latest.json")

    with open(filepath, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "count": len(bounties),
            "bounties": bounties,
        }, f, indent=2, ensure_ascii=False)
    print(f"Resultados salvos em {filepath}")


if __name__ == "__main__":
    print("Buscando bounties open-source...")
    bounties = search_all_bounties()
    display_bounties(bounties)
    save_results(bounties)
