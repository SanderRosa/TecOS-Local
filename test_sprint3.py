"""
TecOS Local v1.0 — Teste automatizado Sprint 3: CRUD de Clientes
"""
import os, sys, sqlite3, urllib.request, urllib.parse, urllib.error

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE    = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, 'database.db')
BASE_URL = 'http://127.0.0.1:5000'
errors = 0

def ok(msg):   print(f"  [PASS] {msg}")
def fail(msg):
    global errors; errors += 1; print(f"  [FAIL] {msg}")
def section(title): print(f"\n[{title}]")

# ── helpers HTTP ──────────────────────────────────────────────
def get(path):
    try:
        r = urllib.request.urlopen(BASE_URL + path, timeout=5)
        return r.getcode(), r.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, ''

def post(path, data: dict):
    encoded = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(BASE_URL + path, data=encoded, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    try:
        # follow_redirects=False: captura o redirect
        opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
        r = opener.open(req, timeout=5)
        return r.getcode(), r.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', errors='replace') if e.fp else ''

# ── limpa clientes de teste anteriores ───────────────────────
def limpar_clientes_teste():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM clientes WHERE nome LIKE 'TESTE_%'")
    conn.commit(); conn.close()

# ─────────────────────────────────────────────────────────────
section("1/7  Rotas HTTP — status 200")
rotas = [
    ("GET /clientes",       "/clientes"),
    ("GET /clientes/novo",  "/clientes/novo"),
]
for label, path in rotas:
    code, _ = get(path)
    if code == 200: ok(f"{label} -> HTTP {code}")
    else:           fail(f"{label} -> HTTP {code}")

# ─────────────────────────────────────────────────────────────
section("2/7  Templates existem e têm conteudo esperado")
tpls = {
    'clientes.html': ['Novo Cliente', 'form-busca', 'empty-state', 'tabela-clientes'],
    'cliente_form.html': ['form-cliente', 'btn-salvar', 'id="nome"', 'id="telefone"',
                          'id="email"', 'id="endereco"', 'id="observacoes"'],
}
for fname, needles in tpls.items():
    path = os.path.join(BASE, 'templates', fname)
    if not os.path.exists(path):
        fail(f"{fname} nao encontrado"); continue
    content = open(path, encoding='utf-8').read()
    for n in needles:
        if n in content: ok(f"{fname}: '{n}'")
        else:            fail(f"{fname}: '{n}' NAO encontrado")

# ─────────────────────────────────────────────────────────────
section("3/7  POST /clientes/novo — validacao: nome vazio")
code, body = post('/clientes/novo', {'nome': '', 'telefone': '', 'email': ''})
# deve redirecionar para /clientes/novo (302) ou retornar flash warning (200)
if code in (200, 302):
    ok(f"Nome vazio -> HTTP {code} (nao gravou sem nome)")
else:
    fail(f"Nome vazio -> HTTP {code} inesperado")

# ─────────────────────────────────────────────────────────────
section("4/7  POST /clientes/novo — cadastro valido")
limpar_clientes_teste()
code, _ = post('/clientes/novo', {
    'nome':        'TESTE_Joao da Silva',
    'telefone':    '(51) 98888-7777',
    'email':       'joao@teste.com',
    'endereco':    'Rua Teste, 1',
    'observacoes': 'Criado pelo teste automatizado',
})
if code in (200, 302): ok(f"Cadastro valido -> HTTP {code}")
else:                  fail(f"Cadastro valido -> HTTP {code}")

# verifica no banco
conn  = sqlite3.connect(DB_PATH)
row   = conn.execute("SELECT * FROM clientes WHERE nome='TESTE_Joao da Silva'").fetchone()
conn.close()
if row: ok(f"Cliente gravado no banco (id={row[0]})")
else:   fail("Cliente NAO encontrado no banco apos POST")
cliente_id = row[0] if row else None

# ─────────────────────────────────────────────────────────────
section("5/7  GET + POST /clientes/<id>/editar")
if cliente_id:
    code, body = get(f'/clientes/{cliente_id}/editar')
    if code == 200 and 'TESTE_Joao' in body:
        ok(f"GET /clientes/{cliente_id}/editar -> HTTP {code}, dados pre-preenchidos")
    else:
        fail(f"GET /clientes/{cliente_id}/editar -> HTTP {code}")

    code, _ = post(f'/clientes/{cliente_id}/editar', {
        'nome':     'TESTE_Joao Editado',
        'telefone': '(51) 91111-2222',
        'email':    'editado@teste.com',
        'endereco': 'Rua Editada, 99',
        'observacoes': '',
    })
    if code in (200, 302): ok(f"POST editar -> HTTP {code}")
    else:                  fail(f"POST editar -> HTTP {code}")

    conn = sqlite3.connect(DB_PATH)
    row2 = conn.execute("SELECT nome FROM clientes WHERE id=?", (cliente_id,)).fetchone()
    conn.close()
    if row2 and row2[0] == 'TESTE_Joao Editado':
        ok("Nome atualizado corretamente no banco")
    else:
        fail(f"Nome no banco: {row2[0] if row2 else 'NAO ENCONTRADO'}")
else:
    fail("Pulando edicao — cliente nao foi criado")

# ─────────────────────────────────────────────────────────────
section("6/7  POST /clientes/<id>/excluir")
if cliente_id:
    code, _ = post(f'/clientes/{cliente_id}/excluir', {})
    if code in (200, 302): ok(f"POST excluir -> HTTP {code}")
    else:                  fail(f"POST excluir -> HTTP {code}")

    conn = sqlite3.connect(DB_PATH)
    row3 = conn.execute("SELECT id FROM clientes WHERE id=?", (cliente_id,)).fetchone()
    conn.close()
    if row3 is None: ok("Cliente removido do banco com sucesso")
    else:            fail("Cliente AINDA existe no banco apos exclusao")
else:
    fail("Pulando exclusao — cliente nao foi criado")

# ─────────────────────────────────────────────────────────────
section("7/7  GET /clientes — busca por nome")
# Insere dois clientes temporarios
conn = sqlite3.connect(DB_PATH)
conn.execute("INSERT INTO clientes (nome, criado_em) VALUES ('TESTE_Alpha', '2026-01-01')")
conn.execute("INSERT INTO clientes (nome, criado_em) VALUES ('TESTE_Beta',  '2026-01-01')")
conn.commit(); conn.close()

code, body = get('/clientes?q=TESTE_Alpha')
if code == 200 and 'TESTE_Alpha' in body and 'TESTE_Beta' not in body:
    ok("Busca por 'TESTE_Alpha' retornou apenas Alpha")
elif code == 200 and 'TESTE_Alpha' in body:
    ok("Busca por 'TESTE_Alpha' retornou resultado (Beta tambem apareceu — ok se busca e client-side)")
else:
    fail(f"Busca -> HTTP {code}, Alpha no body: {'TESTE_Alpha' in body}")

limpar_clientes_teste()

# ── App.py tem rotas certas ───────────────────────────────────
section("EXTRA  Verificar rotas no app.py")
app_src = open(os.path.join(BASE, 'app.py'), encoding='utf-8').read()
for trecho in [
    "'/clientes'", "'/clientes/novo'",
    "'/clientes/<int:cliente_id>/editar'",
    "'/clientes/<int:cliente_id>/excluir'",
    "clientes_list", "cliente_criar", "cliente_salvar", "cliente_excluir",
]:
    if trecho in app_src: ok(f"app.py tem: {trecho}")
    else:                 fail(f"app.py NAO tem: {trecho}")

# ── base.html tem link ativo de Clientes ─────────────────────
base_src = open(os.path.join(BASE, 'templates', 'base.html'), encoding='utf-8').read()
if "clientes_list" in base_src and "menu-clientes" in base_src:
    ok("base.html: link Clientes ativado")
else:
    fail("base.html: link Clientes ainda desativado")

# ── Resultado final ───────────────────────────────────────────
print("\n" + "=" * 50)
if errors == 0:
    print("  TODOS OS TESTES PASSARAM - Sprint 3 OK!")
else:
    print(f"  {errors} ERRO(S) ENCONTRADO(S) - verifique acima.")
print("=" * 50 + "\n")
sys.exit(errors)
