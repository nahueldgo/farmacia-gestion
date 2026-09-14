CREATE TABLE venta (
    id_venta SERIAL PRIMARY KEY,
    numero_comprobante VARCHAR(20) UNIQUE NOT NULL,
    fecha TIMESTAMP NOT NULL DEFAULT NOW(),
    empleado_id INT NOT NULL REFERENCES empleado(id_empleado),
    cliente_id INT REFERENCES cliente(id_cliente),
    obra_social_id INT REFERENCES obra_social(id_obra_social),
    caja_id INT NOT NULL REFERENCES caja(id_caja),
    medio_pago VARCHAR(20) NOT NULL,
    subtotal NUMERIC(10,2) NOT NULL,
    monto_cobertura NUMERIC(10,2) DEFAULT 0,
    monto_gravado NUMERIC(10,2) DEFAULT 0,
    monto_exento NUMERIC(10,2) DEFAULT 0,
    total_a_pagar NUMERIC(10,2) NOT NULL,
    receta_verificada BOOLEAN DEFAULT false,
    estado VARCHAR(20) NOT NULL DEFAULT 'confirmada',
    CHECK (obra_social_id IS NULL OR cliente_id IS NOT NULL)
);
