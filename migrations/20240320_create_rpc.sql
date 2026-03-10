-- Função para deduzir créditos de forma atômica
-- Evita que dois processos deduzam créditos simultâneos resultando em saldo errado
-- Também impede que o saldo fique negativo

create or replace function deduct_credits(p_user_id uuid, p_amount int)
returns boolean
language plpgsql
security definer
as $$
declare
    current_used int;
    current_limit int;
begin
    -- Seleciona com Lock (FOR UPDATE) para garantir exclusividade na transação
    select credits_used, credits_limit into current_used, current_limit
    from public.users
    where id = p_user_id
    for update;

    if not found then
        return false;
    end if;

    -- Verifica se ainda tem saldo
    if (current_used + p_amount) > current_limit then
        return false;
    end if;

    -- Atualiza
    update public.users
    set credits_used = current_used + p_amount,
        updated_at = now()
    where id = p_user_id;

    return true;
end;
$$;
