-- TruthEngine AI Database Schema
-- Run this in Supabase SQL Editor

-- Enable pgvector extension
create extension if not exists vector;

-- Tools table
create table if not exists tools (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    website text,
    category text,
    core_function text,
    pricing_model text,
    free_tier_limits text,
    community_verdict text,
    trust_score float default 0.0,
    tags text[] default '{}',
    created_at timestamp with time zone default now(),
    updated_at timestamp with time zone default now()
);

-- Sources table
create table if not exists sources (
    id uuid primary key default gen_random_uuid(),
    tool_id uuid references tools(id) on delete cascade,
    source_url text not null,
    content text,
    created_at timestamp with time zone default now()
);

-- Reviews table
create table if not exists reviews (
    id uuid primary key default gen_random_uuid(),
    tool_id uuid references tools(id) on delete cascade,
    review_text text,
    sentiment text,
    created_at timestamp with time zone default now()
);

-- Embeddings table (384 dim for all-MiniLM-L6-v2)
create table if not exists embeddings (
    id uuid primary key default gen_random_uuid(),
    tool_id uuid references tools(id) on delete cascade unique,
    embedding vector(384),
    created_at timestamp with time zone default now()
);

-- Index for vector similarity search
create index if not exists embeddings_vector_idx
    on embeddings using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

-- RPC function for vector search
create or replace function match_tools(
    query_embedding vector(384),
    match_count int default 10
)
returns table (
    tool_id uuid,
    similarity float
)
language plpgsql
as $$
begin
    return query
    select
        e.tool_id,
        1 - (e.embedding <=> query_embedding) as similarity
    from embeddings e
    order by e.embedding <=> query_embedding
    limit match_count;
end;
$$;

-- Row-level security (optional, enable if needed)
-- alter table tools enable row level security;
-- alter table sources enable row level security;
-- alter table reviews enable row level security;
-- alter table embeddings enable row level security;
