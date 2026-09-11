CREATE TABLE clase_terapeutica (
    id_clase_terapeutica SERIAL PRIMARY KEY,
    nombre VARCHAR(80) UNIQUE NOT NULL
);