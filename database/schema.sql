-- ============================================================================
-- PROYECTO: Sistema Multiagente Vital Nativa (Llama 3)
-- MOTOR: PostgreSQL / SQLite Compatible
-- DESCRIPCIÓN: Script DDL y DML inicial para agendamiento, atención,
--              inventario y auditoría de métricas de agentes inteligentes.
-- ============================================================================

-- 1. TABLA DE USUARIOS INTERNOS (ADMINISTRACIÓN Y ESTETICISTAS)
CREATE TABLE usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nombre_completo VARCHAR(120) NOT NULL,
    correo VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(30) NOT NULL CHECK (rol IN ('ADMINISTRADOR', 'ESTETICISTA')),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. TABLA DE CLIENTES / PACIENTES DE VITAL NATIVA
CREATE TABLE clientes (
    id_cliente SERIAL PRIMARY KEY,
    documento VARCHAR(25) UNIQUE,
    nombre_completo VARCHAR(120) NOT NULL,
    telefono VARCHAR(25) NOT NULL,
    correo VARCHAR(100),
    consentimiento_datos BOOLEAN NOT NULL DEFAULT TRUE, -- Cumplimiento Ley 1581 de 2012
    fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. TABLA DE CATÁLOGO DE SERVICIOS ESTÉTICOS Y DE BIENESTAR
CREATE TABLE servicios (
    id_servicio SERIAL PRIMARY KEY,
    codigo_servicio VARCHAR(20) NOT NULL UNIQUE,
    nombre_servicio VARCHAR(120) NOT NULL,
    descripcion TEXT NOT NULL,
    duracion_minutos INT NOT NULL CHECK (duracion_minutos > 0),
    precio_cop DECIMAL(12, 2) NOT NULL CHECK (precio_cop >= 0),
    recomendaciones_previas TEXT,
    disponible BOOLEAN NOT NULL DEFAULT TRUE
);

-- 4. TABLA DE AGENDAMIENTO DE CITAS
CREATE TABLE citas (
    id_cita SERIAL PRIMARY KEY,
    id_cliente INT NOT NULL,
    id_servicio INT NOT NULL,
    fecha_cita DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    estado_cita VARCHAR(25) NOT NULL DEFAULT 'CONFIRMADA'
        CHECK (estado_cita IN ('PENDIENTE', 'CONFIRMADA', 'COMPLETADA', 'CANCELADA', 'REPROGRAMADA')),
    observaciones TEXT,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cita_cliente FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente) ON DELETE RESTRICT,
    CONSTRAINT fk_cita_servicio FOREIGN KEY (id_servicio) REFERENCES servicios (id_servicio) ON DELETE RESTRICT,
    CONSTRAINT uq_agenda_horario UNIQUE (fecha_cita, hora_inicio) -- Evita cruces de horario exactos
);

-- 5. TABLA DE PRODUCTOS E INSUMOS DE INVENTARIO
CREATE TABLE productos_inventario (
    id_producto SERIAL PRIMARY KEY,
    codigo_sku VARCHAR(30) NOT NULL UNIQUE,
    nombre_producto VARCHAR(120) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    unidad_medida VARCHAR(20) NOT NULL,
    stock_actual INT NOT NULL DEFAULT 0 CHECK (stock_actual >= 0),
    stock_minimo INT NOT NULL DEFAULT 5 CHECK (stock_minimo >= 0),
    costo_unitario DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    ultima_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 6. TABLA DE MOVIMIENTOS DE INVENTARIO (KARDEX / TRAZABILIDAD)
CREATE TABLE movimientos_inventario (
    id_movimiento SERIAL PRIMARY KEY,
    id_producto INT NOT NULL,
    id_usuario INT,
    id_cita INT,
    tipo_movimiento VARCHAR(20) NOT NULL CHECK (tipo_movimiento IN ('ENTRADA', 'SALIDA', 'AJUSTE')),
    cantidad INT NOT NULL CHECK (cantidad > 0),
    motivo VARCHAR(255) NOT NULL,
    fecha_movimiento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_mov_producto FOREIGN KEY (id_producto) REFERENCES productos_inventario (id_producto) ON DELETE RESTRICT,
    CONSTRAINT fk_mov_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario) ON DELETE SET NULL,
    CONSTRAINT fk_mov_cita FOREIGN KEY (id_cita) REFERENCES citas (id_cita) ON DELETE SET NULL
);

-- 7. TABLA DE AUDITORÍA Y MÉTRICAS DE DESEMPEÑO DEL SISTEMA MULTIAGENTE
CREATE TABLE logs_ejecucion_agentes (
    id_log SERIAL PRIMARY KEY,
    sesion_id VARCHAR(64) NOT NULL,
    agente_invocado VARCHAR(50) NOT NULL,
    proceso_asociado VARCHAR(40) NOT NULL,
    entrada_usuario TEXT NOT NULL,
    respuesta_agente TEXT NOT NULL,
    tiempo_respuesta_ms INT NOT NULL CHECK (tiempo_respuesta_ms >= 0),
    exito BOOLEAN NOT NULL DEFAULT TRUE,
    codigo_error VARCHAR(50),
    fecha_ejecucion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ÍNDICES PARA OPTIMIZACIÓN DE TIEMPOS DE RESPUESTA
CREATE INDEX idx_citas_fecha_estado ON citas (fecha_cita, estado_cita);
CREATE INDEX idx_clientes_telefono ON clientes (telefono);
CREATE INDEX idx_productos_sku ON productos_inventario (codigo_sku);
CREATE INDEX idx_logs_proceso_fecha ON logs_ejecucion_agentes (proceso_asociado, fecha_ejecucion);

-- ============================================================================
-- CARGA DE DATOS SEMILLA (SEED DATA) PARA VITAL NATIVA
-- ============================================================================

INSERT INTO Servicios (codigo_servicio, nombre_servicio, descripcion, duracion_minutos, precio_cop, recomendaciones_previas) VALUES
('SRV-001', 'Limpieza Facial Profunda Vital', 'Higienización facial con extracción ultrasónica, alta frecuencia y mascarilla hidroplástica calmante.', 60, 95000.00, 'Asistir sin maquillaje y evitar exposición solar intensa 24 horas antes.'),
('SRV-002', 'Masaje Relajante y Descontracturante', 'Terapia manual corporal de bienestar con aceites esenciales naturales y piedras volcánicas.', 60, 110000.00, 'No ingerir alimentos pesados 1 hora antes de la sesión.'),
('SRV-003', 'Hidratación Facial con Ácido Hialurónico', 'Protocolo de nutrición celular profunda para pieles deshidratadas o fatigadas.', 45, 120000.00, 'Informar si presenta alergias cutáneas activas.'),
('SRV-004', 'Drenaje Linfático Corporal', 'Técnica manual suave orientada a la reducción de retención de líquidos y mejora circulatoria.', 50, 100000.00, 'Mantener buena hidratación previa y posterior al procedimiento.');

INSERT INTO productos_inventario (codigo_sku, nombre_producto, categoria, unidad_medida, stock_actual, stock_minimo, costo_unitario) VALUES
('INS-001', 'Gel Conductor Neutro Cabina x 1000ml', 'Aparatología', 'Mililitros', 18, 5, 22000.00),
('INS-002', 'Mascarilla Hidroplástica Calmante x 500g', 'Facial', 'Unidades', 12, 4, 48000.00),
('INS-003', 'Aceite Esencial de Lavanda Orgánico x 250ml', 'Corporal', 'Frascos', 4, 5, 35000.00),
('INS-004', 'Sérum Ácido Hialurónico Profesional x 60ml', 'Facial', 'Frascos', 9, 3, 65000.00),
('INS-005', 'Kit Desechable Bioprotección (Gorros y Sabanillas)', 'Bioseguridad', 'Paquetes', 25, 10, 18000.00);
