import os
import sqlite3
from flask import Flask, render_template, g, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from datetime import datetime

# ─────────────────────────────────────────────
#  Configuração do App
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE  = os.path.join(BASE_DIR, 'database.db')

app = Flask(__name__)
app.secret_key = 'tecos-local-sprint2-secret'

# ─────────────────────────────────────────────
#  Configuração de Upload
# ─────────────────────────────────────────────
LOGOS_DIR         = os.path.join(BASE_DIR, 'static', 'logos')
ALLOWED_LOGO_EXT  = {'png', 'jpg', 'jpeg'}
MAX_LOGO_SIZE     = 4 * 1024 * 1024   # 4 MB

app.config['MAX_CONTENT_LENGTH'] = MAX_LOGO_SIZE

def allowed_logo(filename):
    """Retorna True se a extensão do arquivo for permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_LOGO_EXT

# ─────────────────────────────────────────────
#  Criação automática de pastas
# ─────────────────────────────────────────────
REQUIRED_DIRS = [
    os.path.join(BASE_DIR, 'static', 'uploads'),
    os.path.join(BASE_DIR, 'static', 'logos'),
    os.path.join(BASE_DIR, 'relatorios'),
    os.path.join(BASE_DIR, 'backups'),
]

for d in REQUIRED_DIRS:
    os.makedirs(d, exist_ok=True)

# ─────────────────────────────────────────────
#  Banco de Dados
# ─────────────────────────────────────────────
def get_db():
    """Retorna conexão com o banco de dados, reutilizando dentro do contexto da requisição."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(error):
    """Fecha a conexão ao fim de cada requisição."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Cria as tabelas no banco de dados se ainda não existirem."""
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")

    db.executescript("""
        CREATE TABLE IF NOT EXISTS empresa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            documento TEXT,
            telefone TEXT,
            email TEXT,
            endereco TEXT,
            logo TEXT
        );

        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            email TEXT,
            endereco TEXT,
            observacoes TEXT,
            criado_em TEXT
        );

        CREATE TABLE IF NOT EXISTS equipamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            tipo TEXT,
            marca TEXT,
            modelo TEXT,
            numero_serie TEXT,
            local_instalacao TEXT,
            observacoes TEXT,
            criado_em TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        );

        CREATE TABLE IF NOT EXISTS ordens_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            equipamento_id INTEGER,
            data_abertura TEXT,
            problema TEXT,
            diagnostico TEXT,
            servico_executado TEXT,
            pecas_utilizadas TEXT,
            valor REAL,
            status TEXT,
            proxima_manutencao TEXT,
            observacoes TEXT,
            criado_em TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (equipamento_id) REFERENCES equipamentos(id)
        );

        CREATE TABLE IF NOT EXISTS fotos_os (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ordem_id INTEGER NOT NULL,
            caminho_foto TEXT,
            criado_em TEXT,
            FOREIGN KEY (ordem_id) REFERENCES ordens_servico(id)
        );
    """)
    db.commit()
    db.close()
    print("[TecOS] Banco de dados inicializado com sucesso.")


# ─────────────────────────────────────────────
#  Context Processor — variáveis globais p/ templates
# ─────────────────────────────────────────────
@app.context_processor
def inject_globals():
    db = get_db()
    empresa = db.execute("SELECT * FROM empresa LIMIT 1").fetchone()
    return dict(empresa=empresa, now=datetime.now())


# ─────────────────────────────────────────────
#  Rotas — Sprint 1
# ─────────────────────────────────────────────
@app.route('/')
def dashboard():
    db = get_db()

    total_clientes    = db.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    total_equipamentos = db.execute("SELECT COUNT(*) FROM equipamentos").fetchone()[0]
    os_abertas        = db.execute("SELECT COUNT(*) FROM ordens_servico WHERE status = 'Aberta'").fetchone()[0]
    os_andamento      = db.execute("SELECT COUNT(*) FROM ordens_servico WHERE status = 'Em Andamento'").fetchone()[0]
    os_concluidas     = db.execute("SELECT COUNT(*) FROM ordens_servico WHERE status = 'Concluída'").fetchone()[0]

    # Próximas manutenções: OS com proxima_manutencao >= hoje
    hoje = datetime.now().strftime('%Y-%m-%d')
    proximas_manutencoes = db.execute(
        "SELECT COUNT(*) FROM ordens_servico WHERE proxima_manutencao >= ?", (hoje,)
    ).fetchone()[0]

    stats = {
        'total_clientes': total_clientes,
        'total_equipamentos': total_equipamentos,
        'os_abertas': os_abertas,
        'os_andamento': os_andamento,
        'os_concluidas': os_concluidas,
        'proximas_manutencoes': proximas_manutencoes,
    }
    return render_template('dashboard.html', stats=stats)


# ─────────────────────────────────────────────
#  Rotas — Sprint 2: Empresa
# ─────────────────────────────────────────────
@app.route('/empresa', methods=['GET'])
def empresa_view():
    """Exibe o formulário de cadastro/edição da empresa."""
    db = get_db()
    empresa = db.execute('SELECT * FROM empresa LIMIT 1').fetchone()
    return render_template('empresa.html', empresa=empresa)


@app.route('/empresa', methods=['POST'])
def empresa_save():
    """Salva (insert ou update) os dados da empresa."""
    db = get_db()

    nome      = request.form.get('nome', '').strip()
    documento = request.form.get('documento', '').strip()
    telefone  = request.form.get('telefone', '').strip()
    email     = request.form.get('email', '').strip()
    endereco  = request.form.get('endereco', '').strip()

    # ── Tratamento do upload de logo ──────────
    empresa_atual = db.execute('SELECT * FROM empresa LIMIT 1').fetchone()
    logo_atual    = empresa_atual['logo'] if empresa_atual else None
    logo_filename = logo_atual  # mantém a logo existente por padrão

    arquivo = request.files.get('logo')
    if arquivo and arquivo.filename:
        if not allowed_logo(arquivo.filename):
            flash('Formato de imagem inválido. Use PNG, JPG ou JPEG.', 'warning')
            return redirect(url_for('empresa_view'))

        # Remove a logo anterior do disco se existir
        if logo_atual:
            logo_old_path = os.path.join(LOGOS_DIR, logo_atual)
            if os.path.exists(logo_old_path):
                try:
                    os.remove(logo_old_path)
                except OSError:
                    pass

        safe_name     = secure_filename(arquivo.filename)
        logo_filename = safe_name
        arquivo.save(os.path.join(LOGOS_DIR, logo_filename))

    # ── Upsert: insert ou update ───────────────
    try:
        if empresa_atual:
            db.execute(
                '''UPDATE empresa
                   SET nome=?, documento=?, telefone=?, email=?, endereco=?, logo=?
                   WHERE id=?''',
                (nome, documento, telefone, email, endereco, logo_filename, empresa_atual['id'])
            )
        else:
            db.execute(
                '''INSERT INTO empresa (nome, documento, telefone, email, endereco, logo)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (nome, documento, telefone, email, endereco, logo_filename)
            )
        db.commit()
        flash('Dados da empresa salvos com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao salvar: {e}', 'danger')

    return redirect(url_for('empresa_view'))


# ─────────────────────────────────────────────
#  Rotas — Sprint 3: Clientes
# ─────────────────────────────────────────────
@app.route('/clientes')
def clientes_list():
    """Lista todos os clientes com busca opcional."""
    db    = get_db()
    busca = request.args.get('q', '').strip()

    if busca:
        like  = f'%{busca}%'
        rows  = db.execute(
            '''SELECT * FROM clientes
               WHERE nome LIKE ? OR telefone LIKE ? OR email LIKE ?
               ORDER BY nome COLLATE NOCASE''',
            (like, like, like)
        ).fetchall()
    else:
        rows = db.execute(
            'SELECT * FROM clientes ORDER BY nome COLLATE NOCASE'
        ).fetchall()

    return render_template('clientes.html', clientes=rows, busca=busca)


@app.route('/clientes/novo', methods=['GET'])
def cliente_novo():
    """Exibe o formulário de novo cliente."""
    return render_template('cliente_form.html', cliente=None, acao='novo')


@app.route('/clientes/novo', methods=['POST'])
def cliente_criar():
    """Salva um novo cliente no banco."""
    db   = get_db()
    nome = request.form.get('nome', '').strip()

    if not nome:
        flash('O nome do cliente é obrigatório.', 'warning')
        return redirect(url_for('cliente_novo'))

    telefone    = request.form.get('telefone', '').strip()
    email       = request.form.get('email', '').strip()
    endereco    = request.form.get('endereco', '').strip()
    observacoes = request.form.get('observacoes', '').strip()
    criado_em   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        db.execute(
            '''INSERT INTO clientes (nome, telefone, email, endereco, observacoes, criado_em)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (nome, telefone, email, endereco, observacoes, criado_em)
        )
        db.commit()
        flash(f'Cliente “{nome}” cadastrado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao cadastrar cliente: {e}', 'danger')

    return redirect(url_for('clientes_list'))


@app.route('/clientes/<int:cliente_id>/editar', methods=['GET'])
def cliente_editar(cliente_id):
    """Exibe o formulário de edição de cliente."""
    db      = get_db()
    cliente = db.execute('SELECT * FROM clientes WHERE id = ?', (cliente_id,)).fetchone()
    if cliente is None:
        flash('Cliente não encontrado.', 'warning')
        return redirect(url_for('clientes_list'))
    return render_template('cliente_form.html', cliente=cliente, acao='editar')


@app.route('/clientes/<int:cliente_id>/editar', methods=['POST'])
def cliente_salvar(cliente_id):
    """Salva a edição de um cliente existente."""
    db      = get_db()
    cliente = db.execute('SELECT * FROM clientes WHERE id = ?', (cliente_id,)).fetchone()
    if cliente is None:
        flash('Cliente não encontrado.', 'warning')
        return redirect(url_for('clientes_list'))

    nome = request.form.get('nome', '').strip()
    if not nome:
        flash('O nome do cliente é obrigatório.', 'warning')
        return redirect(url_for('cliente_editar', cliente_id=cliente_id))

    telefone    = request.form.get('telefone', '').strip()
    email       = request.form.get('email', '').strip()
    endereco    = request.form.get('endereco', '').strip()
    observacoes = request.form.get('observacoes', '').strip()

    try:
        db.execute(
            '''UPDATE clientes
               SET nome=?, telefone=?, email=?, endereco=?, observacoes=?
               WHERE id=?''',
            (nome, telefone, email, endereco, observacoes, cliente_id)
        )
        db.commit()
        flash(f'Cliente “{nome}” atualizado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao atualizar cliente: {e}', 'danger')

    return redirect(url_for('clientes_list'))


@app.route('/clientes/<int:cliente_id>/excluir', methods=['POST'])
def cliente_excluir(cliente_id):
    """Exclui um cliente após verificar se não possui vínculos."""
    db      = get_db()
    cliente = db.execute('SELECT * FROM clientes WHERE id = ?', (cliente_id,)).fetchone()
    if cliente is None:
        flash('Cliente não encontrado.', 'warning')
        return redirect(url_for('clientes_list'))

    # Verifica vínculos antes de excluir
    total_equip = db.execute(
        'SELECT COUNT(*) FROM equipamentos WHERE cliente_id = ?', (cliente_id,)
    ).fetchone()[0]
    total_os = db.execute(
        'SELECT COUNT(*) FROM ordens_servico WHERE cliente_id = ?', (cliente_id,)
    ).fetchone()[0]

    if total_equip > 0 or total_os > 0:
        partes = []
        if total_equip: partes.append(f'{total_equip} equipamento(s)')
        if total_os:    partes.append(f'{total_os} ordem(ns) de serviço')
        flash(
            f'Não é possível excluir “{cliente["nome"]}” pois possui '
            + ' e '.join(partes) + ' vinculado(s).',
            'danger'
        )
        return redirect(url_for('clientes_list'))

    try:
        db.execute('DELETE FROM clientes WHERE id = ?', (cliente_id,))
        db.commit()
        flash(f'Cliente “{cliente["nome"]}” excluído com sucesso.', 'success')
    except Exception as e:
        flash(f'Erro ao excluir: {e}', 'danger')

    return redirect(url_for('clientes_list'))


# ─────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 50)
    print("  TecOS Local v1.0 — Sprint 3")
    print("=" * 50)
    init_db()
    print("[TecOS] Iniciando servidor em http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
