CREATE TABLE condicion_iva (
    id_condicion_iva SERIAL PRIMARY KEY,
    nombre VARCHAR(30) UNIQUE NOT NULL,
    alicuota NUMERIC(5,2) NOT NULL CHECK (alicuota BETWEEN 0 AND 100)
);
