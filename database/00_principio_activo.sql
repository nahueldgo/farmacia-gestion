CREATE TABLE principio_activo (
    id_principio_activo SERIAL PRIMARY KEY,
    nombre VARCHAR(150) UNIQUE NOT NULL
);
