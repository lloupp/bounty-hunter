#!/usr/bin/env python3
"""
Bounty Hunter - Verificacao de PRs
Cruza os repos trabalhados (logs/hunt.log) com os PRs reais no GitHub.
PRs merged sao registrados automaticamente em earnings.log (alimentando
o aprendizado de confiabilidade do search-bounties.py); PRs ainda
abertos sao listados para acompanhamento.
"""

import json
import os
import subprocess
import sys

BH_DIR = os.path.expanduser("~/bounty-hunter")
LOG_DIR = os.path.join(BH_DIR, "logs")


def load_hunt_log():
    """Ultimo estado conhecido de cada (repo, titulo) trabalhado, ignorando NOOPs."""
    path = os.path.join(LOG_DIR, "hunt.log")
    entries = {}
    if not os.path.exists(path):
        return entries
    with open(path) as f:
        for line in f:
            parts = [p.strip() for p in line.strip().split("|")]
            if len(parts) < 6:
                continue
            ts, mode, num, repo, title, value = parts[:6]
            if mode.endswith("-NOOP"):
                continue
            entries[(repo, title)] = {"ts": ts, "mode": mode, "value": value}
    return entries


def load_paid_keys():
    """(repo, titulo) ja registrados como pagos, para nao duplicar earnings.log."""
    path = os.path.join(LOG_DIR, "earnings.log")
    paid = set()
    if not os.path.exists(path):
        return paid
    with open(path) as f:
        for line in f:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4 and parts[1] == "PAGO":
                paid.add((parts[2], parts[3]))
    return paid


def gh_pr_list(repo):
    """PRs do usuario autenticado naquele repo (abertos, merged ou fechados)."""
    cmd = [
        "gh", "pr", "list", "--repo", repo, "--author", "@me", "--state", "all",
        "--json", "url,title,state,mergedAt,createdAt",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        print("[erro] 'gh' CLI nao encontrado. Instale: https://cli.github.com/", file=sys.stderr)
        sys.exit(1)
    if result.returncode != 0:
        print(f"  [warn] Nao foi possivel listar PRs de {repo}: {result.stderr.strip()[:200]}", file=sys.stderr)
        return []
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return []


def match_pr(repo, pr_title, entries):
    """Casa um PR com a bounty correspondente pelo titulo (match aproximado)."""
    pr_title_lower = pr_title.lower()
    for (r, title), info in entries.items():
        if r != repo:
            continue
        title_lower = title.lower()
        if title_lower in pr_title_lower or pr_title_lower in title_lower:
            return title, info
    return None, None


def main():
    entries = load_hunt_log()
    if not entries:
        print("Nenhum trabalho registrado em hunt.log ainda.")
        return

    paid = load_paid_keys()
    repos = sorted({repo for repo, _ in entries})

    new_earnings = []
    still_open = []

    for repo in repos:
        for pr in gh_pr_list(repo):
            title, info = match_pr(repo, pr.get("title", ""), entries)
            if title is None:
                continue

            if pr.get("mergedAt") and (repo, title) not in paid:
                new_earnings.append((pr["mergedAt"], repo, title, info["value"]))
            elif pr.get("state") == "OPEN":
                still_open.append((pr.get("createdAt", "?"), repo, pr.get("url", ""), title))

    if new_earnings:
        path = os.path.join(LOG_DIR, "earnings.log")
        with open(path, "a") as f:
            for merged_at, repo, title, value in new_earnings:
                f.write(f"{merged_at} | PAGO | {repo} | {title} | {value}\n")
        print(f"=== {len(new_earnings)} PR(s) merged detectado(s) - earnings.log atualizado ===")
        for merged_at, repo, title, value in new_earnings:
            print(f"  [OK] {repo} | {title[:50]} | {value} | merged em {merged_at}")
    else:
        print("Nenhum PR novo merged encontrado.")

    if still_open:
        print(f"\n=== {len(still_open)} PR(s) ainda aberto(s) ===")
        for created_at, repo, url, title in still_open:
            print(f"  [???] {repo} | {title[:50]}")
            print(f"        aberto desde {created_at} | {url}")


if __name__ == "__main__":
    main()
