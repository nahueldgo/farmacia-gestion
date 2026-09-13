CREATE TABLE lote (
    id_lote SERIAL PRIMARY KEY, 
    producto_id INT NOT NULL REFERENCES producto(id_producto),
    numero_lote VARCHAR(50) NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    cantidad INT NOT NULL CHECK (cantidad >= 0),
    fecha_creacion TIMESTAMP NOT NULL DEFAULT NOW()
);