CREATE TABLE medicamento_clase_terapeutica (
    medicamento_id INT NOT NULL REFERENCES medicamento(producto_id) ON DELETE CASCADE,
    clase_terapeutica_id INT NOT NULL REFERENCES clase_terapeutica(id_clase_terapeutica) ON DELETE RESTRICT,
    PRIMARY KEY (medicamento_id, clase_terapeutica_id)
);


