"""
TechFix Informática — Painel Administrativo e Gerencial (Streamlit)
Arquivo: app_streamlit.py
Descrição: Painel web com CRUD completo (Consultar, Cadastrar, Editar/Excluir e Indicadores),
           filtros na barra lateral, exportação CSV (+0,5 bônus) e métricas/gráficos em tempo real.
"""

import os
import re
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client

# Carrega variáveis de ambiente do arquivo .env (caso exista localmente)
load_dotenv()

st.set_page_config(
    page_title="TechFix Informática — Painel do Gerente",
    page_icon="🛠️",
    layout="wide",
)

LISTA_STATUS = [
    "Aberto",
    "Em análise",
    "Aguardando peça",
    "Concluído",
    "Entregue",
]

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
CELULAR_REGEX = re.compile(r"^[0-9]{10,13}$")


def obter_credenciais():
    """Lê as credenciais do Supabase via variáveis de ambiente (.env) ou st.secrets."""
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()

    if not url or not key:
        try:
            url = st.secrets.get("SUPABASE_URL", url).strip()
            key = st.secrets.get("SUPABASE_KEY", key).strip()
        except Exception:
            pass

    return url, key


@st.cache_resource
def conectar_supabase() -> Client:
    """Cria e armazena em cache o cliente do Supabase."""
    url, key = obter_credenciais()
    if not url or not key:
        raise RuntimeError(
            "Credenciais SUPABASE_URL e SUPABASE_KEY não encontradas. "
            "Configure o arquivo .env ou .streamlit/secrets.toml."
        )
    return create_client(url, key)


def carregar_dados_os():
    """Busca todas as Ordens de Serviço com os dados do cliente vinculado."""
    try:
        supabase = conectar_supabase()
        resposta = (
            supabase.table("ordens_servico")
            .select(
                "id, cliente_id, modelo_computador, problema_relatado, status, "
                "data_abertura, data_atualizacao, "
                "clientes(id, nome, email, celular_whatsapp, endereco)"
            )
            .order("id", desc=True)
            .execute()
        )
        registros = []
        for item in resposta.data or []:
            cli = item.get("clientes") or {}
            registros.append(
                {
                    "os_id": item.get("id"),
                    "cliente_id": item.get("cliente_id"),
                    "cliente_nome": cli.get("nome", ""),
                    "cliente_email": cli.get("email", ""),
                    "cliente_celular": cli.get("celular_whatsapp", ""),
                    "cliente_endereco": cli.get("endereco", ""),
                    "modelo_computador": item.get("modelo_computador", ""),
                    "problema_relatado": item.get("problema_relatado", ""),
                    "status": item.get("status", ""),
                    "data_abertura": item.get("data_abertura", ""),
                    "data_atualizacao": item.get("data_atualizacao", ""),
                }
            )
        return pd.DataFrame(registros)
    except Exception as exc:
        st.error(f"❌ Erro ao consultar ordens de serviço no banco: {exc}")
        return pd.DataFrame()


def carregar_clientes():
    """Busca todos os clientes cadastrados."""
    try:
        supabase = conectar_supabase()
        resposta = (
            supabase.table("clientes")
            .select("id, nome, email, celular_whatsapp, endereco, data_cadastro")
            .order("nome")
            .execute()
        )
        return pd.DataFrame(resposta.data or [])
    except Exception as exc:
        st.error(f"❌ Erro ao carregar lista de clientes: {exc}")
        return pd.DataFrame()


# Cabeçalho Principal
st.title("🛠️ TechFix Informática — Painel de Gerenciamento de OS")
st.caption(
    "Sistema administrativo em nuvem (Streamlit + Supabase) para controle de clientes e manutenção."
)

# Carregamento inicial de dados
df_os = carregar_dados_os()
df_clientes = carregar_clientes()

# =============================================================================
# BARRA LATERAL (SIDEBAR) — FILTROS DE BUSCA
# =============================================================================
st.sidebar.header("🔎 Filtros de Busca")
st.sidebar.markdown("Utilize os filtros abaixo para refinar a listagem e a exportação:")

filtro_nome = st.sidebar.text_input(
    "Nome do Cliente", placeholder="Digite parte do nome..."
)
filtro_email = st.sidebar.text_input(
    "E-mail do Cliente", placeholder="Digite parte do e-mail..."
)
filtro_status = st.sidebar.multiselect(
    "Status da Ordem de Serviço",
    options=LISTA_STATUS,
    default=LISTA_STATUS,
)

if st.sidebar.button("🔄 Recarregar Dados", use_container_width=True):
    st.rerun()

# Aplicação dos filtros sobre o DataFrame
df_filtrado = df_os.copy()
if not df_filtrado.empty:
    if filtro_nome.strip():
        df_filtrado = df_filtrado[
            df_filtrado["cliente_nome"].str.contains(
                filtro_nome.strip(), case=False, na=False
            )
        ]
    if filtro_email.strip():
        df_filtrado = df_filtrado[
            df_filtrado["cliente_email"].str.contains(
                filtro_email.strip(), case=False, na=False
            )
        ]
    if filtro_status:
        df_filtrado = df_filtrado[df_filtrado["status"].isin(filtro_status)]
    else:
        df_filtrado = df_filtrado.iloc[0:0]

# =============================================================================
# ORGANIZAÇÃO EM ABAS (st.tabs)
# =============================================================================
aba_consultar, aba_cadastrar, aba_editar_excluir, aba_indicadores = st.tabs(
    [
        "📋 Consultar",
        "➕ Cadastrar",
        "✏️ Editar / Excluir",
        "📊 Indicadores",
    ]
)

# -----------------------------------------------------------------------------
# ABA 1: CONSULTAR + EXPORTAR CSV (BÔNUS +0,5)
# -----------------------------------------------------------------------------
with aba_consultar:
    st.subheader("📋 Ordens de Serviço Cadastradas")
    st.markdown(
        f"Exibindo **{len(df_filtrado)}** de **{len(df_os)}** ordens de serviço conforme os filtros da barra lateral."
    )

    if df_filtrado.empty:
        st.info("Nenhuma Ordem de Serviço encontrada para os filtros selecionados.")
    else:
        st.dataframe(
            df_filtrado.rename(
                columns={
                    "os_id": "Nº OS",
                    "cliente_id": "ID Cliente",
                    "cliente_nome": "Cliente",
                    "cliente_email": "E-mail",
                    "cliente_celular": "Celular/WhatsApp",
                    "cliente_endereco": "Endereço",
                    "modelo_computador": "Equipamento / Modelo",
                    "problema_relatado": "Problema Relatado",
                    "status": "Status",
                    "data_abertura": "Data Abertura",
                    "data_atualizacao": "Última Atualização",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        # Desafio Opcional (+0,5): Botão para exportar os dados filtrados em CSV
        csv_bytes = df_filtrado.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Exportar Dados Filtrados em CSV (ordens_servico_techfix.csv)",
            data=csv_bytes,
            file_name="ordens_servico_techfix.csv",
            mime="text/csv",
            use_container_width=True,
        )

# -----------------------------------------------------------------------------
# ABA 2: CADASTRAR NOVA ORDEM DE SERVIÇO
# -----------------------------------------------------------------------------
with aba_cadastrar:
    st.subheader("➕ Cadastrar Nova Ordem de Serviço pelo Painel")
    st.markdown(
        "Se o e-mail informado já pertencer a um cliente cadastrado, o sistema reaproveitará o registro automaticamente."
    )

    with st.form("form_nova_os", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            novo_nome = st.text_input(
                "Nome do Cliente *", placeholder="Ex.: Carlos Alberto Prado"
            )
            novo_email = st.text_input(
                "E-mail *", placeholder="Ex.: carlos.prado@emailficticio.com.br"
            )
            novo_celular = st.text_input(
                "Celular / WhatsApp (somente dígitos, 10 a 13 números) *",
                placeholder="Ex.: 11977665544",
            )
        with col2:
            novo_endereco = st.text_input(
                "Endereço Completo *", placeholder="Ex.: Rua Augusta, 500 - São Paulo/SP"
            )
            novo_modelo = st.text_input(
                "Modelo do Computador / Periférico *",
                placeholder="Ex.: Notebook Asus VivoBook 15",
            )
            novo_status = st.selectbox(
                "Status Inicial da OS", options=LISTA_STATUS, index=0
            )

        novo_problema = st.text_area(
            "Problema Apresentado / Relato Técnico *",
            placeholder="Descreva o defeito apresentado pelo equipamento...",
        )

        btn_salvar_os = st.form_submit_button(
            "💾 Cadastrar Ordem de Serviço", use_container_width=True
        )

    if btn_salvar_os:
        nome_limpo = novo_nome.strip()
        email_limpo = novo_email.strip().lower()
        celular_limpo = novo_celular.strip()
        endereco_limpo = novo_endereco.strip()
        modelo_limpo = novo_modelo.strip()
        problema_limpo = novo_problema.strip()

        if not all(
            [
                nome_limpo,
                email_limpo,
                celular_limpo,
                endereco_limpo,
                modelo_limpo,
                problema_limpo,
            ]
        ):
            st.warning("⚠️ Preencha todos os campos obrigatórios antes de salvar.")
        elif not EMAIL_REGEX.match(email_limpo):
            st.warning("⚠️ Formato de e-mail inválido.")
        elif not CELULAR_REGEX.match(celular_limpo):
            st.warning(
                "⚠️ O celular/WhatsApp deve conter apenas números (10 a 13 dígitos)."
            )
        else:
            try:
                supabase = conectar_supabase()
                busca_cli = (
                    supabase.table("clientes")
                    .select("id")
                    .eq("email", email_limpo)
                    .execute()
                )
                if busca_cli.data:
                    cid = busca_cli.data[0]["id"]
                else:
                    ins_cli = (
                        supabase.table("clientes")
                        .insert(
                            {
                                "nome": nome_limpo,
                                "endereco": endereco_limpo,
                                "email": email_limpo,
                                "celular_whatsapp": celular_limpo,
                            }
                        )
                        .execute()
                    )
                    cid = ins_cli.data[0]["id"]

                ins_os = (
                    supabase.table("ordens_servico")
                    .insert(
                        {
                            "cliente_id": cid,
                            "modelo_computador": modelo_limpo,
                            "problema_relatado": problema_limpo,
                            "status": novo_status,
                        }
                    )
                    .execute()
                )
                os_criada = ins_os.data[0]["id"]
                st.success(
                    f"✅ Ordem de Serviço Nº #{os_criada} cadastrada com sucesso!"
                )
                st.rerun()
            except Exception as exc:
                st.error(f"❌ Erro ao cadastrar Ordem de Serviço: {exc}")

# -----------------------------------------------------------------------------
# ABA 3: EDITAR / EXCLUIR (ORDENS DE SERVIÇO E CLIENTES)
# -----------------------------------------------------------------------------
with aba_editar_excluir:
    col_ed_os, col_ed_cli = st.columns(2)

    # --- SUBSEÇÃO 3.1: ATUALIZAR E EXCLUIR ORDEM DE SERVIÇO ---
    with col_ed_os:
        st.subheader("🔧 Atualizar ou Excluir Ordem de Serviço")
        if df_os.empty:
            st.info("Não há Ordens de Serviço registradas.")
        else:
            opcoes_os = {
                f"OS #{row['os_id']} — {row['modelo_computador']} ({row['cliente_nome']}) [{row['status']}]": row
                for _, row in df_os.iterrows()
            }
            chave_os_sel = st.selectbox(
                "Selecione a Ordem de Serviço", options=list(opcoes_os.keys())
            )
            os_atual = opcoes_os[chave_os_sel]

            with st.form("form_editar_os"):
                idx_status = (
                    LISTA_STATUS.index(os_atual["status"])
                    if os_atual["status"] in LISTA_STATUS
                    else 0
                )
                status_editado = st.selectbox(
                    "Novo Status da OS", options=LISTA_STATUS, index=idx_status
                )
                modelo_editado = st.text_input(
                    "Modelo do Computador / Periférico",
                    value=os_atual["modelo_computador"],
                )
                problema_editado = st.text_area(
                    "Problema Relatado", value=os_atual["problema_relatado"]
                )
                btn_atualizar_os = st.form_submit_button(
                    "💾 Salvar Alterações da OS", use_container_width=True
                )

            if btn_atualizar_os:
                try:
                    supabase = conectar_supabase()
                    supabase.table("ordens_servico").update(
                        {
                            "status": status_editado,
                            "modelo_computador": modelo_editado.strip(),
                            "problema_relatado": problema_editado.strip(),
                        }
                    ).eq("id", int(os_atual["os_id"])).execute()
                    st.success(
                        f"✅ Ordem de Serviço #{os_atual['os_id']} atualizada para '{status_editado}'!"
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"❌ Erro ao atualizar a Ordem de Serviço: {exc}")

            st.divider()
            st.markdown("#### 🗑️ Excluir Ordem de Serviço")
            confirmar_del_os = st.checkbox(
                f"Confirmo que desejo excluir permanentemente a OS #{os_atual['os_id']}"
            )
            if st.button(
                f"🗑️ Excluir OS #{os_atual['os_id']}",
                type="primary",
                disabled=not confirmar_del_os,
                use_container_width=True,
            ):
                try:
                    supabase = conectar_supabase()
                    supabase.table("ordens_servico").delete().eq(
                        "id", int(os_atual["os_id"])
                    ).execute()
                    st.success(
                        f"✅ Ordem de Serviço #{os_atual['os_id']} excluída com sucesso!"
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"❌ Erro ao excluir a Ordem de Serviço: {exc}")

    # --- SUBSEÇÃO 3.2: EDITAR E EXCLUIR CLIENTE ---
    with col_ed_cli:
        st.subheader("👤 Editar ou Excluir Cliente")
        if df_clientes.empty:
            st.info("Não há clientes cadastrados.")
        else:
            opcoes_cli = {
                f"ID #{row['id']} — {row['nome']} ({row['email']})": row
                for _, row in df_clientes.iterrows()
            }
            chave_cli_sel = st.selectbox(
                "Selecione o Cliente", options=list(opcoes_cli.keys())
            )
            cli_atual = opcoes_cli[chave_cli_sel]

            with st.form("form_editar_cliente"):
                nome_cli_ed = st.text_input(
                    "Nome do Cliente", value=cli_atual["nome"]
                )
                email_cli_ed = st.text_input(
                    "E-mail do Cliente", value=cli_atual["email"]
                )
                celular_cli_ed = st.text_input(
                    "Celular / WhatsApp (somente dígitos)",
                    value=cli_atual["celular_whatsapp"],
                )
                endereco_cli_ed = st.text_input(
                    "Endereço", value=cli_atual["endereco"]
                )
                btn_atualizar_cli = st.form_submit_button(
                    "💾 Atualizar Dados do Cliente", use_container_width=True
                )

            if btn_atualizar_cli:
                if not EMAIL_REGEX.match(email_cli_ed.strip()):
                    st.warning("⚠️ Formato de e-mail inválido.")
                elif not CELULAR_REGEX.match(celular_cli_ed.strip()):
                    st.warning(
                        "⚠️ O celular deve conter apenas números (10 a 13 dígitos)."
                    )
                else:
                    try:
                        supabase = conectar_supabase()
                        supabase.table("clientes").update(
                            {
                                "nome": nome_cli_ed.strip(),
                                "email": email_cli_ed.strip().lower(),
                                "celular_whatsapp": celular_cli_ed.strip(),
                                "endereco": endereco_cli_ed.strip(),
                            }
                        ).eq("id", int(cli_atual["id"])).execute()
                        st.success(
                            f"✅ Dados do cliente '{nome_cli_ed.strip()}' atualizados com sucesso!"
                        )
                        st.rerun()
                    except Exception as exc:
                        st.error(f"❌ Erro ao atualizar cliente: {exc}")

            st.divider()
            st.markdown("#### 🗑️ Excluir Cliente")
            confirmar_del_cli = st.checkbox(
                f"Confirmo que desejo excluir o cliente '{cli_atual['nome']}' (e suas OS vinculadas)"
            )
            if st.button(
                f"🗑️ Excluir Cliente #{cli_atual['id']}",
                type="primary",
                disabled=not confirmar_del_cli,
                use_container_width=True,
            ):
                try:
                    supabase = conectar_supabase()
                    supabase.table("clientes").delete().eq(
                        "id", int(cli_atual["id"])
                    ).execute()
                    st.success(
                        f"✅ Cliente '{cli_atual['nome']}' removido com sucesso!"
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"❌ Erro ao excluir cliente: {exc}")

# -----------------------------------------------------------------------------
# ABA 4: INDICADORES (MÉTRICAS E GRÁFICO POR STATUS)
# -----------------------------------------------------------------------------
with aba_indicadores:
    st.subheader("📊 Indicadores Operacionais da TechFix Informática")

    total_geral = len(df_os)
    contagem_status = {
        status: int((df_os["status"] == status).sum()) if not df_os.empty else 0
        for status in LISTA_STATUS
    }

    cols_metricas = st.columns(6)
    cols_metricas[0].metric("Total de OS", total_geral)
    for idx, status_nome in enumerate(LISTA_STATUS, start=1):
        cols_metricas[idx].metric(status_nome, contagem_status[status_nome])

    st.divider()
    st.markdown("### 📈 Distribuição de Ordens de Serviço por Status")

    df_grafico = pd.DataFrame(
        {
            "Status": LISTA_STATUS,
            "Quantidade de OS": [contagem_status[s] for s in LISTA_STATUS],
        }
    ).set_index("Status")

    st.bar_chart(df_grafico, use_container_width=True)
