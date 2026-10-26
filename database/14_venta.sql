-- Número de comprobante (V-00000001...): la secuencia no repite números aunque haya ventas simultáneas.
CREATE SEQUENCE seq_numero_comprobante;

CREATE TABLE venta (
    id_venta SERIAL PRIMARY KEY,
    numero_comprobante VARCHAR(20) UNIQUE NOT NULL,
    -- La genera el frontend: si reintenta el mismo pedido, no se duplica la venta.
    clave_operacion VARCHAR(36) UNIQUE,
    fecha TIMESTAMP NOT NULL DEFAULT NOW(),
    empleado_id INT NOT NULL REFERENCES empleado(id_empleado),
    cliente_id INT REFERENCES cliente(id_cliente),
    obra_social_id INT REFERENCES obra_social(id_obra_social),
    caja_id INT NOT NULL REFERENCES caja(id_caja),
    medio_pago VARCHAR(20) NOT NULL
        CHECK (medio_pago IN ('efectivo', 'tarjeta_credito', 'tarjeta_debito', 'transferencia', 'qr')),
    subtotal NUMERIC(10,2) NOT NULL,
    monto_cobertura NUMERIC(10,2) DEFAULT 0,
    monto_gravado NUMERIC(10,2) DEFAULT 0,
    monto_exento NUMERIC(10,2) DEFAULT 0,
    total_a_pagar NUMERIC(10,2) NOT NULL,
    receta_verificada BOOLEAN DEFAULT false,
    estado VARCHAR(20) NOT NULL DEFAULT 'confirmada'
        CHECK (estado IN ('confirmada', 'anulada')),
    -- Quién anuló la venta y cuándo: vacíos mientras está confirmada.
    empleado_anulacion_id INT REFERENCES empleado(id_empleado),
    fecha_anulacion TIMESTAMP,
    CHECK (obra_social_id IS NULL OR cliente_id IS NOT NULL),
    CHECK (estado = 'confirmada' OR (empleado_anulacion_id IS NOT NULL AND fecha_anulacion IS NOT NULL))
);
