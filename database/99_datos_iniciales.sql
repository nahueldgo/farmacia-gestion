-- Categorias de cobertura del PMO
INSERT INTO categoria_cobertura_obra_social (nombre) VALUES
    ('ambulatorio'),
    ('cronico'),
    ('diabetes_insulina'),
    ('oncologico'),
    ('anticonceptivos'),
    ('hiv'),
    ('discapacidad')
ON CONFLICT (nombre) DO NOTHING;

-- Condiciones de IVA (alicuota en %)
INSERT INTO condicion_iva (nombre, alicuota) VALUES
    ('exento', 0),
    ('gravado_21', 21),
    ('gravado_10_5', 10.5)
ON CONFLICT (nombre) DO NOTHING;

-- Formas farmaceuticas más comunes
INSERT INTO forma_farmaceutica (nombre) VALUES
    ('Comprimido'),
    ('Cápsula'),
    ('Jarabe'),
    ('Suspensión'),
    ('Solución inyectable'),
    ('Ampolla'),
    ('Crema'),
    ('Gel'),
    ('Pomada'),
    ('Gotas'),
    ('Óvulo'),
    ('Supositorio'),
    ('Aerosol'),
    ('Parche')
ON CONFLICT (nombre) DO NOTHING;
