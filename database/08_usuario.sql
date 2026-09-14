CREATE TABLE usuario (
    id_usuario SERIAL PRIMARY KEY,
    empleado_id INT UNIQUE NOT NULL REFERENCES empleado(id_empleado),
    nombre_usuario VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    contrasena_hash VARCHAR(255) NOT NULL,
    activo BOOLEAN DEFAULT true,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT NOW(),
    ultimo_login TIMESTAMP
);
