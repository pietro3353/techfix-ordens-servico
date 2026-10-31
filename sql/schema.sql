-- =============================================================================
-- SISTEMA DE ORDENS DE SERVIÇO — TECHFIX INFORMÁTICA
-- Arquivo: sql/schema.sql
-- Descrição: Script DDL para criação das tabelas `clientes` e `ordens_servico`,
--            com chaves primárias, chaves estrangeiras, restrições de integridade
--            (NOT NULL, UNIQUE, CHECK), índices, triggers e políticas RLS.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. TABELA DE CLIENTES (`public.clientes`)
-- Armazena os dados cadastrais dos clientes da loja.
-- O e-mail possui restrição UNIQUE para permitir o reaproveitamento do cadastro
-- quando o mesmo cliente trouxer novos equipamentos no futuro.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.clientes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome TEXT NOT NULL CHECK (char_length(trim(nome)) >= 2),
    endereco TEXT NOT NULL CHECK (char_length(trim(endereco)) >= 3),
    email TEXT NOT NULL UNIQUE,
    celular_whatsapp TEXT NOT NULL,
    data_cadastro TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Validação simples de formato de e-mail (deve conter '@' e '.')
    CONSTRAINT chk_clientes_email_formato
        CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),

    -- Validação do celular/WhatsApp: somente dígitos numéricos, entre 10 e 13 caracteres
    CONSTRAINT chk_clientes_celular_digitos
        CHECK (celular_whatsapp ~ '^[0-9]{10,13}$')
);

-- Comentários descritivos nas colunas de `clientes`
COMMENT ON TABLE public.clientes IS 'Cadastro de clientes da TechFix Informática';
COMMENT ON COLUMN public.clientes.email IS 'E-mail único do cliente usado para identificação e reaproveitamento';
COMMENT ON COLUMN public.clientes.celular_whatsapp IS 'Telefone celular/WhatsApp contendo apenas números (10 a 13 dígitos)';

-- -----------------------------------------------------------------------------
-- 2. TABELA DE ORDENS DE SERVIÇO (`public.ordens_servico`)
-- Armazena os equipamentos recebidos, o defeito relatado e o status do reparo.
-- Relaciona-se com `public.clientes` por meio da chave estrangeira `cliente_id`.
-- Comportamento na exclusão: ON DELETE CASCADE (ao excluir um cliente, suas
-- respectivas ordens de serviço também são removidas de forma consistente).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.ordens_servico (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cliente_id BIGINT NOT NULL,
    modelo_computador TEXT NOT NULL CHECK (char_length(trim(modelo_computador)) >= 2),
    problema_relatado TEXT NOT NULL CHECK (char_length(trim(problema_relatado)) >= 3),
    status TEXT NOT NULL DEFAULT 'Aberto',
    data_abertura TIMESTAMPTZ NOT NULL DEFAULT now(),
    data_atualizacao TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Chave estrangeira referenciando `clientes(id)` com exclusão em cascata
    CONSTRAINT fk_ordens_servico_cliente
        FOREIGN KEY (cliente_id)
        REFERENCES public.clientes (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    -- Restrição CHECK permitindo apenas os 5 status válidos do fluxo de reparo
    CONSTRAINT chk_ordens_servico_status
        CHECK (status IN (
            'Aberto',
            'Em análise',
            'Aguardando peça',
            'Concluído',
            'Entregue'
        ))
);

-- Comentários descritivos nas colunas de `ordens_servico`
COMMENT ON TABLE public.ordens_servico IS 'Ordens de serviço de manutenção de computadores e periféricos';
COMMENT ON COLUMN public.ordens_servico.status IS 'Fluxo: Aberto -> Em análise -> Aguardando peça -> Concluído -> Entregue';

-- -----------------------------------------------------------------------------
-- 3. ÍNDICES PARA OTIMIZAÇÃO DE CONSULTAS E FILTROS
-- Aceleram buscas por cliente_id, status da OS e e-mail do cliente.
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_ordens_servico_cliente_id ON public.ordens_servico (cliente_id);
CREATE INDEX IF NOT EXISTS idx_ordens_servico_status ON public.ordens_servico (status);
CREATE INDEX IF NOT EXISTS idx_clientes_nome ON public.clientes (nome);

-- -----------------------------------------------------------------------------
-- 4. TRIGGER PARA ATUALIZAÇÃO AUTOMÁTICA DE `data_atualizacao`
-- Sempre que uma ordem de serviço for alterada (ex.: mudança de status),
-- atualiza automaticamente a coluna `data_atualizacao` para `now()`.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.fn_atualizar_timestamp_os()
RETURNS TRIGGER AS $$
BEGIN
    NEW.data_atualizacao = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_atualizar_timestamp_os ON public.ordens_servico;

CREATE TRIGGER trg_atualizar_timestamp_os
BEFORE UPDATE ON public.ordens_servico
FOR EACH ROW
EXECUTE FUNCTION public.fn_atualizar_timestamp_os();

-- -----------------------------------------------------------------------------
-- 5. POLÍTICAS DE ACESSO (ROW LEVEL SECURITY - RLS)
-- Habilita RLS e permite as operações CRUD para a chave pública (`anon` /
-- `authenticated`) utilizada pelas aplicações Gradio e Streamlit.
-- -----------------------------------------------------------------------------
ALTER TABLE public.clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ordens_servico ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Permitir acesso completo em clientes" ON public.clientes;
CREATE POLICY "Permitir acesso completo em clientes"
    ON public.clientes
    FOR ALL
    TO anon, authenticated
    USING (true)
    WITH CHECK (true);

DROP POLICY IF EXISTS "Permitir acesso completo em ordens_servico" ON public.ordens_servico;
CREATE POLICY "Permitir acesso completo em ordens_servico"
    ON public.ordens_servico
    FOR ALL
    TO anon, authenticated
    USING (true)
    WITH CHECK (true);
