CREATE TABLE producto (
    id_producto SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    laboratorio VARCHAR(150),
    precio NUMERIC(10,2) NOT NULL,
    condicion_iva VARCHAR(20) NOT NULL,
    tipo_producto VARCHAR(20) NOT NULL,
    stock_minimo INT DEFAULT 0,
    activo BOOLEAN DEFAULT true,
    CHECK (tipo_producto <> 'medicamento' OR laboratorio IS NOT NULL)
);
