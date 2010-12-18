create table runtime (
    id        integer primary key autoincrement not null,
    startTime    date,
    endTime    date
);

create table city (
    id        integer primary key autoincrement not null,
    description text,
    prefix text
);

create table category (
    id        integer primary key autoincrement not null,
    description text,
    prefix text
);

create table listing (
    id        integer primary key autoincrement not null,
    title text,
    name text,
    location text,
    price integer,
    link text,
    description text,
    listingDate    date,
    runtime_id integer,
    city_id integer,
    category_id integer,

    FOREIGN KEY(runtime_id) REFERENCES runtime(id),
    FOREIGN KEY(city_id) REFERENCES city(id),
    FOREIGN KEY(category_id) REFERENCES category(id)
);

create table analyzed (
    id        integer primary key autoincrement not null,
    analyzedDate    date,
    listing_id integer,

    FOREIGN KEY(listing_id) REFERENCES listing(id)
);

