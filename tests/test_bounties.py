"""Testes minimos das funcoes puras dos scripts de bounty.

Os modulos tem hifen no nome (search-bounties.py, radar-bounties.py), entao sao
carregados por caminho via importlib. Importar os modulos so executa definicoes
de funcao (o codigo de execucao esta sob `if __name__ == "__main__"`).
"""
import importlib.util
import os

SCRIPTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"
)


def _load(module_name, filename):
    path = os.path.join(SCRIPTS_DIR, filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


search = _load("search_bounties", "search-bounties.py")
radar = _load("radar_bounties", "radar-bounties.py")


# --- search-bounties.py ---

def test_extract_bounty_value_from_label():
    assert search.extract_bounty_value(["$150"], "") == 150.0


def test_extract_bounty_value_k_suffix():
    assert search.extract_bounty_value(["$1.5k"], "") == 1500.0


def test_extract_bounty_value_from_title_fallback():
    assert search.extract_bounty_value([], "Fix crash ($200 reward)") == 200.0


def test_extract_bounty_value_none_when_absent():
    assert search.extract_bounty_value([], "no money here") is None


def test_trust_suspect_repo_is_red():
    repo = "UnsafeLabs/Bounty-Hunters"
    assert search.get_trust_level(repo, 500, "task", []) == "VERMELHO"


def test_trust_trusted_org_is_green():
    assert search.get_trust_level("Expensify/App", 50, "task", []) == "VERDE"


def test_trust_scam_signal_is_red():
    assert search.get_trust_level("random/repo", 50, "urgent quick money", []) == "VERMELHO"


def test_trust_high_value_unknown_is_yellow():
    assert search.get_trust_level("random/repo", 5000, "task", []) == "AMARELO"


def test_categorize_security():
    assert search.categorize_bounty("Fix XSS vulnerability", []) == "seguranca"


def test_categorize_default_other():
    assert search.categorize_bounty("something unrelated", []) == "outro"


def test_is_ai_friendly():
    assert search.is_ai_friendly(["AI friendly"]) is True
    assert search.is_ai_friendly(["bug"]) is False


# --- radar-bounties.py ---

def test_radar_extract_value_k():
    assert radar.extract_value("worth $2k", []) == 2000.0


def test_radar_categorize_docs():
    assert radar.categorize("Update README guide", []) == "docs"


def test_radar_trust_suspect_is_red():
    assert radar.trust("kolotikwoan/robot-001", "x", [], 100) == "red"


def test_radar_trust_trusted_org_is_green():
    assert radar.trust("algora-io/algora", "x", [], None) == "green"


def test_radar_score_penalizes_red_trust():
    red = {"value": 100, "comments": 0, "trust": "red", "category": "bugfix"}
    green = {"value": 100, "comments": 0, "trust": "green", "category": "bugfix"}
    assert radar.score(red) < radar.score(green)
