CREATE TABLE medicamento (
    producto_id INT PRIMARY KEY REFERENCES producto(id_producto) ON DELETE CASCADE,
    principio_activo_id INT NOT NULL REFERENCES principio_activo(id_principio_activo),
    concentracion VARCHAR(30) NOT NULL,
    forma_farmaceutica_id INT NOT NULL REFERENCES forma_farmaceutica(id_forma_farmaceutica),
    requiere_receta BOOLEAN DEFAULT false,
    categoria_cobertura_obra_social_id INT REFERENCES categoria_cobertura_obra_social(id_categoria_cobertura_obra_social)
);

