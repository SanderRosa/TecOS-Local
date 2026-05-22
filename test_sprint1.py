"""
TecOS Local v1.0 - Teste automatizado da Sprint 1
Executa verificacoes de: banco, tabelas, colunas, rotas HTTP e arquivos.
"""

import os
import sys
import sqlite3
import urllib.request
import urllib.error

# Força UTF-8 no terminal Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"
errors = 0

def ok(msg):
    print(f"  {PASS} {msg}")

def fail(msg):
    global errors
    errors += 1
    print(f"  {FAIL} {msg}")

def warn(msg):
    print(f"  {WARN} {msg}")

# ─── 1. ARQUIVOS OBRIGATÓRIOS ───────────────────────────────
print("\n[1/5] Verificando arquivos obrigatórios...")
required_files = [
    "app.py",
    "requirements.txt",
    "iniciar_sistema.bat",
    "README.md",
    os.path.join("templates", "base.html"),
    os.path.join("templates", "dashboard.html"),
    os.path.join("static", "css", "style.css"),
]
for f in required_files:
    path = os.path.join(BASE, f)
    if os.path.exists(path):
        size = os.path.getsize(path)
        ok(f"{f}  ({size:,} bytes)")
    else:
        fail(f"{f}  — ARQUIVO NÃO ENCONTRADO")

# ─── 2. PASTAS OBRIGATÓRIAS ─────────────────────────────────
print("\n[2/5] Verificando pastas obrigatórias...")
required_dirs = [
    os.path.join("static", "uploads"),
    os.path.join("static", "logos"),
    "relatorios",
    "backups",
]
for d in required_dirs:
    path = os.path.join(BASE, d)
    if os.path.isdir(path):
        ok(f"{d}/")
    else:
        fail(f"{d}/  — PASTA NÃO ENCONTRADA")

# ─── 3. BANCO DE DADOS ──────────────────────────────────────
print("\n[3/5] Verificando banco de dados SQLite...")
db_path = os.path.join(BASE, "database.db")
if not os.path.exists(db_path):
    fail("database.db não encontrado")
else:
    ok(f"database.db  ({os.path.getsize(db_path):,} bytes)")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    expected_tables = {
        "empresa":       ["id", "nome", "documento", "telefone", "email", "endereco", "logo"],
        "clientes":      ["id", "nome", "telefone", "email", "endereco", "observacoes", "criado_em"],
        "equipamentos":  ["id", "cliente_id", "tipo", "marca", "modelo", "numero_serie",
                          "local_instalacao", "observacoes", "criado_em"],
        "ordens_servico":["id", "cliente_id", "equipamento_id", "data_abertura", "problema",
                          "diagnostico", "servico_executado", "pecas_utilizadas", "valor",
                          "status", "proxima_manutencao", "observacoes", "criado_em"],
        "fotos_os":      ["id", "ordem_id", "caminho_foto", "criado_em"],
    }

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    existing_tables = {row[0] for row in cursor.fetchall()}

    for table, expected_cols in expected_tables.items():
        if table not in existing_tables:
            fail(f"Tabela '{table}' NÃO existe")
            continue
        cursor.execute(f"PRAGMA table_info({table})")
        actual_cols = [row[1] for row in cursor.fetchall()]
        missing_cols = [c for c in expected_cols if c not in actual_cols]
        if missing_cols:
            fail(f"Tabela '{table}' — colunas faltando: {missing_cols}")
        else:
            ok(f"Tabela '{table}'  ({len(actual_cols)} colunas OK)")

    # Verifica FK
    cursor.execute("PRAGMA foreign_key_list(equipamentos)")
    fks = cursor.fetchall()
    if any(row[2] == "clientes" for row in fks):
        ok("FK equipamentos -> clientes OK")
    else:
        fail("FK equipamentos -> clientes NAO configurada")

    cursor.execute("PRAGMA foreign_key_list(ordens_servico)")
    fks = cursor.fetchall()
    tables_ref = {row[2] for row in fks}
    if "clientes" in tables_ref and "equipamentos" in tables_ref:
        ok("FK ordens_servico -> clientes + equipamentos OK")
    else:
        fail(f"FKs de ordens_servico incompletas - refs encontradas: {tables_ref}")

    conn.close()

# ─── 4. ROTA HTTP ───────────────────────────────────────────
print("\n[4/5] Verificando rotas HTTP (servidor Flask)...")
routes = [
    ("GET  /", "http://127.0.0.1:5000/"),
    ("GET  /static/css/style.css", "http://127.0.0.1:5000/static/css/style.css"),
]
for label, url in routes:
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=4)
        code = resp.getcode()
        length = len(resp.read())
        ok(f"{label}  → HTTP {code}  ({length:,} bytes)")
    except urllib.error.HTTPError as e:
        fail(f"{label}  → HTTP {e.code}: {e.reason}")
    except Exception as e:
        fail(f"{label}  → {type(e).__name__}: {e}")

# ─── 5. CONTEÚDO DOS TEMPLATES ──────────────────────────────
print("\n[5/5] Verificando conteúdo dos templates...")

checks = {
    os.path.join("templates", "base.html"): [
        ("Bootstrap 5 CDN", "cdn.jsdelivr.net/npm/bootstrap@5"),
        ("Bootstrap Icons CDN", "bootstrap-icons"),
        ("Google Fonts", "fonts.googleapis.com"),
        ("Link style.css", "style.css"),
        ("Block content", "{% block content %}"),
        ("Menu Dashboard", "Dashboard"),
        ("Menu Clientes", "Clientes"),
        ("Menu Equipamentos", "Equipamentos"),
        ("Menu Ordens de Serviço", "Ordens de Servi"),
        ("Menu Backup", "Backup"),
        ("Menu Empresa", "Empresa"),
    ],
    os.path.join("templates", "dashboard.html"): [
        ("Extends base", "extends 'base.html'"),
        ("Card Clientes", "total_clientes"),
        ("Card Equipamentos", "total_equipamentos"),
        ("Card OS Abertas", "os_abertas"),
        ("Card Em Andamento", "os_andamento"),
        ("Card Concluídas", "os_concluidas"),
        ("Card Manutenções", "proximas_manutencoes"),
    ],
    os.path.join("static", "css", "style.css"): [
        ("Variável --primary", "--primary"),
        ("Sidebar styles", ".sidebar"),
        ("Topbar styles", ".topbar"),
        ("Stat card", ".stat-card"),
    ],
}

for filepath, assertions in checks.items():
    full = os.path.join(BASE, filepath)
    try:
        content = open(full, encoding="utf-8").read()
        for label, needle in assertions:
            if needle in content:
                ok(f"{os.path.basename(filepath)}: {label}")
            else:
                fail(f"{os.path.basename(filepath)}: {label}  — '{needle}' NÃO encontrado")
    except FileNotFoundError:
        fail(f"{filepath} não encontrado")

# ─── RESULTADO FINAL ────────────────────────────────────────
print("\n" + "=" * 50)
if errors == 0:
    print("  TODOS OS TESTES PASSARAM - Sprint 1 OK!")
else:
    print(f"  {errors} ERRO(S) ENCONTRADO(S) - verifique acima.")
print("=" * 50 + "\n")

sys.exit(errors)
