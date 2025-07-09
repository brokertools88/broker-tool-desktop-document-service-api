create table public.documents (
  id uuid not null default extensions.uuid_generate_v4 (),
  file_name text not null,
  original_file_name text not null,
  file_size integer not null,
  file_type text not null,
  file_path text not null,
  document_type text null,
  client_id uuid null,
  insurer_id uuid null,
  uploaded_by text null,
  upload_date timestamp with time zone null default now(),
  last_modified timestamp with time zone null default now(),
  metadata jsonb null default '{}'::jsonb,
  status text null default 'active'::text,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  constraint documents_pkey primary key (id),
  constraint documents_client_id_fkey foreign KEY (client_id) references clients (id),
  constraint documents_insurer_id_fkey foreign KEY (insurer_id) references insurers (id)
) TABLESPACE pg_default;

create index IF not exists idx_documents_client_id on public.documents using btree (client_id) TABLESPACE pg_default;

create index IF not exists idx_documents_insurer_id on public.documents using btree (insurer_id) TABLESPACE pg_default;

create index IF not exists idx_documents_document_type on public.documents using btree (document_type) TABLESPACE pg_default;