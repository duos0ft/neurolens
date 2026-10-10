create table public.employee_sessions
(
    id              uuid primary key default gen_random_uuid(),
    session_hash    text        not null unique,
    employee_id     uuid        not null
        references public.employees (user_id)
            on delete cascade,
    created_at      timestamptz not null default now(),
    last_active_at  timestamptz not null default now(),
    expires_at      timestamptz not null,
    revoked_at      timestamptz,

    constraint employee_sessions_valid_expiry
        check (expires_at > created_at)
);

create index employee_sessions_employee_id_idx
    on public.employee_sessions (employee_id);

create index employee_sessions_expires_at_idx
    on public.employee_sessions (expires_at);

alter table public.employee_sessions
    enable row level security;