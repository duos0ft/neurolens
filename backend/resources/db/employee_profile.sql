create table public.employee_profile
(
    user_id               uuid primary key references auth.users (id) on delete cascade,
    display_name          text,
    timezone              text        not null default 'UTC',
    directness            text        not null default 'balanced'
        check (directness in ('low', 'balanced', 'high')),
    response_length       text        not null default 'medium'
        check (response_length in ('short', 'medium', 'detailed')),
    highlight_ambiguity   boolean     not null default true,
    step_by_step_guidance boolean     not null default true,
    always_show_next_step boolean     not null default true,
    created_at            timestamptz not null default now(),
    updated_at            timestamptz not null default now()
);