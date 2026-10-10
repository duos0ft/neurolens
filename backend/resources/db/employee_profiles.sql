create table public.employee_profiles
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

-- RLS
alter table public.employee_profiles
    enable row level security;

create policy "Employees can view their own profile"
on public.employee_profiles
for select
               to authenticated
               using ((select auth.uid()) = user_id);

create policy "Employees can create their own profile"
on public.employee_profiles
for insert
to authenticated
with check ((select auth.uid()) = user_id);

create policy "Employees can update their own profile"
on public.employee_profiles
for update
                      to authenticated
                      using ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);

create policy "Employees can delete their own profile"
on public.employee_profiles
for delete
to authenticated
using ((select auth.uid()) = user_id);

alter table public.employee_profiles
drop constraint employee_profile_user_id_fkey;

alter table public.employee_profiles
    add constraint employee_profiles_user_id_fkey
        foreign key (user_id)
            references public.employees (user_id)
            on delete cascade;