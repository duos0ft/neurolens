create table public.employees
(
    user_id      uuid primary key references auth.users (id) on delete cascade,
    role         text        not null default 'employee'
        check (role in ('admin', 'employee')),
    status       text        not null default 'active'
        check (status in ('active', 'suspended')),
    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now()
);

create trigger employees_updated_at
    before update on public.employees
    for each row
    execute function public.set_updated_at();


alter table public.employees
    enable row level security;

create policy "Employees can read their own record"
on public.employees
for select
               to authenticated
               using (
               (select auth.uid()) = user_id
               );

alter table public.employees
    add column auth0_user_id text unique;

select
    user_id,
    auth0_user_id,
    role,
    status
from public.employees
where role = 'admin';

update public.employees
set auth0_user_id = 'YOUR_AUTH0_USER_ID'
where user_id = 'YOUR_EMPLOYEE_UUID'
  and role = 'admin'
  and auth0_user_id is null
    returning user_id, auth0_user_id, role, status;

