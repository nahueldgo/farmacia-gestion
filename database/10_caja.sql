CREATE TABLE caja (
    id_caja SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    empleado_apertura_id INT NOT NULL REFERENCES empleado(id_empleado),
    hora_apertura TIMESTAMP NOT NULL,
    monto_apertura NUMERIC(10,2) NOT NULL,
    empleado_cierre_id INT REFERENCES empleado(id_empleado),
    hora_cierre TIMESTAMP,
    monto_cierre_declarado NUMERIC(10,2),
    monto_cierre_sistema NUMERIC(10,2),
    diferencia NUMERIC(10,2),
    estado VARCHAR(20) NOT NULL DEFAULT 'abierta'
        CHECK (estado IN ('abierta', 'cerrada'))
);

-- Solo puede haber una caja abierta a la vez (la base lo garantiza aunque dos pedidos lleguen juntos).
CREATE UNIQUE INDEX uq_una_caja_abierta ON caja (estado) WHERE estado = 'abierta';
