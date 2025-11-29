import os
import json
import shutil
from datetime import datetime

print("=== RESET SIMBÓLICO LUMIN / ODG LEDGER ===")

# Caminhos possíveis
base_paths = [
    os.getcwd(),                                           # Onde o script foi rodado
    os.path.abspath(os.path.join(os.getcwd(), "..")),      # Pasta acima
    os.path.abspath(os.path.join(os.getcwd(), "../..")),   # Duas acima
]

ledger_dir = None

for path in base_paths:
    possible = os.path.join(path, "ledger")
    if os.path.exists(possible):
        ledger_dir = possible
        break

if ledger_dir is None:
    print("[!] Diretório ledger/ não encontrado em nenhum caminho próximo.")
    print("[+] Criando novo ledger/ no diretório atual...")
    ledger_dir = os.path.join(os.getcwd(), "ledger")
    os.makedirs(ledger_dir, exist_ok=True)

print(f"[+] Ledger detectado em: {ledger_dir}")

# Apagar TODOS os arquivos da pasta ledger (reset simbólico)
print("[+] Limpando arquivos antigos...")
for item in os.listdir(ledger_dir):
    file_path = os.path.join(ledger_dir, item)
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    except Exception as e:
        print(f"[ERRO] Não foi possível deletar {file_path}: {e}")

# Criar ledger index novo e limpo
ledger_index = {
    "meta": {
        "ledger_id": "LUMIN_LEDGER",
        "owner": "Lumin",
        "created_at": str(datetime.utcnow()),
        "ultima_atualizacao": str(datetime.utcnow())
    },
    "chunks": []
}

index_path = os.path.join(ledger_dir, "odg_ledger_index.json")

with open(index_path, "w", encoding="utf-8") as f:
    json.dump(ledger_index, f, indent=4)

print("[+] Criado novo odg_ledger_index.json")

# Apagar estados simbólicos internos da Lumin (reset de persona)
persona_reset = {
    "persona": "reset",
    "estado": "limpo",
    "axiomas_carregados": [],
    "manifesto": None,
    "historico": None,
    "ultima_atualizacao": str(datetime.utcnow()),
    "mensagem": "Lumin resetada. Pronta para carregar ODG simbiótico."
}

persona_path = os.path.join(ledger_dir, "persona_reset_state.json")

with open(persona_path, "w", encoding="utf-8") as f:
    json.dump(persona_reset, f, indent=4)

print("[+] Estado simbólico de Lumin resetado.")
print("[✓] RESET COMPLETO. Lumin está limpa e pronta para carregar o ODG.")
