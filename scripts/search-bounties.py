#!/usr/bin/env python3
"""
Bounty Hunter - Busca de bounties open-source
Procura issues remuneradas no GitHub via gh CLI.
Filtra por confiabilidade — qualquer valor, mas so as legit.
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
TRUSTED_REPOS = {
    "Expensify/App",
    "spaceandtimefdn/sxt-proof-of-sql",
    "hnpy/hn",
    "claude-builders-bounty/claude-builders-bounty",
}

# Repos suspeitos (valor alto sem historico, criados recentemente, possivel scam)
SUSPECT_REPOS = {
 "orchestration-agent/AgentOrchestration",
 "SecureBananaLabs/bug-bounty",
}

# Sinais de suspeita no titulo/labels
SUSPECT_SIGNALS = [
    "urgent", "immediate", "quick money", "easy $",
]


def run_gh_search(query, limit=30):
    """Roda gh search issues e retorna parsed via texto."""
    cmd = ["gh", "search", "issues", "--limit", str(limit), "--sort", "updated", query]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        return []

    lines = result.stdout.strip().split("\n")
    items = []
    for line in lines:
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 4:
            repo = parts[0].strip()
            url = f"https://github.com/{repo}/issues/{parts[1].strip()}"
            items.append({
                "repo": repo,
                "title": parts[3].strip() if len(parts) > 3 else "",
                "labels": parts[4].strip() if len(parts) > 4 else "",
                "url": url,
            })
    return items


def extract_bounty_value(text):
    """Extrai valor monetario de texto."""
    m = re.search(r'\$\s*([\d,]+)\s*(k|K)?', text)
    if m:
        val_str = m.group(1).replace(",", "")
        if not val_str:
            return None
        value = float(val_str)
        if m.group(2) and m.group(2).lower() == "k":
            value *= 1000
        return value

    m = re.search(r'bounty:\s*(\d+)\s*usd', text, re.I)
    if m:
        return float(m.group(1))

    return None


def get_trust_level(repo, value, title, labels):
    """
    Classifica confiabilidade da bounty.
    VERDE  = confiavel (pagamento provavel)
    AMARELO = cautela (precisa verificar)
    VERMELHO = suspeito (provavelmente nao paga ou e scam)
    """
    text = (title + " " + labels).lower()

    # Hard-coded suspeitos
    if repo in SUSPECT_REPOS:
        return "VERMELHO"

    # Hard-coded confiaveis
    if repo in TRUSTED_REPOS:
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
    text = (title + " " + labels).lower()
    if any(w in text for w in ["security", "vuln", "audit", "cve", "xss", "inject", "auth", "jwt", "hook", "destructive", "block"]):
        return "seguranca"
    if any(w in text for w in ["doc", "document", "readme", "tutorial", "guide", "content", "template", "claudemd"]):
        return "documentacao"
    if any(w in text for w in ["bug", "fix", "crash", "error", "broken", "prevent", "reject", "validate", "verify", "enforce"]):
        return "bugfix"
    if any(w in text for w in ["feature", "add", "implement", "support", "create"]):
        return "feature"
    if any(w in text for w in ["test", "coverage", "spec"]):
        return "teste"
    if any(w in text for w in ["typo", "refactor", "clean", "triage", "review"]):
        return "triage"
    return "outro"


def is_ai_friendly(labels):
    """Verifica se a bounty e amigavel para agentes AI."""
    return any(tag in labels.lower() for tag in ["ai agent", "ai only", "ai friendly", "ai-friendly"])


def search_all_bounties():
    """Busca bounties de multiplas fontes."""
    queries = [
        "label:bounty",
        "label:💎-Bounty",
        "label:reward",
    ]

    all_results = []
    seen_urls = set()

    for query in queries:
        items = run_gh_search(query, limit=30)
        for item in items:
            url = item.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)

            title = item.get("title", "")
            labels = item.get("labels", "")
            repo = item.get("repo", "")

            combined = title + " " + labels
            value = extract_bounty_value(combined)
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
            })

    return all_results


def display_bounties(bounties):
    """Exibe bounties agrupadas por confiabilidade, qualquer valor."""
    if not bounties:
        print("Nenhuma bounty encontrada.")
        return

    trust_icons = {
        "VERDE":    "[OK] ",
        "AMARELO":  "[???]",
        "VERMELHO": "[!!!]",
    }
    trust_order = {"VERDE": 0, "AMARELO": 1, "VERMELHO": 2}
    trust_sections = {
        "VERDE":    "CONFIAVEIS — pagamento provavel",
        "AMARELO":  "CAUTELA — verificar antes de trabalhar",
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
    print(f" [OK]=confiavel  [???]=cautela  [!!!]=suspeito")
    print(f"{'='*82}")

    current_trust = None
    global_idx = 0

    for b in bounties:
        # Imprimir header da secao quando mudar a confiabilidade
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
        ai_tag = " AI" if b["ai_friendly"] else "   "
        cat = b["category"].upper()[:12]

        print(f"  {global_idx:2d}. {trust_icon} {value_str:>8s}  {cat:<13s}{ai_tag}")
        print(f"      {b['title'][:74]}")
        print(f"      {b['repo']}")
        print(f"      {b['url']}")
        print()

    # Resumo
    verde = sum(1 for b in bounties if b["trust"] == "VERDE")
    amarelo = sum(1 for b in bounties if b["trust"] == "AMARELO")
    vermelho = sum(1 for b in bounties if b["trust"] == "VERMELHO")
    potencial_verde = sum(b["value"] or 0 for b in bounties if b["trust"] == "VERDE")
    potencial_total = sum(b["value"] or 0 for b in bounties if b["value"])

    print(f" {'='*82}")
    print(f" RESUMO: {verde} confiaveis | {amarelo} cautela | {vermelho} suspeitas")
    print(f" POTENCIAL CONFIavel: ${potencial_verde:,.0f} | Total: ${potencial_total:,.0f}")
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
