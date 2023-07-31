create table if not exists users (
    id serial primary key,
    email text not null unique,
    password text not null,
    active boolean not null default false,
    created_at timestamp default current_timestamp,
    activated_at timestamp
);

create table if not exists tokens (
    id serial primary key,
    token text not null,
    user_id integer not null references users(id) on delete cascade,
    created_at timestamp not null default now()
);

create table if not exists guestbook (
    id serial primary key,
    message text not null,
    user_id integer not null references users(id) on delete cascade,
    private boolean not null default false,
    created_at timestamp not null default now(),
    updated_at timestamp
);

create table if not exists upvotes (
    id serial primary key,
    user_id integer not null references users(id) on delete cascade,
    message_id integer not null references guestbook(id) on delete cascade,
    created_at timestamp not null default now()
);