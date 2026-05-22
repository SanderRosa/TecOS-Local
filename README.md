# TecOS Local v1.0

> Sistema de gerenciamento de ordens de serviço para assistências técnicas — roda 100% local, sem internet (exceto para carregar Bootstrap via CDN).

---

## 📋 Sobre o Projeto

O **TecOS Local** é um sistema desktop-web que roda no próprio computador da assistência técnica, acessível via navegador em `http://localhost:5000`. Não exige servidores externos, planos pagos ou instalação complexa.

---

## 🚀 Como Iniciar

### Opção 1 — Duplo clique (recomendado)

Execute o arquivo **`iniciar_sistema.bat`**. Ele irá:

1. Verificar se o Python está instalado
2. Criar um ambiente virtual (`venv/`)
3. Instalar as dependências automaticamente
4. Iniciar o servidor Flask
5. Abrir o navegador em `http://localhost:5000`

### Opção 2 — Terminal manual

```bash
# 1. Criar ambiente virtual (somente na primeira vez)
python -m venv venv

# 2. Ativar o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Iniciar o sistema
python app.py
```

---

## 🗂️ Estrutura de Pastas

```
tecos-local/
│
├── app.py                  ← Aplicação Flask principal
├── database.db             ← Banco SQLite (criado automaticamente)
├── requirements.txt        ← Dependências Python
├── iniciar_sistema.bat     ← Script de inicialização (Windows)
├── README.md               ← Este arquivo
│
├── static/
│   ├── css/
│   │   └── style.css       ← Estilos personalizados
│   ├── uploads/            ← Fotos de OS (Sprint futura)
│   └── logos/              ← Logo da empresa (Sprint futura)
│
├── templates/
│   ├── base.html           ← Template base com sidebar e topbar
│   └── dashboard.html      ← Página principal (dashboard)
│
├── relatorios/             ← PDFs gerados (Sprint futura)
└── backups/                ← Backups do banco (Sprint futura)
```

---

## 🗃️ Banco de Dados

O banco **`database.db`** é criado automaticamente na primeira execução com as tabelas:

| Tabela | Descrição |
|---|---|
| `empresa` | Dados da assistência técnica |
| `clientes` | Cadastro de clientes |
| `equipamentos` | Equipamentos vinculados a clientes |
| `ordens_servico` | Ordens de serviço |
| `fotos_os` | Fotos vinculadas às OS |

---

## ✅ Checklist — Sprint 1

- [x] Estrutura inicial do projeto
- [x] `app.py` funcional (Flask)
- [x] Criação automática de pastas
- [x] Criação automática do banco SQLite e tabelas
- [x] Template `base.html` com Bootstrap 5
- [x] Dashboard com 6 cards de estatísticas
- [x] Sidebar com menu completo
- [x] `static/css/style.css` — design profissional
- [x] `requirements.txt`
- [x] `iniciar_sistema.bat`
- [x] `README.md`

---

## 🔄 Sprints Planejadas

| Sprint | Funcionalidades |
|---|---|
| **Sprint 1** ✅ | Estrutura base, banco, dashboard |
| **Sprint 2** | Cadastro de Empresa |
| **Sprint 3** | CRUD de Clientes |
| **Sprint 4** | CRUD de Equipamentos |
| **Sprint 5** | Ordens de Serviço (CRUD + PDF) |
| **Sprint 6** | Upload de Fotos |
| **Sprint 7** | Backup automático |

---

## ⚙️ Requisitos

- **Python** 3.10 ou superior → [python.org](https://www.python.org/downloads/)
- **Navegador** moderno (Chrome, Firefox, Edge)
- Conexão com internet apenas para carregar Bootstrap 5 via CDN

---

## 📌 Notas

- O servidor roda em modo **debug** durante o desenvolvimento. Para produção, desative `debug=True` no `app.py`.
- O banco `database.db` **não** deve ser compartilhado em repositórios públicos (adicione ao `.gitignore`).
