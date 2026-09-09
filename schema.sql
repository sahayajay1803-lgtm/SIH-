create extension if not exists pgcrypto;

create table if not exists business_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid,
  name text not null,
  industry_category text not null,
  location_district text not null,
  investment_amount numeric not null check (investment_amount >= 0),
  project_stage text not null check (project_stage in ('new_setup', 'expansion', 'operating')),
  employee_count integer not null check (employee_count >= 0),
  created_at timestamptz not null default now()
);

create table if not exists approvals (
  id text primary key,
  name text not null,
  department text not null,
  required_documents jsonb not null default '[]',
  sla_days integer not null,
  dependencies jsonb not null default '[]',
  source text not null,
  active boolean not null default true
);

create table if not exists checklist_items (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references business_profiles(id) on delete cascade,
  approval_id text not null references approvals(id),
  status text not null default 'not_started' check (status in ('not_started', 'in_progress', 'submitted', 'approved', 'rejected')),
  due_at timestamptz,
  created_at timestamptz not null default now(),
  unique(profile_id, approval_id)
);

create table if not exists documents (
  id uuid primary key default gen_random_uuid(),
  checklist_item_id uuid not null references checklist_items(id) on delete cascade,
  storage_path text not null,
  file_name text not null,
  content_type text not null check (content_type in ('application/pdf', 'image/jpeg', 'image/png')),
  metadata jsonb not null default '{}',
  validation_status text not null default 'pending',
  created_at timestamptz not null default now()
);

create table if not exists notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid,
  checklist_item_id uuid references checklist_items(id) on delete cascade,
  channel text not null check (channel in ('in_app', 'email')),
  subject text not null,
  body text not null,
  read_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists checklist_profile_idx on checklist_items(profile_id);
create index if not exists checklist_status_idx on checklist_items(status);
