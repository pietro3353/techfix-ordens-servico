# 🛠️ TechFix Informática — Sistema de Ordens de Serviço (Gradio + Supabase + Streamlit)

Solução completa em nuvem para gerenciamento de Ordens de Serviço (OS) e clientes da **TechFix Informática**, integrando **Gradio** (atendimento rápido no balcão/celular), **Streamlit** (painel gerencial com CRUD completo e indicadores) e **Supabase / PostgreSQL** (banco de dados relacional em nuvem).

---

## 📂 Estrutura do Projeto

```text
techfix/
├── sql/
│   └── schema.sql            # Script DDL completo (tabelas, PK, FK, UNIQUE, CHECK, índices e RLS)
├── app_gradio.py             # Interface responsiva de abertura de OS (balcão / mobile)
├── app_streamlit.py          # Painel administrativo do gerente (CRUD em abas + indicadores + CSV)
├── requirements.txt          # Dependências do projeto (gradio, streamlit, supabase, pandas, python-dotenv)
├── .env.example              # Modelo das variáveis de ambiente (sem chaves expostas)
├── .gitignore                # Proteção para não versionar .env nem secrets.toml
├── README.md                 # Documentação de instalação e execução
└── evidencias/               # Capturas de tela das interfaces e das tabelas no Supabase
```

---

## ⚙️ Pré-requisitos e Instalação

### 1. Clonar o repositório e criar o ambiente virtual
```bash
git clone https://github.com/pietro3353/techfix-ordens-servico.git
cd techfix-ordens-servico
python -m venv .venv
# No Windows:
.venv\Scripts\activate
# No Linux/macOS:
source .venv/bin/activate
```

### 2. Instalar as dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar o Banco de Dados no Supabase
1. Crie um projeto gratuito em [supabase.com](https://supabase.com).
2. No menu **SQL Editor**, cole e execute todo o conteúdo do arquivo [`sql/schema.sql`](sql/schema.sql).
3. Em **Project Settings → API**, copie a `Project URL` e a chave `anon` (`public`).

### 4. Configurar as Variáveis de Ambiente
Copie o arquivo `.env.example` para `.env` e preencha com as credenciais do seu projeto:
```bash
cp .env.example .env
```
Edite o arquivo `.env`:
```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-anon-publica
```
*(Opcionalmente, para o Streamlit Cloud, configure as mesmas chaves em `.streamlit/secrets.toml` ou nas configurações de Secrets do painel da nuvem).*

---

## 🚀 Como Executar

### 1. Aplicação de Atendimento (Gradio)
```bash
python app_gradio.py
```
- Acesse localmente em `http://127.0.0.1:7860` ou pelo link público temporário `*.gradio.live` gerado automaticamente (`share=True`) para testar pelo celular.

### 2. Painel de Gerenciamento (Streamlit)
```bash
streamlit run app_streamlit.py
```
- Acesse em `http://localhost:8501`.
- O painel conta com **barra lateral de filtros** (por nome, e-mail e status) e **4 abas**:
  1. **📋 Consultar:** Tabela consolidada de Ordens de Serviço + botão bônus para **Exportar dados filtrados em CSV**.
  2. **➕ Cadastrar:** Inclusão manual de nova OS pelo painel.
  3. **✏️ Editar / Excluir:** Alteração de status da OS, edição de dados cadastrais do cliente e exclusão com caixa de confirmação obrigatória.
  4. **📊 Indicadores:** Métricas (`st.metric`) com o total de OS por status e gráfico de barras (`st.bar_chart`).

---

## 🔒 Segurança e Boas Práticas Implementadas
- **Credenciais Protegidas:** Nenhuma chave de API está exposta no código-fonte (`os.environ` / `python-dotenv` / `st.secrets`).
- **Tratamento de Exceções:** Todas as chamadas ao Supabase utilizam blocos `try/except` com mensagens amigáveis ao usuário.
- **Integridade de Dados:** Validação tanto no front-end (Python/Regex) quanto no banco de dados PostgreSQL (`NOT NULL`, `UNIQUE`, `FOREIGN KEY ON DELETE CASCADE` e `CHECK` para status, formato de e-mail e dígitos de celular).
- **Conformidade LGPD:** Todos os registros de teste utilizam exclusivamente dados fictícios.
