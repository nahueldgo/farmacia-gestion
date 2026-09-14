CREATE TABLE detalle_venta (
    id_detalle_venta SERIAL PRIMARY KEY,
    venta_id INT NOT NULL REFERENCES venta(id_venta) ON DELETE CASCADE,
    producto_id INT NOT NULL REFERENCES producto(id_producto),
    lote_id INT NOT NULL REFERENCES lote(id_lote),
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(10,2) NOT NULL,
    subtotal NUMERIC(10,2) NOT NULL
);
