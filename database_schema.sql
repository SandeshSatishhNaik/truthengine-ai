create extension if not exists vector;

create table tools (
 id uuid primary key default gen_random_uuid(),
 name text,
 website text,
 category text,
 core_function text,
 pricing_model text,
 free_tier_limits text,
 community_verdict text,
 trust_score float,
 source_type text not null default 'submitted',
 created_at timestamp default now()
);

create table sources (
 id uuid primary key default gen_random_uuid(),
 tool_id uuid references tools(id),
 source_url text,
 content text
);

create table reviews (
 id uuid primary key default gen_random_uuid(),
 tool_id uuid references tools(id),
 review_text text,
 sentiment text
);

create table embeddings (
 tool_id uuid references tools(id),
 embedding vector(1536)
);