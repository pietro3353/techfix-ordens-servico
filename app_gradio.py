"""
TechFix Informática — Aplicação de Atendimento (Gradio)
Arquivo: app_gradio.py
Descrição: Interface web responsiva (PC e celular) para abertura de Ordens de Serviço
           integrada ao banco de dados PostgreSQL em nuvem (Supabase).
"""

import os
import re
import gradio as gr
from dotenv import load_dotenv
from supabase import create_client, Client

# Carrega variáveis de ambiente do arquivo .env (sem expor chaves no código)
load_dotenv()

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
CELULAR_REGEX = re.compile(r"^[0-9]{10,13}$")


def obter_cliente_supabase() -> Client:
    """Inicializa e retorna o cliente de conexão com o Supabase."""
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    if not url or not key:
        raise RuntimeError(
            "Credenciais SUPABASE_URL e SUPABASE_KEY não configuradas no ambiente (.env)."
        )
    return create_client(url, key)


def validar_dados(nome, endereco, email, celular, modelo, problema):
    """Valida todos os campos antes de enviar ao banco de dados."""
    nome = (nome or "").strip()
    endereco = (endereco or "").strip()
    email = (email or "").strip().lower()
    celular = (celular or "").strip()
    modelo = (modelo or "").strip()
    problema = (problema or "").strip()

    if not all([nome, endereco, email, celular, modelo, problema]):
        return (
            False,
            "⚠️ Todos os campos são de preenchimento obrigatório. Verifique os dados informados.",
        )

    if len(nome) < 2:
        return False, "⚠️ O nome do cliente deve ter pelo menos 2 caracteres."

    if len(endereco) < 3:
        return False, "⚠️ Informe um endereço válido (mínimo de 3 caracteres)."

    if not EMAIL_REGEX.match(email):
        return (
            False,
            "⚠️ Formato de e-mail inválido. Exemplo válido: cliente@email.com",
        )

    if not CELULAR_REGEX.match(celular):
        return (
            False,
            "⚠️ O campo Celular/WhatsApp deve conter APENAS números (entre 10 e 13 dígitos, ex.: 11987654321).",
        )

    if len(modelo) < 2:
        return False, "⚠️ Informe o modelo do computador ou periférico."

    if len(problema) < 3:
        return False, "⚠️ Descreva o problema apresentado com mais detalhes."

    return True, ""


def cadastrar_ordem_servico(nome, endereco, email, celular, modelo, problema):
    """
    Valida as entradas, verifica se o cliente já existe pelo e-mail (reaproveitando-o
    ou criando um novo registro) e insere a Ordem de Serviço com status inicial 'Aberto'.
    """
    valido, msg_erro = validar_dados(nome, endereco, email, celular, modelo, problema)
    if not valido:
        return msg_erro

    nome = nome.strip()
    endereco = endereco.strip()
    email = email.strip().lower()
    celular = celular.strip()
    modelo = modelo.strip()
    problema = problema.strip()

    try:
        supabase = obter_cliente_supabase()

        # 1. Verifica se já existe um cliente cadastrado com o mesmo e-mail
        consulta_cliente = (
            supabase.table("clientes")
            .select("id, nome")
            .eq("email", email)
            .execute()
        )

        if consulta_cliente.data and len(consulta_cliente.data) > 0:
            cliente_id = consulta_cliente.data[0]["id"]
            info_cliente = f"Cliente existente reaproveitado (ID #{cliente_id})"
        else:
            # Cria um novo cliente
            novo_cliente = (
                supabase.table("clientes")
                .insert(
                    {
                        "nome": nome,
                        "endereco": endereco,
                        "email": email,
                        "celular_whatsapp": celular,
                    }
                )
                .execute()
            )
            if not novo_cliente.data:
                return "❌ Erro ao cadastrar o cliente no banco de dados."
            cliente_id = novo_cliente.data[0]["id"]
            info_cliente = f"Novo cliente cadastrado (ID #{cliente_id})"

        # 2. Cria a Ordem de Serviço vinculada ao cliente com status inicial 'Aberto'
        nova_os = (
            supabase.table("ordens_servico")
            .insert(
                {
                    "cliente_id": cliente_id,
                    "modelo_computador": modelo,
                    "problema_relatado": problema,
                    "status": "Aberto",
                }
            )
            .execute()
        )

        if not nova_os.data:
            return "❌ Erro ao gerar a Ordem de Serviço no banco de dados."

        numero_os = nova_os.data[0]["id"]
        return (
            f"✅ Ordem de Serviço Nº #{numero_os} cadastrada com sucesso! "
            f"| Status inicial: Aberto | {info_cliente}."
        )

    except Exception as exc:
        return (
            "❌ Não foi possível concluir o cadastro no banco de dados. "
            f"Detalhes técnicos: {str(exc)}"
        )


def limpar_campos():
    """Esvazia todos os campos do formulário e a mensagem de status."""
    return "", "", "", "", "", "", ""


# Construção da Interface Responsiva com gr.Blocks
with gr.Blocks(title="TechFix Informática — Abertura de OS") as demo:
    gr.Markdown(
        """
        # 🛠️ TechFix Informática — Recepção e Abertura de OS
        **Instruções de uso:** Preencha os dados do cliente e do equipamento abaixo.
        Caso o e-mail já esteja cadastrado, o sistema reaproveitará automaticamente o cadastro do cliente.
        """
    )

    with gr.Column():
        gr.Markdown("### 👤 Dados do Cliente")
        with gr.Row():
            campo_nome = gr.Textbox(
                label="Nome do Cliente *",
                placeholder="Ex.: Mariana Souza (apenas dados fictícios - LGPD)",
            )
            campo_email = gr.Textbox(
                label="E-mail *",
                placeholder="Ex.: mariana.souza@emailficticio.com.br",
            )

        with gr.Row():
            campo_celular = gr.Textbox(
                label="Celular / WhatsApp (somente números, 10 a 13 dígitos) *",
                placeholder="Ex.: 11987654321",
            )
            campo_endereco = gr.Textbox(
                label="Endereço Completo *",
                placeholder="Ex.: Av. Paulista, 1000 - São Paulo/SP",
            )

        gr.Markdown("### 💻 Dados do Equipamento e Defeito")
        campo_modelo = gr.Textbox(
            label="Modelo do Computador / Periférico *",
            placeholder="Ex.: Notebook Dell Inspiron 15 5510 / PC Gamer Ryzen 5",
        )
        campo_problema = gr.Textbox(
            label="Problema Apresentado *",
            placeholder="Descreva detalhadamente os sintomas relatados pelo cliente...",
            lines=4,
        )

        with gr.Row():
            btn_cadastrar = gr.Button("💾 Cadastrar Ordem de Serviço", variant="primary")
            btn_limpar = gr.Button("🧹 Limpar Campos", variant="secondary")

        saida_resultado = gr.Textbox(
            label="Retorno do Sistema",
            placeholder="O resultado do cadastro e o número da OS aparecerão aqui...",
            interactive=False,
            lines=2,
        )

    btn_cadastrar.click(
        fn=cadastrar_ordem_servico,
        inputs=[
            campo_nome,
            campo_endereco,
            campo_email,
            campo_celular,
            campo_modelo,
            campo_problema,
        ],
        outputs=saida_resultado,
    )

    btn_limpar.click(
        fn=limpar_campos,
        inputs=[],
        outputs=[
            campo_nome,
            campo_endereco,
            campo_email,
            campo_celular,
            campo_modelo,
            campo_problema,
            saida_resultado,
        ],
    )

if __name__ == "__main__":
    # share=True gera um link público temporário (*.gradio.live) para acesso via celular
    demo.launch(share=True)
