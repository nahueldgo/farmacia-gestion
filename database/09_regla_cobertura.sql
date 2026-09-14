CREATE TABLE regla_cobertura (
    id_regla_cobertura SERIAL PRIMARY KEY,
    obra_social_id INT NOT NULL REFERENCES obra_social(id_obra_social),
    categoria_cobertura_obra_social_id INT NOT NULL REFERENCES categoria_cobertura_obra_social(id_categoria_cobertura_obra_social),
    porcentaje_cobertura NUMERIC(5,2) NOT NULL,
    activo BOOLEAN DEFAULT true,
    UNIQUE(obra_social_id, categoria_cobertura_obra_social_id)
);
