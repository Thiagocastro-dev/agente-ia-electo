CREATE schema rag;


set search_path = 'rag';

create table document(
    id bigserial primary key,
    hash varchar(100),
    filename varchar(255),
    state varchar(20),
    num_parts int,
    processed_parts int,
    created_at timestamp not null default current_timestamp,
    updated_at timestamp
);

create table document_part (
    document_id bigint,
    part_id bigserial,
    state varchar(20),
    created_at timestamp not null default current_timestamp,
    updated_at timestamp,
    PRIMARY KEY(document_id,part_id)
);

create table chat_message (
    id bigserial primary key,
    session_id varchar(255) not null,
    sender varchar(20) not null,
    message text not null,
    created_at timestamp not null default current_timestamp
);

create index idx_chat_message_session_id on chat_message(session_id);

create table orders (
    id bigserial primary key,
    session_id varchar(255) not null,
    status varchar(30) not null default 'draft',
    items jsonb not null default '[]'::jsonb,
    delivery_address text,
    freight_cost numeric(10, 2) default 0.00,
    subtotal numeric(10, 2) not null default 0.00,
    total_amount numeric(10, 2) not null default 0.00,
    created_at timestamp with time zone not null default current_timestamp,
    updated_at timestamp with time zone not null default current_timestamp
);

create index idx_orders_session_id on orders(session_id);
