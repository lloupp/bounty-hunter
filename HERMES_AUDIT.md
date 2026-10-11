# Auditoria Hermes — bounty-hunter

Gerado em: `2026-09-06 11:59:30`

## Escopo

- **Não alterei código-fonte nem arquivos de configuração.**
- Arquivo criado/atualizado por pedido do Eduardo: `HERMES_AUDIT.md`.
- Testes executados apenas quando havia comando/estrutura detectável, com timeout curto e sem instalar dependências do projeto.

## Resumo

- Tipo detectado: **Site estático / HTML**
- Arquivos analisados: **81494**
- Tamanho aproximado analisado: **1667.57 MB**

## Linguagens / tipos de arquivo

- Outro: 77825
- Python: 1754
- Markdown: 523
- TypeScript: 352
- YAML: 325
- JSON: 258
- Shell: 114
- JavaScript: 100
- HTML: 96
- Rust: 50

## Arquivos principais vistos

- `.gitignore`
- `hunt.sh`
- `results/latest.json`
- `results/radar-latest.json`
- `scripts/radar-bounties.py`
- `scripts/search-bounties.py`
- `social/memanto-showcase.txt`
- `work/AncientBeast/.babelrc.js`
- `work/AncientBeast/.dockerignore`
- `work/AncientBeast/.editorconfig`
- `work/AncientBeast/.env.example`
- `work/AncientBeast/.eslintignore`
- `work/AncientBeast/.eslintrc.json`
- `work/AncientBeast/.gitignore`
- `work/AncientBeast/.htaccess`
- `work/AncientBeast/.husky/pre-commit`
- `work/AncientBeast/.prettierignore`
- `work/AncientBeast/.prettierrc`
- `work/AncientBeast/AGPL.txt`
- `work/AncientBeast/CODE_OF_CONDUCT.md`
- `work/AncientBeast/CONTRIBUTING.md`
- `work/AncientBeast/Dockerfile`
- `work/AncientBeast/HOW_TO_PLAY.md`
- `work/AncientBeast/LICENSE.md`
- `work/AncientBeast/README.md`
- `work/AncientBeast/SECURITY.md`
- `work/AncientBeast/assets/README.md`
- `work/AncientBeast/assets/autoload/drops/apple.png`
- `work/AncientBeast/assets/autoload/drops/bat wing.png`
- `work/AncientBeast/assets/autoload/drops/bread.png`
- `work/AncientBeast/assets/autoload/drops/carrot.png`
- `work/AncientBeast/assets/autoload/drops/cherry.png`
- `work/AncientBeast/assets/autoload/drops/fang.png`
- `work/AncientBeast/assets/autoload/drops/feather.png`
- `work/AncientBeast/assets/autoload/drops/fish.png`
- `work/AncientBeast/assets/autoload/drops/fried chicken.png`
- `work/AncientBeast/assets/autoload/drops/frog leg.png`
- `work/AncientBeast/assets/autoload/drops/hook.png`
- `work/AncientBeast/assets/autoload/drops/lemon.png`
- `work/AncientBeast/assets/autoload/drops/meat.png`
- … mais 81454 arquivo(s)

## Estado Git

- Comando: `git status --short --branch`
- Exit code: `0`

```text
## main...origin/main
?? scripts/radar-bounties.py
```

## Resultado dos testes / validações

### ❌ FALHOU
- Comando: `python3 -m pytest -q`
- Exit code: `3`
- Tempo: `35.72s`

```text
ERROR: PyTorch with CUDA support required. Install: pip install torch
INTERNALERROR> Traceback (most recent call last):
INTERNALERROR>   File "/home/eduardodlima/projetos/bounty-hunter/work/Rustchain/miners/gpu_fingerprint.py", line 40, in <module>
INTERNALERROR>     import torch
INTERNALERROR> ModuleNotFoundError: No module named 'torch'
INTERNALERROR> 
INTERNALERROR> During handling of the above exception, another exception occurred:
INTERNALERROR> 
INTERNALERROR> Traceback (most recent call last):
INTERNALERROR>   File "/home/eduardodlima/.hermes/hermes-agent/venv/lib/python3.11/site-packages/_pytest/main.py", line 330, in wrap_session
INTERNALERROR>     session.exitstatus = doit(config, session) or 0
INTERNALERROR>                          ^^^^^^^^^^^^^^^^^^^^^
INTERNALERROR>   File "/home/eduardodlima/.hermes/hermes-agent/venv/lib/python3.11/site-packages/_pytest/main.py", line 383, in _main
INTERNALERROR>     config.hook.pytest_collection(session=session)
INTERNALERROR>   File "/home/eduardodlima/.hermes/hermes-agent/venv/lib/python3.11/site-packages/pluggy/_hooks.py", line 512, in __call__
INTERNALERROR>     return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
INTERNALERROR>            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
INTERNALERROR>   File "/home/eduardodlima/.hermes/hermes-agent/venv/lib/python3.11/site-packages/pluggy/_manager.py", line 120, in _hookexec
INTERNALERROR>     return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
INTERNALERROR>            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
INTERNALERROR>   File "/home/eduardodlima/.hermes/hermes-agent/venv/lib/python3.11/site-packages/pluggy/_callers.py", line 167, in _multicall
INTERNALERROR>     raise exceptio

...[saída cortada]...

lib/__init__.py", line 126, in import_module
INTERNALERROR>     return _bootstrap._gcd_import(name[level:], package, level)
INTERNALERROR>            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
INTERNALERROR>   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
INTERNALERROR>   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
INTERNALERROR>   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
INTERNALERROR>   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
INTERNALERROR>   File "/home/eduardodlima/.hermes/hermes-agent/venv/lib/python3.11/site-packages/_pytest/assertion/rewrite.py", line 188, in exec_module
INTERNALERROR>     exec(co, module.__dict__)
INTERNALERROR>   File "/home/eduardodlima/projetos/bounty-hunter/work/Rustchain/miners/gpu_spoof_test.py", line 29, in <module>
INTERNALERROR>     from gpu_fingerprint import run_gpu_fingerprint
INTERNALERROR>   File "/home/eduardodlima/projetos/bounty-hunter/work/Rustchain/miners/gpu_fingerprint.py", line 44, in <module>
INTERNALERROR>     sys.exit(1)
INTERNALERROR> SystemExit: 1
mainloop: caught unexpected SystemExit!

22 warnings, 14 errors in 34.20s

```


## Propostas gerais de melhoria

1. Criar README com objetivo, como rodar, comandos de teste e status atual.
2. Adicionar checklist de deploy (Vercel/Netlify), SEO básico e teste visual mobile.
3. Corrigir os testes/comandos que falharam antes de evoluir funcionalidades.
4. Criar documentação curta de arquitetura (`docs/arquitetura.md`).

## Próximo passo sugerido

Primeiro estabilizar os testes/comandos que falharam; depois evoluir funcionalidades.

---

## Intervenção Claude Code

Gerado em: `2026-09-06` — modelo Opus 4.8.

### Diagnóstico

A falha do `pytest -q` **não era do código do bounty-hunter**. O comando foi
executado a partir da raiz e coletou recursivamente os testes dentro de `work/`,
que contém repositórios de terceiros clonados (bounties em andamento). O arquivo
`work/Rustchain/miners/gpu_fingerprint.py` chama `sys.exit(1)` no momento do
import quando o `torch` não está instalado, o que aborta a coleta inteira do
pytest (`INTERNALERROR`). O diretório `work/` é ignorado pelo git e não faz parte
do código-fonte do projeto.

Também foi identificado um bug latente: tanto `hunt.sh` quanto os scripts Python
apontavam `BH_DIR` para `~/bounty-hunter`, um diretório **inexistente** (o projeto
real vive em `~/projetos/bounty-hunter`). Isso fazia os resultados serem gravados
fora do projeto.

### O que foi alterado

1. **`pytest.ini` (novo)** — restringe a coleta a `testpaths = tests` e adiciona
   `norecursedirs = work results logs .git`, isolando os repositórios de terceiros
   da suíte de testes do projeto.
2. **`tests/test_bounties.py` (novo)** — 16 testes unitários das funções puras dos
   dois scripts (extração de valor, classificação de confiança/trust, categorização,
   scoring, detecção AI-friendly). Os módulos com hífen no nome são carregados via
   `importlib`.
3. **`scripts/radar-bounties.py` e `scripts/search-bounties.py`** — `BH_DIR` agora é
   derivado da localização do próprio arquivo (pai de `scripts/`), com override
   opcional por `BOUNTY_HUNTER_DIR`. Passa a resolver corretamente para a raiz do
   projeto.
4. **`hunt.sh`** — mesma correção: `BH_DIR` derivado de `${BASH_SOURCE[0]}` com
   override por `BOUNTY_HUNTER_DIR`.

Nenhuma funcionalidade existente foi removida. O diretório `work/` (repos de
terceiros) e `apura-tributario-v2` não foram tocados.

### Resultado dos testes

- `python3 -m pytest -q` → **16 passed in 0.20s** ✅
- `bash -n hunt.sh` → OK ✅
- `python3 -m py_compile scripts/*.py` → OK ✅
- Verificação manual: `BH_DIR` resolve para `/home/eduardodlima/projetos/bounty-hunter`
  e o override `BOUNTY_HUNTER_DIR` funciona ✅

### Próximo passo recomendado

Adicionar um README curto com objetivo/uso e considerar um teste de fumaça para
`hunt.sh` (ex.: `./hunt.sh` sem args deve imprimir o help e sair com código 1).
