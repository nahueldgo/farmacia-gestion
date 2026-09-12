CREATE TABLE medicamento (
    producto_id INT PRIMARY KEY REFERENCES producto(id_producto) ON DELETE CASCADE,
    principio_activo VARCHAR(150) NOT NULL,
    concentracion VARCHAR(30) NOT NULL,
    forma_farmaceutica VARCHAR(20) NOT NULL,
    requiere_receta BOOLEAN DEFAULT false,
    categoria_cobertura_obra_social_id INT REFERENCES categoria_cobertura_obra_social(id_categoria_cobertura_obra_social)
);
