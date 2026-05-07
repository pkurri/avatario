create extension if not exists pgcrypto;

create table if not exists public.demo_users (
  id text primary key,
  name text not null,
  email text not null,
  role text not null default 'Product Manager',
  preferences jsonb not null default '{}'::jsonb,
  stats jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.demo_sessions (
  id text primary key,
  user_id text not null references public.demo_users(id) on delete cascade,
  created_at timestamptz not null default now(),
  expires_at timestamptz
);

create table if not exists public.call_logs (
  call_sid text primary key,
  user_id text,
  to_number text,
  from_number text,
  persona_id text,
  context jsonb not null default '{}'::jsonb,
  status text not null,
  direction text not null default 'outbound',
  started_at timestamptz,
  ended_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.call_transcripts (
  id uuid primary key default gen_random_uuid(),
  call_sid text not null references public.call_logs(call_sid) on delete cascade,
  role text not null,
  text text not null,
  audio_url text,
  created_at timestamptz not null default now()
);

create table if not exists public.conversations (
  id text primary key,
  user_id text,
  channel text not null,
  customer_id text,
  customer_name text,
  customer_email text,
  status text not null default 'active',
  priority text,
  assigned_to text,
  tags text[] not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.conversation_messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id text not null references public.conversations(id) on delete cascade,
  sender_type text not null,
  sender_id text,
  recipient_id text,
  message_type text not null default 'text',
  content text not null,
  metadata jsonb not null default '{}'::jsonb,
  read_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists public.mobile_user_settings (
  user_id text primary key,
  settings jsonb not null default '{}'::jsonb,
  call_handling_enabled boolean not null default false,
  clone_llm_id text,
  use_clone_llm boolean not null default false,
  updated_at timestamptz not null default now()
);

create table if not exists public.mobile_push_tokens (
  user_id text not null,
  platform text not null check (platform in ('ios', 'android')),
  push_token text not null,
  updated_at timestamptz not null default now(),
  primary key (user_id, platform)
);

alter table public.demo_users enable row level security;
alter table public.demo_sessions enable row level security;
alter table public.call_logs enable row level security;
alter table public.call_transcripts enable row level security;
alter table public.conversations enable row level security;
alter table public.conversation_messages enable row level security;
alter table public.mobile_user_settings enable row level security;
alter table public.mobile_push_tokens enable row level security;

create policy "service role owns demo users" on public.demo_users
  for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
create policy "service role owns demo sessions" on public.demo_sessions
  for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
create policy "service role owns call logs" on public.call_logs
  for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
create policy "service role owns call transcripts" on public.call_transcripts
  for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
create policy "service role owns conversations" on public.conversations
  for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
create policy "service role owns conversation messages" on public.conversation_messages
  for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
create policy "service role owns mobile settings" on public.mobile_user_settings
  for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
create policy "service role owns mobile push tokens" on public.mobile_push_tokens
  for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
