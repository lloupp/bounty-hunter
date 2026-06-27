#!/usr/bin/env bash
# Bounty Hunter - Script principal
# Uso: ./hunt.sh [comando]
#
# Comandos:
#   search       - Busca bounties disponiveis
#   work N       - Delega bounty #N para o Claude Code
#   quick N      - Delega bounty #N com prompt rapido (tipo Chrisgpt)
#   status       - Mostra status dos trabalhos em andamento
#   earnings     - Mostra ganhos acumulados
#   list         - Lista bounties do ultimo search

set -euo pipefail

BH_DIR="$HOME/bounty-hunter"
RESULTS_DIR="$BH_DIR/results"
WORK_DIR="$BH_DIR/work"
LOG_DIR="$BH_DIR/logs"

mkdir -p "$RESULTS_DIR" "$WORK_DIR" "$LOG_DIR"

_get_bounty() {
    local NUM="$1"
    if [ ! -f "$RESULTS_DIR/latest.json" ]; then
        echo "Nenhum resultado encontrado. Rode './hunt.sh search' primeiro."
        exit 1
    fi
    
    python3 -c "
import json, sys
with open('$RESULTS_DIR/latest.json') as f:
    data = json.load(f)
idx = int('$NUM') - 1
if idx < 0 or idx >= len(data['bounties']):
    print('ERROR: Numero invalido. Use 1 a', len(data['bounties']), file=sys.stderr)
    sys.exit(1)
b = data['bounties'][idx]
print(json.dumps(b))
"
}

_review_and_send() {
    # Mostra o diff gerado pela IA e exige confirmacao manual antes
    # de dar push/abrir PR. Nada e enviado sem voce ver o que mudou.
    local WORKSPACE="$1" BASE_BRANCH="$2" NUM="$3" REPO="$4" TITLE="$5" VALUE="$6" MODE="$7"
    local NEW_BRANCH
    NEW_BRANCH=$(git -C "$WORKSPACE" rev-parse --abbrev-ref HEAD)

    echo ""
    echo "=== Revisao antes do envio ==="

    if [ "$NEW_BRANCH" = "$BASE_BRANCH" ]; then
        echo "Claude Code nao criou uma branch nova nem fez commit. Nada a enviar."
        echo "$(date -Iseconds) | ${MODE}-NOOP | #$NUM | $REPO | $TITLE | \$$VALUE" >> "$LOG_DIR/hunt.log"
        return
    fi

    git -C "$WORKSPACE" --no-pager log --oneline "$BASE_BRANCH..$NEW_BRANCH"
    echo ""
    git -C "$WORKSPACE" --no-pager diff "$BASE_BRANCH...$NEW_BRANCH" || true
    echo ""
    read -r -p "Revisei o diff acima. Enviar push + abrir PR? (s/N): " CONFIRM

    if [[ "$CONFIRM" =~ ^[sS]$ ]]; then
        git -C "$WORKSPACE" push -u origin "$NEW_BRANCH"
        (cd "$WORKSPACE" && gh pr create --title "$TITLE" --body "Resolve: $TITLE

Implementado com assistencia de IA; revisado antes do envio.") 2>&1 || \
            echo "Nao foi possivel abrir o PR automaticamente. Rode 'gh pr create' manualmente em $WORKSPACE."
        echo "$(date -Iseconds) | $MODE | #$NUM | $REPO | $TITLE | \$$VALUE" >> "$LOG_DIR/hunt.log"
    else
        echo "Envio cancelado. As mudancas ficam na branch '$NEW_BRANCH' em $WORKSPACE para revisao manual."
        echo "$(date -Iseconds) | ${MODE}-PENDENTE | #$NUM | $REPO | $TITLE | \$$VALUE" >> "$LOG_DIR/hunt.log"
    fi
}

case "${1:-search}" in
    search)
        echo "=== Buscando bounties ==="
        python3 "$BH_DIR/scripts/search-bounties.py"
        echo ""
        echo "Para trabalhar numa bounty: ./hunt.sh work <NUMERO>"
        echo "Para dispatch rapido: ./hunt.sh quick <NUMERO>"
        ;;
    
    list)
        if [ ! -f "$RESULTS_DIR/latest.json" ]; then
            echo "Nenhum resultado. Rode './hunt.sh search' primeiro."
            exit 1
        fi
        python3 -c "
import json
with open('$RESULTS_DIR/latest.json') as f:
    data = json.load(f)
for i, b in enumerate(data['bounties'], 1):
    v = f\"\${b['value']:,.0f}\" if b['value'] else '\$?'
    ai = ' [AI]' if b.get('ai_friendly') else ''
    cat = b.get('category','?').upper()
    print(f\"  {i:2d}. {v:>8s}  [{cat:<13s}]{ai}  {b['title'][:60]}\")
"
        ;;
    
    work)
        NUM="${2:-}"
        if [ -z "$NUM" ]; then
            echo "Uso: ./hunt.sh work <NUMERO_DA_BOUNTY>"
            echo "Rode './hunt.sh list' para ver as bounties."
            exit 1
        fi
        
        BOUNTY=$(_get_bounty "$NUM") || exit 1
        
        TITLE=$(echo "$BOUNTY" | python3 -c "import json,sys; print(json.load(sys.stdin)['title'])")
        URL=$(echo "$BOUNTY" | python3 -c "import json,sys; print(json.load(sys.stdin)['url'])")
        REPO=$(echo "$BOUNTY" | python3 -c "import json,sys; print(json.load(sys.stdin)['repo'])")
        VALUE=$(echo "$BOUNTY" | python3 -c "import json,sys; b=json.load(sys.stdin); print(b['value'] or '?')")
        
        echo "=== Trabalhando na Bounty #$NUM ==="
        echo "Titulo: $TITLE"
        echo "Repo: $REPO"
        echo "Valor: \$$VALUE"
        echo "URL: $URL"
        echo ""
        
        # Clonar o repo
        WORKSPACE="$WORK_DIR/$(echo $REPO | tr '/' '-')"
        if [ ! -d "$WORKSPACE" ]; then
            echo "Clonando $REPO..."
            gh repo clone "$REPO" "$WORKSPACE" 2>&1 || {
                echo "Tentando via git clone..."
                git clone "https://github.com/$REPO.git" "$WORKSPACE" 2>&1
            }
        else
            echo "Repo ja clonado em $WORKSPACE"
            cd "$WORKSPACE" && git pull 2>&1 || true
        fi
        
        BASE_BRANCH=$(git -C "$WORKSPACE" rev-parse --abbrev-ref HEAD)

        echo ""
        echo "=== Delegando para Claude Code ==="
        echo ""

        # Prompt detalhado para o Claude Code
        PROMPT="Resolva esta GitHub issue: $TITLE. Issue URL: $URL. Instrucoes: 1) Leia a issue completa. 2) Entenda o contexto do projeto. 3) Implemente a correcao/feature. 4) Escreva testes se aplicavel e rode a suite de testes existente do projeto antes de finalizar. 5) Crie uma branch descritiva a partir de $BASE_BRANCH. 6) Faca commit das mudancas com mensagem clara, incluindo a nota 'Implementado com assistencia de IA; revisado antes do envio.'. NAO faca push e NAO abra PR - o envio sera revisado manualmente."

        (cd "$WORKSPACE" && claude -p "$PROMPT" --dangerously-skip-permissions) 2>&1 | tee "$LOG_DIR/bounty-${NUM}-$(date +%Y%m%d-%H%M%S).log"

        _review_and_send "$WORKSPACE" "$BASE_BRANCH" "$NUM" "$REPO" "$TITLE" "$VALUE" "WORK"
        ;;
    
    quick)
        NUM="${2:-}"
        if [ -z "$NUM" ]; then
            echo "Uso: ./hunt.sh quick <NUMERO_DA_BOUNTY>"
            exit 1
        fi
        
        BOUNTY=$(_get_bounty "$NUM") || exit 1
        
        TITLE=$(echo "$BOUNTY" | python3 -c "import json,sys; print(json.load(sys.stdin)['title'])")
        URL=$(echo "$BOUNTY" | python3 -c "import json,sys; print(json.load(sys.stdin)['url'])")
        REPO=$(echo "$BOUNTY" | python3 -c "import json,sys; print(json.load(sys.stdin)['repo'])")
        VALUE=$(echo "$BOUNTY" | python3 -c "import json,sys; b=json.load(sys.stdin); print(b['value'] or '?')")
        
        echo "=== Quick Dispatch: Bounty #$NUM ==="
        echo "Titulo: $TITLE"
        echo "Repo: $REPO | Valor: \$$VALUE"
        echo ""
        
        # Clonar
        WORKSPACE="$WORK_DIR/$(echo $REPO | tr '/' '-')"
        if [ ! -d "$WORKSPACE" ]; then
            echo "Clonando $REPO..."
            gh repo clone "$REPO" "$WORKSPACE" 2>&1
        else
            cd "$WORKSPACE" && git pull 2>&1 || true
        fi

        BASE_BRANCH=$(git -C "$WORKSPACE" rev-parse --abbrev-ref HEAD)

        # Prompt rapido, mas sem ocultar autoria e sem push/PR automatico
        PROMPT="Resolva esta issue de forma rapida e correta: $TITLE. URL: $URL. Crie uma branch descritiva a partir de $BASE_BRANCH, implemente, rode os testes do projeto e faca commit com a nota 'Implementado com assistencia de IA; revisado antes do envio.'. NAO faca push e NAO abra PR."

        echo "Dispatching Claude Code..."
        (cd "$WORKSPACE" && claude -p "$PROMPT" --dangerously-skip-permissions) 2>&1 | tee "$LOG_DIR/bounty-${NUM}-quick-$(date +%Y%m%d-%H%M%S).log"

        _review_and_send "$WORKSPACE" "$BASE_BRANCH" "$NUM" "$REPO" "$TITLE" "$VALUE" "QUICK"
        ;;
    
    status)
        echo "=== Status dos trabalhos ==="
        if [ -f "$LOG_DIR/hunt.log" ]; then
            cat "$LOG_DIR/hunt.log"
        else
            echo "Nenhum trabalho registrado ainda."
        fi
        echo ""
        echo "Repositorios clonados:"
        ls -1 "$WORK_DIR" 2>/dev/null || echo "  (nenhum)"
        ;;
    
    earnings)
        echo "=== Ganhos ==="
        if [ -f "$LOG_DIR/earnings.log" ]; then
            cat "$LOG_DIR/earnings.log"
            echo ""
            TOTAL=$(awk -F'|' '{gsub(/[^0-9.]/,"",$5); sum+=$5} END{print sum}' "$LOG_DIR/earnings.log")
            echo "TOTAL: \$$TOTAL"
        else
            echo "Nenhum ganho registrado ainda."
            echo ""
            echo "Para registrar um pagamento:"
            echo "  echo \"\$(date -Iseconds) | PAGO | repo | bounty | VALOR\" >> $LOG_DIR/earnings.log"
        fi
        ;;
    
    *)
        echo "Comando desconhecido: $1"
        echo ""
        echo "Uso: ./hunt.sh [comando]"
        echo ""
        echo "Comandos:"
        echo "  search       Busca bounties disponiveis"
        echo "  list         Lista bounties do ultimo search"
        echo "  work N       Delega bounty #N para Claude Code (prompt detalhado)"
        echo "  quick N      Delega bounty #N para Claude Code (prompt rapido estilo Chrisgpt)"
        echo "  status       Mostra status dos trabalhos"
        echo "  earnings     Mostra ganhos acumulados"
        exit 1
        ;;
esac
