-- SQL script to create the patients table
CREATE TABLE pacientes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre_completo VARCHAR(255) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    correo VARCHAR(255) NOT NULL,
    telefono VARCHAR(15),
    fecha_ultima_cita DATE,
    diagnostico TEXT
);

-- Sample data insertion
INSERT INTO pacientes (nombre_completo, fecha_nacimiento, correo, telefono, fecha_ultima_cita, diagnostico) VALUES
('Juan Perez', '1985-06-15', 'juan.perez@example.com', '1234567890', '2023-10-01', 'Gripe'),
('Maria Lopez', '1990-12-22', 'maria.lopez@example.com', '0987654321', '2023-09-15', 'Consulta general'),
('Carlos Sanchez', '1978-03-30', 'carlos.sanchez@example.com', '1122334455', '2023-08-20', 'Control de diabetes'),
('Ana Garcia', '2000-01-10', 'ana.garcia@example.com', '5566778899', '2023-07-05', 'Chequeo anual');
