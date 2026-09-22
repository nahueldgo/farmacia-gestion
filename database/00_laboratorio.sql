CREATE TABLE laboratorio (
    id_laboratorio SERIAL PRIMARY KEY,
    nombre VARCHAR(150) UNIQUE NOT NULL,
    activo BOOLEAN DEFAULT true
);
