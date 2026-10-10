create table public.auth_flows
(
    id                 uuid primary key default gen_random_uuid(),
    state_hash         text        not null unique,
    browser_nonce_hash text        not null,
    oidc_nonce         text        not null,
    code_verifier      text        not null,
    return_path        text        not null default '/app',
    created_at         timestamptz not null default now(),
    expires_at         timestamptz not null,
    consumed_at        timestamptz,

    constraint auth_flows_valid_expiry
        check (expires_at > created_at)
);

create index auth_flows_expires_at_idx
    on public.auth_flows (expires_at);

alter table public.auth_flows
    enable row level security;