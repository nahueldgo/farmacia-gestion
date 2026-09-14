CREATE TABLE movimiento_caja (
    id_movimiento_caja SERIAL PRIMARY KEY,
    caja_id INT NOT NULL REFERENCES caja(id_caja),
    empleado_id INT NOT NULL REFERENCES empleado(id_empleado),
    tipo VARCHAR(20) NOT NULL,
    monto NUMERIC(10,2) NOT NULL,
    motivo VARCHAR(200) NOT NULL,
    hora TIMESTAMP NOT NULL DEFAULT NOW()
);
