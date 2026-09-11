CREATE TABLE empleado (
    id_empleado SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    dni VARCHAR(20) UNIQUE NOT NULL,
    rol VARCHAR(30) NOT NULL,
    matricula_profesional VARCHAR(30),
    fecha_ingreso DATE NOT NULL,
    activo BOOLEAN DEFAULT true
);
