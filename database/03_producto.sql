CREATE TABLE producto (
    id_producto SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    laboratorio_id INT REFERENCES laboratorio(id_laboratorio),
    precio NUMERIC(10,2) NOT NULL,
    condicion_iva_id INT NOT NULL REFERENCES condicion_iva(id_condicion_iva),
    tipo_producto VARCHAR(20) NOT NULL
        CHECK (tipo_producto IN ('medicamento', 'perfumeria', 'cuidado_personal', 'otro')),
    stock_minimo INT DEFAULT 0,
    activo BOOLEAN DEFAULT true,
    CHECK (tipo_producto <> 'medicamento' OR laboratorio_id IS NOT NULL)
);
