CREATE TABLE obra_social (
    id_obra_social SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    cuit VARCHAR(15) UNIQUE,
    contacto VARCHAR(100),
    tipo_validacion VARCHAR(20) NOT NULL DEFAULT 'manual',
    activo BOOLEAN DEFAULT true
);  
