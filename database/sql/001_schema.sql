PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version      INTEGER PRIMARY KEY,
    descripcion  TEXT NOT NULL,
    aplicado_en  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS plantilla_categorias (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre   TEXT    NOT NULL,
    tipo     TEXT    NOT NULL CHECK (tipo IN ('gasto','ingreso')),
    icono    TEXT    NOT NULL,
    es_fija  INTEGER NOT NULL DEFAULT 0 CHECK (es_fija IN (0,1)),
    orden    INTEGER NOT NULL DEFAULT 0,
    UNIQUE (tipo, nombre)
);

CREATE TABLE IF NOT EXISTS plantilla_categoria_palabras (
    categoria_nombre TEXT NOT NULL,
    tipo             TEXT NOT NULL,
    palabra          TEXT NOT NULL,
    PRIMARY KEY (tipo, categoria_nombre, palabra),
    FOREIGN KEY (tipo, categoria_nombre) REFERENCES plantilla_categorias (tipo, nombre)
);

CREATE TABLE IF NOT EXISTS plantilla_cuentas (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre         TEXT    NOT NULL UNIQUE,
    tipo_cuenta    TEXT    NOT NULL CHECK (tipo_cuenta IN
                       ('efectivo','billetera_digital','tarjeta','cuenta_ahorros','inversion')),
    icono          TEXT    NOT NULL,
    es_por_defecto INTEGER NOT NULL DEFAULT 0 CHECK (es_por_defecto IN (0,1)),
    orden          INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS plantilla_cuenta_palabras (
    cuenta_nombre TEXT NOT NULL REFERENCES plantilla_cuentas (nombre),
    palabra       TEXT NOT NULL,
    PRIMARY KEY (cuenta_nombre, palabra)
);

CREATE TABLE IF NOT EXISTS usuarios (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre             TEXT    NOT NULL CHECK (length(nombre) BETWEEN 1 AND 50),
    nombre_completo    TEXT,
    correo             TEXT    NOT NULL,
    correo_verificado  INTEGER NOT NULL DEFAULT 0 CHECK (correo_verificado IN (0,1)),
    telefono           TEXT,
    proveedor_auth     TEXT    NOT NULL DEFAULT 'correo'
                       CHECK (proveedor_auth IN ('correo','google','apple')),
    proveedor_uid      TEXT,
    password_hash      TEXT,
    presupuesto_diario INTEGER NOT NULL DEFAULT 30000 CHECK (presupuesto_diario >= 0),
    moneda             TEXT    NOT NULL DEFAULT 'COP' CHECK (moneda = 'COP'),
    zona_horaria       TEXT    NOT NULL DEFAULT 'America/Bogota',
    estado             TEXT    NOT NULL DEFAULT 'activo'
                       CHECK (estado IN ('activo','pendiente_eliminacion')),
    ultimo_acceso      TEXT,
    creado_en          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    actualizado_en     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    CHECK (proveedor_auth <> 'correo' OR password_hash IS NOT NULL)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_correo
    ON usuarios (lower(correo));

CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_proveedor
    ON usuarios (proveedor_auth, proveedor_uid)
    WHERE proveedor_uid IS NOT NULL;

CREATE TABLE IF NOT EXISTS consentimientos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    tipo        TEXT    NOT NULL CHECK (tipo IN ('terminos','privacidad','datos_estudio_anonimo')),
    version     TEXT    NOT NULL,
    aceptado    INTEGER NOT NULL CHECK (aceptado IN (0,1)),
    aceptado_en TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE (usuario_id, tipo, version)
);

CREATE TABLE IF NOT EXISTS tokens_recuperacion (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    token_hash  TEXT    NOT NULL,
    expira_en   TEXT    NOT NULL,
    usado_en    TEXT,
    creado_en   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE INDEX IF NOT EXISTS ix_tokens_rec_usuario
    ON tokens_recuperacion (usuario_id, expira_en);

CREATE TABLE IF NOT EXISTS tokens_verificacion_correo (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    token_hash  TEXT    NOT NULL,
    expira_en   TEXT    NOT NULL,
    usado_en    TEXT,
    creado_en   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE INDEX IF NOT EXISTS ix_tokens_verif_usuario
    ON tokens_verificacion_correo (usuario_id, expira_en);

CREATE TABLE IF NOT EXISTS sesiones_refresco (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    token_hash  TEXT    NOT NULL UNIQUE,
    expira_en   TEXT    NOT NULL,
    revocado_en TEXT,
    user_agent  TEXT,
    ip          TEXT,
    creado_en   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE INDEX IF NOT EXISTS ix_sesiones_refresco_usuario
    ON sesiones_refresco (usuario_id, expira_en);

CREATE TABLE IF NOT EXISTS solicitudes_eliminacion_cuenta (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id               INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    solicitada_en            TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    ejecutar_despues_de      TEXT    NOT NULL,
    conservar_datos_anonimos INTEGER NOT NULL DEFAULT 0 CHECK (conservar_datos_anonimos IN (0,1)),
    estado                   TEXT    NOT NULL DEFAULT 'pendiente'
                             CHECK (estado IN ('pendiente','cancelada','ejecutada')),
    resuelta_en              TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_eliminacion_pendiente
    ON solicitudes_eliminacion_cuenta (usuario_id)
    WHERE estado = 'pendiente';

CREATE TABLE IF NOT EXISTS preferencias_notificacion (
    usuario_id                 INTEGER PRIMARY KEY REFERENCES usuarios (id) ON DELETE CASCADE,
    recordatorio_diario_activo INTEGER NOT NULL DEFAULT 1 CHECK (recordatorio_diario_activo IN (0,1)),
    recordatorio_hora          TEXT    NOT NULL DEFAULT '20:00' CHECK (length(recordatorio_hora) = 5),
    avisos_presupuesto         INTEGER NOT NULL DEFAULT 1 CHECK (avisos_presupuesto IN (0,1)),
    avisos_metas               INTEGER NOT NULL DEFAULT 1 CHECK (avisos_metas IN (0,1)),
    avisos_dispositivo         INTEGER NOT NULL DEFAULT 1 CHECK (avisos_dispositivo IN (0,1)),
    modo_silencio              INTEGER NOT NULL DEFAULT 0 CHECK (modo_silencio IN (0,1)),
    silencio_inicio            TEXT    NOT NULL DEFAULT '22:00' CHECK (length(silencio_inicio) = 5),
    silencio_fin               TEXT    NOT NULL DEFAULT '07:00' CHECK (length(silencio_fin) = 5)
);

CREATE TABLE IF NOT EXISTS perfil_financiero (
    usuario_id        INTEGER PRIMARY KEY REFERENCES usuarios (id) ON DELETE CASCADE,
    edad              INTEGER CHECK (edad IS NULL OR edad BETWEEN 15 AND 100),
    genero            TEXT CHECK (genero IN ('mujer','hombre','no_binario','prefiero_no_decir')),
    localidad         TEXT,
    ocupacion         TEXT CHECK (ocupacion IN ('estudio','estudio_y_trabajo','trabajo','otra')),
    nivel_educativo   TEXT,
    con_quien_vive    TEXT CHECK (con_quien_vive IN ('familia','solo','companeros','otra')),
    tiene_ingresos_propios       INTEGER CHECK (tiene_ingresos_propios IN (0,1)),
    ingreso_trabajo_mensual      INTEGER NOT NULL DEFAULT 0 CHECK (ingreso_trabajo_mensual >= 0),
    apoyo_familiar_mensual       INTEGER NOT NULL DEFAULT 0 CHECK (apoyo_familiar_mensual >= 0),
    beca_mensual                 INTEGER NOT NULL DEFAULT 0 CHECK (beca_mensual >= 0),
    otros_ingresos_mensual       INTEGER NOT NULL DEFAULT 0 CHECK (otros_ingresos_mensual >= 0),
    ingreso_total_mensual        INTEGER GENERATED ALWAYS AS
        (ingreso_trabajo_mensual + apoyo_familiar_mensual + beca_mensual + otros_ingresos_mensual) STORED,
    frecuencia_ingreso           TEXT CHECK (frecuencia_ingreso IN ('semanal','quincenal','mensual','irregular')),
    estilo_control               TEXT CHECK (estilo_control IN ('de_memoria','algunas_veces','riguroso')),
    gasto_total_mensual_estimado INTEGER CHECK (gasto_total_mensual_estimado >= 0),
    frecuencia_compras_impulsivas TEXT CHECK (frecuencia_compras_impulsivas IN
                                    ('casi_nunca','a_veces','seguido','siempre')),
    num_suscripciones            INTEGER CHECK (num_suscripciones >= 0),
    gasto_suscripciones_mensual  INTEGER CHECK (gasto_suscripciones_mensual >= 0),
    pedidos_domicilio_mes        INTEGER CHECK (pedidos_domicilio_mes >= 0),
    gasto_domicilios_mensual     INTEGER CHECK (gasto_domicilios_mensual >= 0),
    registros_estimados_semana   INTEGER CHECK (registros_estimados_semana BETWEEN 0 AND 100),
    usa_app_presupuesto          INTEGER CHECK (usa_app_presupuesto IN (0,1)),
    anota_gastos_manual          INTEGER CHECK (anota_gastos_manual IN (0,1)),
    dificultad_llevar_cuentas    INTEGER CHECK (dificultad_llevar_cuentas BETWEEN 1 AND 5),
    tiene_deuda_tarjeta          INTEGER CHECK (tiene_deuda_tarjeta IN (0,1)),
    saldo_deuda_tarjeta          INTEGER CHECK (saldo_deuda_tarjeta >= 0),
    paga_a_cuotas                INTEGER CHECK (paga_a_cuotas IN (0,1)),
    ahorro_mensual               INTEGER CHECK (ahorro_mensual >= 0),
    tiene_fondo_emergencia       INTEGER CHECK (tiene_fondo_emergencia IN (0,1)),
    estres_financiero            INTEGER CHECK (estres_financiero BETWEEN 1 AND 10),
    se_siente_seguro             INTEGER CHECK (se_siente_seguro IN (0,1)),
    actualizado_en               TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS perfil_secciones (
    usuario_id             INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    seccion                TEXT    NOT NULL CHECK (seccion IN
        ('sobre_ti','ingresos','gastos_habitos','como_llevas_cuentas','deudas_ahorro','bienestar')),
    estado                 TEXT    NOT NULL DEFAULT 'pendiente'
                           CHECK (estado IN ('pendiente','en_progreso','completo')),
    preguntas_respondidas  INTEGER NOT NULL DEFAULT 0 CHECK (preguntas_respondidas >= 0),
    actualizado_en         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    PRIMARY KEY (usuario_id, seccion)
);

CREATE TABLE IF NOT EXISTS retos_respuestas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    reto_codigo     TEXT    NOT NULL CHECK (reto_codigo IN ('interes_compuesto','inflacion','diversificacion')),
    opcion_elegida  TEXT    NOT NULL CHECK (opcion_elegida IN ('A','B','C','D')),
    es_correcta     INTEGER NOT NULL CHECK (es_correcta IN (0,1)),
    respondido_en   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE (usuario_id, reto_codigo)
);

CREATE TABLE IF NOT EXISTS dispositivos (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    device_uid            TEXT    NOT NULL UNIQUE,
    usuario_id            INTEGER REFERENCES usuarios (id) ON DELETE SET NULL,
    modelo                TEXT,
    firmware              TEXT,
    mac_address           TEXT,
    token_hash            TEXT,
    token_actualizado_en  TEXT,
    metodo_vinculacion    TEXT CHECK (metodo_vinculacion IN ('qr','pin')),
    vinculado_en          TEXT,
    estado_conexion       TEXT NOT NULL DEFAULT 'desconectado'
                          CHECK (estado_conexion IN ('conectado','sin_conexion','desconectado')),
    estado_dispositivo    TEXT NOT NULL DEFAULT 'reposo'
                          CHECK (estado_dispositivo IN ('reposo','grabando','procesando','transmitiendo','bloqueado')),
    nivel_bateria         INTEGER CHECK (nivel_bateria BETWEEN 0 AND 100),
    ultima_conexion       TEXT,
    ultima_telemetria     TEXT,
    registros_pendientes  INTEGER NOT NULL DEFAULT 0 CHECK (registros_pendientes >= 0),
    creado_en             TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    actualizado_en        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE INDEX IF NOT EXISTS ix_dispositivos_usuario
    ON dispositivos (usuario_id)
    WHERE usuario_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS vinculacion_codigos (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    dispositivo_id       INTEGER NOT NULL REFERENCES dispositivos (id) ON DELETE CASCADE,
    metodo               TEXT    NOT NULL CHECK (metodo IN ('qr','pin')),
    codigo_hash          TEXT    NOT NULL,
    expira_en            TEXT    NOT NULL,
    usado_en             TEXT,
    usado_por_usuario_id INTEGER REFERENCES usuarios (id) ON DELETE SET NULL,
    intentos             INTEGER NOT NULL DEFAULT 0 CHECK (intentos >= 0),
    max_intentos         INTEGER NOT NULL DEFAULT 5 CHECK (max_intentos > 0),
    creado_en            TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE INDEX IF NOT EXISTS ix_vinc_codigos_disp
    ON vinculacion_codigos (dispositivo_id, expira_en);

CREATE TABLE IF NOT EXISTS cuentas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    nombre          TEXT    NOT NULL CHECK (length(nombre) BETWEEN 1 AND 24),
    tipo_cuenta     TEXT    NOT NULL CHECK (tipo_cuenta IN
                      ('efectivo','billetera_digital','tarjeta','cuenta_ahorros','inversion')),
    icono           TEXT,
    ultimos_4       TEXT    CHECK (ultimos_4 IS NULL OR length(ultimos_4) = 4),
    saldo_inicial   INTEGER NOT NULL DEFAULT 0,
    es_sistema      INTEGER NOT NULL DEFAULT 0 CHECK (es_sistema IN (0,1)),
    es_por_defecto  INTEGER NOT NULL DEFAULT 0 CHECK (es_por_defecto IN (0,1)),
    oculta          INTEGER NOT NULL DEFAULT 0 CHECK (oculta IN (0,1)),
    orden           INTEGER NOT NULL DEFAULT 0,
    creado_en       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    actualizado_en  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE (usuario_id, id),
    CHECK (tipo_cuenta <> 'tarjeta' OR saldo_inicial = 0),
    CHECK (NOT (oculta = 1 AND es_por_defecto = 1))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_cuentas_nombre
    ON cuentas (usuario_id, lower(nombre));

CREATE UNIQUE INDEX IF NOT EXISTS ux_cuentas_por_defecto
    ON cuentas (usuario_id)
    WHERE es_por_defecto = 1;

CREATE TABLE IF NOT EXISTS cuenta_palabras (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    cuenta_id   INTEGER NOT NULL,
    palabra     TEXT    NOT NULL CHECK (palabra = lower(palabra) AND length(palabra) BETWEEN 1 AND 40),
    FOREIGN KEY (usuario_id, cuenta_id) REFERENCES cuentas (usuario_id, id) ON DELETE CASCADE,
    UNIQUE (usuario_id, palabra)
);

CREATE INDEX IF NOT EXISTS ix_cuenta_palabras_cuenta
    ON cuenta_palabras (usuario_id, cuenta_id);

CREATE TABLE IF NOT EXISTS categorias (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    nombre      TEXT    NOT NULL CHECK (length(nombre) BETWEEN 1 AND 24),
    tipo        TEXT    NOT NULL CHECK (tipo IN ('gasto','ingreso')),
    icono       TEXT    NOT NULL,
    es_sistema  INTEGER NOT NULL DEFAULT 0 CHECK (es_sistema IN (0,1)),
    es_fija     INTEGER NOT NULL DEFAULT 0 CHECK (es_fija IN (0,1)),
    activa      INTEGER NOT NULL DEFAULT 1 CHECK (activa IN (0,1)),
    orden       INTEGER NOT NULL DEFAULT 0,
    creado_en   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE (usuario_id, id),
    UNIQUE (usuario_id, id, tipo),
    UNIQUE (usuario_id, tipo, nombre)
);

CREATE TABLE IF NOT EXISTS categoria_palabras (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id    INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    categoria_id  INTEGER NOT NULL,
    palabra       TEXT    NOT NULL CHECK (palabra = lower(palabra) AND length(palabra) BETWEEN 1 AND 40),
    FOREIGN KEY (usuario_id, categoria_id) REFERENCES categorias (usuario_id, id) ON DELETE CASCADE,
    UNIQUE (usuario_id, palabra)
);

CREATE INDEX IF NOT EXISTS ix_cat_palabras_cat
    ON categoria_palabras (usuario_id, categoria_id);

CREATE TABLE IF NOT EXISTS metas (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id         INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    nombre             TEXT    NOT NULL CHECK (length(nombre) BETWEEN 1 AND 30),
    icono              TEXT,
    monto_meta         INTEGER NOT NULL CHECK (monto_meta > 0),
    fecha_limite       TEXT    NOT NULL,
    frecuencia_ahorro  TEXT    NOT NULL CHECK (frecuencia_ahorro IN ('diaria','semanal','quincenal','mensual')),
    aporte_periodico   INTEGER NOT NULL CHECK (aporte_periodico > 0),
    dia_aporte         INTEGER CHECK (dia_aporte BETWEEN 1 AND 7),
    hora_recordatorio  TEXT    DEFAULT '08:00',
    prioridad          INTEGER NOT NULL DEFAULT 1 CHECK (prioridad >= 1),
    estado             TEXT    NOT NULL DEFAULT 'activa' CHECK (estado IN ('activa','completada')),
    completada_en      TEXT,
    is_deleted         INTEGER NOT NULL DEFAULT 0 CHECK (is_deleted IN (0,1)),
    deleted_at         TEXT,
    creado_en          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    actualizado_en     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE (usuario_id, id),
    CHECK ((is_deleted = 1) = (deleted_at IS NOT NULL))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_metas_nombre_activa
    ON metas (usuario_id, lower(nombre))
    WHERE is_deleted = 0;

CREATE INDEX IF NOT EXISTS ix_metas_usuario
    ON metas (usuario_id, fecha_limite)
    WHERE is_deleted = 0;

CREATE TABLE IF NOT EXISTS dispositivos_telemetria (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    dispositivo_id    INTEGER REFERENCES dispositivos (id) ON DELETE SET NULL,
    usuario_id        INTEGER REFERENCES usuarios (id) ON DELETE SET NULL,
    message_id        TEXT,
    tipo              TEXT    NOT NULL CHECK (tipo IN ('latido','evento','confirmacion')),
    bateria           INTEGER CHECK (bateria BETWEEN 0 AND 100),
    estado            TEXT,
    boton             INTEGER CHECK (boton IN (0,1)),
    audio_duracion_s  REAL    CHECK (audio_duracion_s IS NULL OR audio_duracion_s BETWEEN 0.5 AND 30),
    payload_json      TEXT,
    recibido_en       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    fecha_local       TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_telemetria_dispositivo
    ON dispositivos_telemetria (dispositivo_id, recibido_en);

CREATE INDEX IF NOT EXISTS ix_telemetria_usuario
    ON dispositivos_telemetria (usuario_id, fecha_local);

CREATE TABLE IF NOT EXISTS mensajes_dispositivo (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id        INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    device_id         INTEGER REFERENCES dispositivos (id) ON DELETE SET NULL,
    device_uid        TEXT    NOT NULL,
    message_id        TEXT    NOT NULL,
    secuencia         INTEGER NOT NULL DEFAULT 1 CHECK (secuencia >= 1),
    origen            TEXT    NOT NULL DEFAULT 'dispositivo'
                      CHECK (origen IN ('dispositivo','app_voz','manual','importacion')),
    texto_transcrito  TEXT,
    duracion_audio_s  REAL    CHECK (duracion_audio_s IS NULL OR duracion_audio_s BETWEEN 0.5 AND 30),
    confianza_ia      REAL    CHECK (confianza_ia IS NULL OR confianza_ia BETWEEN 0 AND 1),
    estado            TEXT    NOT NULL DEFAULT 'recibido'
                      CHECK (estado IN ('recibido','procesado','confirmado','descartado')),
    error             TEXT,
    recibido_en       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    procesado_en      TEXT,
    UNIQUE (usuario_id, message_id),
    UNIQUE (usuario_id, id)
);

CREATE INDEX IF NOT EXISTS ix_mensajes_usuario_fecha
    ON mensajes_dispositivo (usuario_id, recibido_en);

CREATE TABLE IF NOT EXISTS transacciones (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id        INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    mensaje_id        INTEGER,
    device_uid        TEXT,
    secuencia         INTEGER,
    tipo              TEXT    NOT NULL CHECK (tipo IN ('gasto','ingreso','ahorro')),
    monto             INTEGER NOT NULL CHECK (monto > 0),
    categoria_id      INTEGER,
    cuenta_id         INTEGER NOT NULL,
    meta_id           INTEGER,
    concepto          TEXT    CHECK (concepto IS NULL OR length(concepto) <= 255),
    fecha_hora        TEXT    NOT NULL,
    fecha_local       TEXT    NOT NULL,
    origen            TEXT    NOT NULL DEFAULT 'dispositivo'
                      CHECK (origen IN ('dispositivo','app_voz','manual','importacion')),
    texto_transcrito  TEXT,
    confianza_ia      REAL    CHECK (confianza_ia IS NULL OR confianza_ia BETWEEN 0 AND 1),
    estado            TEXT    NOT NULL DEFAULT 'confirmado'
                      CHECK (estado IN ('pendiente','confirmado')),
    version           INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    is_deleted        INTEGER NOT NULL DEFAULT 0 CHECK (is_deleted IN (0,1)),
    deleted_at        TEXT,
    eliminado_via     TEXT    CHECK (eliminado_via IN ('app','voz','deshacer','sistema')),
    confirmado_en     TEXT,
    creado_en         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    actualizado_en    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    FOREIGN KEY (usuario_id, mensaje_id)              REFERENCES mensajes_dispositivo (usuario_id, id),
    FOREIGN KEY (usuario_id, cuenta_id)               REFERENCES cuentas    (usuario_id, id),
    FOREIGN KEY (usuario_id, categoria_id, tipo)      REFERENCES categorias (usuario_id, id, tipo),
    FOREIGN KEY (usuario_id, meta_id)                 REFERENCES metas      (usuario_id, id),
    UNIQUE (usuario_id, id),
    CHECK ((is_deleted = 1) = (deleted_at IS NOT NULL)),
    CHECK (is_deleted = 1 OR eliminado_via IS NULL),
    CHECK (  (tipo = 'ahorro'  AND categoria_id IS NULL)
          OR (tipo <> 'ahorro' AND categoria_id IS NOT NULL AND meta_id IS NULL) )
);

CREATE INDEX IF NOT EXISTS ix_tx_usuario_fecha
    ON transacciones (usuario_id, fecha_local)
    WHERE is_deleted = 0;

CREATE INDEX IF NOT EXISTS ix_tx_usuario_cat_fecha
    ON transacciones (usuario_id, categoria_id, fecha_local)
    WHERE is_deleted = 0;

CREATE INDEX IF NOT EXISTS ix_tx_usuario_cuenta
    ON transacciones (usuario_id, cuenta_id);

CREATE INDEX IF NOT EXISTS ix_tx_usuario_meta
    ON transacciones (usuario_id, meta_id)
    WHERE meta_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_tx_papelera
    ON transacciones (usuario_id, deleted_at)
    WHERE is_deleted = 1;

CREATE INDEX IF NOT EXISTS ix_tx_estado_fecha
    ON transacciones (usuario_id, estado, fecha_local)
    WHERE is_deleted = 0;

CREATE TABLE IF NOT EXISTS transacciones_versiones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id      INTEGER NOT NULL,
    transaccion_id  INTEGER NOT NULL,
    version         INTEGER NOT NULL,
    tipo            TEXT    NOT NULL,
    monto           INTEGER NOT NULL,
    categoria_id    INTEGER,
    cuenta_id       INTEGER NOT NULL,
    meta_id         INTEGER,
    concepto        TEXT,
    fecha_hora      TEXT    NOT NULL,
    fecha_local     TEXT    NOT NULL,
    estado          TEXT    NOT NULL,
    cambiado_por    TEXT    NOT NULL DEFAULT 'app'
                    CHECK (cambiado_por IN ('app','voz','sistema')),
    cambiado_en     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    FOREIGN KEY (usuario_id, transaccion_id) REFERENCES transacciones (usuario_id, id) ON DELETE CASCADE,
    UNIQUE (transaccion_id, version)
);

CREATE INDEX IF NOT EXISTS ix_tx_versiones
    ON transacciones_versiones (usuario_id, transaccion_id);

CREATE TABLE IF NOT EXISTS interacciones_ia (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id     INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    mensaje_id     INTEGER,
    proveedor      TEXT    NOT NULL,
    modelo         TEXT,
    version_prompt TEXT,
    entrada_json   TEXT,
    salida_json    TEXT,
    confianza      REAL    CHECK (confianza IS NULL OR confianza BETWEEN 0 AND 1),
    latencia_ms    INTEGER CHECK (latencia_ms IS NULL OR latencia_ms >= 0),
    tokens_entrada INTEGER CHECK (tokens_entrada IS NULL OR tokens_entrada >= 0),
    tokens_salida  INTEGER CHECK (tokens_salida IS NULL OR tokens_salida >= 0),
    creado_en      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    FOREIGN KEY (usuario_id, mensaje_id) REFERENCES mensajes_dispositivo (usuario_id, id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_interacciones_usuario
    ON interacciones_ia (usuario_id, creado_en);

CREATE TABLE IF NOT EXISTS dispositivos_comandos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    dispositivo_id  INTEGER NOT NULL REFERENCES dispositivos (id) ON DELETE CASCADE,
    usuario_id      INTEGER REFERENCES usuarios (id) ON DELETE SET NULL,
    tipo            TEXT    NOT NULL CHECK (tipo IN
                      ('sincronizar','desvincular','reiniciar','actualizar_firmware','silenciar')),
    payload_json    TEXT,
    estado          TEXT    NOT NULL DEFAULT 'pendiente'
                    CHECK (estado IN ('pendiente','enviado','confirmado','error')),
    idempotency_key TEXT    NOT NULL,
    error           TEXT,
    creado_en       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    enviado_en      TEXT,
    confirmado_en   TEXT,
    UNIQUE (dispositivo_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS ix_comandos_pendientes
    ON dispositivos_comandos (dispositivo_id, estado)
    WHERE estado IN ('pendiente','enviado');

CREATE TABLE IF NOT EXISTS gastos_fijos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id    INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    nombre        TEXT    NOT NULL,
    monto         INTEGER NOT NULL CHECK (monto > 0),
    periodicidad  TEXT    NOT NULL CHECK (periodicidad IN ('semanal','quincenal','mensual','bimestral','anual')),
    dia_pago      INTEGER CHECK (dia_pago BETWEEN 1 AND 31),
    tipo          TEXT    NOT NULL DEFAULT 'gasto' CHECK (tipo = 'gasto'),
    categoria_id  INTEGER NOT NULL,
    cuenta_id     INTEGER,
    activo        INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0,1)),
    creado_en     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    FOREIGN KEY (usuario_id, categoria_id, tipo) REFERENCES categorias (usuario_id, id, tipo),
    FOREIGN KEY (usuario_id, cuenta_id)          REFERENCES cuentas    (usuario_id, id)
);

CREATE INDEX IF NOT EXISTS ix_gastos_fijos_usuario
    ON gastos_fijos (usuario_id)
    WHERE activo = 1;

CREATE TABLE IF NOT EXISTS presupuestos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id     INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    fecha_inicio   TEXT    NOT NULL,
    fecha_fin      TEXT    NOT NULL,
    meses          INTEGER NOT NULL CHECK (meses IN (2,3)),
    aprobado       INTEGER NOT NULL DEFAULT 0 CHECK (aprobado IN (0,1)),
    aprobado_en    TEXT,
    creado_en      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE (usuario_id, id),
    CHECK (fecha_fin > fecha_inicio),
    CHECK ((aprobado = 1) = (aprobado_en IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS ix_presupuestos_usuario
    ON presupuestos (usuario_id, fecha_inicio, fecha_fin);

CREATE TABLE IF NOT EXISTS presupuesto_categoria (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id            INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    presupuesto_id        INTEGER NOT NULL,
    categoria_id          INTEGER NOT NULL,
    tipo                  TEXT    NOT NULL DEFAULT 'gasto' CHECK (tipo = 'gasto'),
    monto_limite_mensual  INTEGER NOT NULL CHECK (monto_limite_mensual >= 0),
    FOREIGN KEY (usuario_id, presupuesto_id)      REFERENCES presupuestos (usuario_id, id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id, categoria_id, tipo)  REFERENCES categorias   (usuario_id, id, tipo),
    UNIQUE (presupuesto_id, categoria_id)
);

CREATE INDEX IF NOT EXISTS ix_presup_cat_usuario
    ON presupuesto_categoria (usuario_id, categoria_id);

CREATE TABLE IF NOT EXISTS presupuesto_diario_historial (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id     INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    fecha_local    TEXT    NOT NULL,
    monto          INTEGER NOT NULL CHECK (monto >= 0),
    motivo         TEXT    NOT NULL CHECK (motivo IN ('inicial','ajuste','importacion')),
    creado_en      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    actualizado_en TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE (usuario_id, fecha_local)
);

CREATE INDEX IF NOT EXISTS ix_presupuesto_diario_usuario
    ON presupuesto_diario_historial (usuario_id, fecha_local);

CREATE TABLE IF NOT EXISTS progreso_etapa (
    usuario_id                  INTEGER PRIMARY KEY REFERENCES usuarios (id) ON DELETE CASCADE,
    etapa_actual                INTEGER NOT NULL DEFAULT 0 CHECK (etapa_actual BETWEEN 0 AND 3),
    dias_diagnostico            INTEGER NOT NULL DEFAULT 28 CHECK (dias_diagnostico BETWEEN 1 AND 60),
    fecha_inicio_diagnostico    TEXT,
    meta_registros              INTEGER CHECK (meta_registros > 0),
    meta_puntos                 INTEGER NOT NULL DEFAULT 100 CHECK (meta_puntos > 0),
    racha_actual                INTEGER NOT NULL DEFAULT 0 CHECK (racha_actual >= 0),
    mejor_racha                 INTEGER NOT NULL DEFAULT 0 CHECK (mejor_racha >= 0),
    etapa1_aprobada_en          TEXT,
    actualizado_en              TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS puntos_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    transaccion_id  INTEGER,
    meta_id         INTEGER,
    fecha_local     TEXT    NOT NULL,
    puntos          INTEGER NOT NULL,
    motivo          TEXT    NOT NULL CHECK (motivo IN
                      ('registro_valido','bonus_semana','bonus_hito','meta_cumplida','ajuste')),
    clave_unica     TEXT,
    detalle_json    TEXT,
    otorgado_en     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    FOREIGN KEY (usuario_id, transaccion_id) REFERENCES transacciones (usuario_id, id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id, meta_id)        REFERENCES metas         (usuario_id, id) ON DELETE SET NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_puntos_una_vez_por_tx
    ON puntos_log (usuario_id, transaccion_id)
    WHERE motivo = 'registro_valido';

CREATE UNIQUE INDEX IF NOT EXISTS ux_puntos_clave
    ON puntos_log (usuario_id, clave_unica)
    WHERE clave_unica IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_puntos_usuario
    ON puntos_log (usuario_id, otorgado_en);

CREATE TABLE IF NOT EXISTS metas_eventos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    meta_id         INTEGER NOT NULL,
    transaccion_id  INTEGER,
    tipo            TEXT    NOT NULL CHECK (tipo IN ('cumplida','atrasada','recordatorio','aporte')),
    periodo_clave   TEXT    NOT NULL,
    puntos          INTEGER NOT NULL DEFAULT 0,
    salud_delta     INTEGER NOT NULL DEFAULT 0,
    detalle_json    TEXT,
    creado_en       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    FOREIGN KEY (usuario_id, meta_id)        REFERENCES metas         (usuario_id, id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id, transaccion_id) REFERENCES transacciones (usuario_id, id) ON DELETE SET NULL,
    UNIQUE (usuario_id, meta_id, tipo, periodo_clave)
);

CREATE INDEX IF NOT EXISTS ix_metas_eventos
    ON metas_eventos (usuario_id, creado_en);

CREATE TABLE IF NOT EXISTS cierres_dia (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id           INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    fecha_local          TEXT    NOT NULL,
    total_ingresos       INTEGER NOT NULL DEFAULT 0,
    total_gastos         INTEGER NOT NULL DEFAULT 0,
    total_ahorrado       INTEGER NOT NULL DEFAULT 0,
    balance_neto         INTEGER NOT NULL,
    presupuesto_diario   INTEGER NOT NULL,
    porcentaje_usado     INTEGER NOT NULL CHECK (porcentaje_usado >= 0),
    calificacion         TEXT    NOT NULL CHECK (calificacion IN ('bien','regular','mal')),
    num_registros        INTEGER NOT NULL DEFAULT 0 CHECK (num_registros >= 0),
    salud_inicio         INTEGER CHECK (salud_inicio BETWEEN 0 AND 100),
    salud_fin            INTEGER CHECK (salud_fin BETWEEN 0 AND 100),
    delta_salud          INTEGER GENERATED ALWAYS AS
                         (CASE WHEN salud_inicio IS NULL OR salud_fin IS NULL THEN NULL ELSE salud_fin - salud_inicio END) STORED,
    version              INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    cerrado_en           TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    recalculado_en       TEXT,
    UNIQUE (usuario_id, fecha_local)
);

CREATE INDEX IF NOT EXISTS ix_cierres_usuario_fecha
    ON cierres_dia (usuario_id, fecha_local);

CREATE TABLE IF NOT EXISTS estado_mascota (
    usuario_id           INTEGER PRIMARY KEY REFERENCES usuarios (id) ON DELETE CASCADE,
    nombre               TEXT    NOT NULL DEFAULT 'Nancy',
    salud                INTEGER NOT NULL DEFAULT 100 CHECK (salud BETWEEN 0 AND 100),
    ultima_actualizacion TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS salud_log (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id       INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    fecha_local      TEXT    NOT NULL,
    regla_codigo     TEXT    NOT NULL,
    motivo           TEXT    NOT NULL CHECK (motivo IN
                       ('cierre_dia','presupuesto_diario','presupuesto_categoria','balance_positivo',
                        'ahorro','inactividad','racha','meta','ajuste')),
    salud_anterior   INTEGER NOT NULL CHECK (salud_anterior BETWEEN 0 AND 100),
    salud_nueva      INTEGER NOT NULL CHECK (salud_nueva BETWEEN 0 AND 100),
    delta            INTEGER GENERATED ALWAYS AS (salud_nueva - salud_anterior) STORED,
    referencia_tipo  TEXT    CHECK (referencia_tipo IS NULL OR referencia_tipo IN
                        ('transaccion','cierre','categoria','meta','sistema')),
    referencia_id    INTEGER,
    detalle_json     TEXT,
    transaccion_id   INTEGER,
    creado_en        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    FOREIGN KEY (usuario_id, transaccion_id) REFERENCES transacciones (usuario_id, id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_salud_regla_dia
    ON salud_log (usuario_id, fecha_local, regla_codigo, COALESCE(referencia_id, 0))
    WHERE referencia_tipo IS NULL OR referencia_tipo <> 'sistema';

CREATE INDEX IF NOT EXISTS ix_salud_log_usuario
    ON salud_log (usuario_id, fecha_local);

CREATE TABLE IF NOT EXISTS alertas_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    tipo            TEXT    NOT NULL CHECK (tipo IN (
        'presupuesto_diario_excedido','presupuesto_categoria_excedido','salud_critica',
        'meta_atrasada','meta_cumplida','racha_en_riesgo','recordatorio_diario',
        'movimiento_registrado','movimiento_editado','movimiento_eliminado',
        'confirmar_entendimiento','registros_agrupados','sincronizacion',
        'bateria_baja','dispositivo_desconectado','dispositivo_vinculado',
        'dispositivo_desvinculado','resumen_semanal','perfil_incompleto')),
    severidad       TEXT    NOT NULL DEFAULT 'info' CHECK (severidad IN ('info','advertencia','critica')),
    titulo          TEXT    NOT NULL,
    mensaje         TEXT,
    fecha_local     TEXT    NOT NULL,
    transaccion_id  INTEGER,
    categoria_id    INTEGER,
    meta_id         INTEGER,
    dispositivo_id  INTEGER REFERENCES dispositivos (id) ON DELETE SET NULL,
    valor_actual    INTEGER,
    valor_limite    INTEGER,
    datos_json      TEXT,
    leida           INTEGER NOT NULL DEFAULT 0 CHECK (leida IN (0,1)),
    leida_en        TEXT,
    is_deleted      INTEGER NOT NULL DEFAULT 0 CHECK (is_deleted IN (0,1)),
    deleted_at      TEXT,
    creado_en       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    FOREIGN KEY (usuario_id, transaccion_id) REFERENCES transacciones (usuario_id, id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id, categoria_id)   REFERENCES categorias    (usuario_id, id),
    FOREIGN KEY (usuario_id, meta_id)        REFERENCES metas         (usuario_id, id),
    CHECK ((is_deleted = 1) = (deleted_at IS NOT NULL)),
    CHECK ((leida = 1) = (leida_en IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS ix_alertas_usuario_fecha
    ON alertas_log (usuario_id, creado_en)
    WHERE is_deleted = 0;

CREATE INDEX IF NOT EXISTS ix_alertas_no_leidas
    ON alertas_log (usuario_id)
    WHERE is_deleted = 0 AND leida = 0;

CREATE UNIQUE INDEX IF NOT EXISTS ux_alertas_dedup
    ON alertas_log (usuario_id, tipo, fecha_local, COALESCE(categoria_id, 0))
    WHERE tipo IN ('presupuesto_diario_excedido','presupuesto_categoria_excedido');

CREATE TABLE IF NOT EXISTS dispositivos_notificaciones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    dispositivo_id  INTEGER NOT NULL REFERENCES dispositivos (id) ON DELETE CASCADE,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    mensaje_id      INTEGER,
    transaccion_id  INTEGER,
    tipo            TEXT    NOT NULL CHECK (tipo IN (
        'movimiento_registrado','movimiento_editado','movimiento_eliminado',
        'registros_agrupados','sincronizacion','bateria_baja',
        'dispositivo_desconectado','dispositivo_vinculado','dispositivo_desvinculado')),
    titulo          TEXT    NOT NULL,
    mensaje         TEXT,
    payload_json    TEXT,
    estado          TEXT    NOT NULL DEFAULT 'pendiente'
                    CHECK (estado IN ('pendiente','entregada','leida')),
    creado_en       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    entregado_en    TEXT,
    leido_en        TEXT,
    FOREIGN KEY (usuario_id, mensaje_id)
        REFERENCES mensajes_dispositivo (usuario_id, id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id, transaccion_id)
        REFERENCES transacciones (usuario_id, id) ON DELETE CASCADE,
    CHECK (
        (estado = 'pendiente' AND entregado_en IS NULL AND leido_en IS NULL)
        OR (estado = 'entregada' AND entregado_en IS NOT NULL AND leido_en IS NULL)
        OR (estado = 'leida' AND entregado_en IS NOT NULL AND leido_en IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS ix_dispositivos_notificaciones_pendientes
    ON dispositivos_notificaciones (dispositivo_id, estado, id);

CREATE INDEX IF NOT EXISTS ix_dispositivos_notificaciones_usuario
    ON dispositivos_notificaciones (usuario_id, creado_en);

CREATE TRIGGER IF NOT EXISTS trg_usuarios_seed
AFTER INSERT ON usuarios
BEGIN
    INSERT INTO perfil_financiero (usuario_id) VALUES (NEW.id);
    INSERT INTO preferencias_notificacion (usuario_id) VALUES (NEW.id);
    INSERT INTO progreso_etapa (usuario_id) VALUES (NEW.id);
    INSERT INTO estado_mascota (usuario_id) VALUES (NEW.id);

    INSERT INTO perfil_secciones (usuario_id, seccion) VALUES
        (NEW.id,'sobre_ti'), (NEW.id,'ingresos'), (NEW.id,'gastos_habitos'),
        (NEW.id,'como_llevas_cuentas'), (NEW.id,'deudas_ahorro'), (NEW.id,'bienestar');

    INSERT INTO categorias (usuario_id, nombre, tipo, icono, es_sistema, es_fija, orden)
        SELECT NEW.id, nombre, tipo, icono, 1, es_fija, orden
        FROM plantilla_categorias
        ORDER BY tipo, orden;

    INSERT INTO categoria_palabras (usuario_id, categoria_id, palabra)
        SELECT NEW.id, c.id, p.palabra
        FROM plantilla_categoria_palabras p
        JOIN categorias c
          ON c.usuario_id = NEW.id AND c.tipo = p.tipo AND c.nombre = p.categoria_nombre;

    INSERT INTO cuentas (usuario_id, nombre, tipo_cuenta, icono, es_sistema, es_por_defecto, orden)
        SELECT NEW.id, nombre, tipo_cuenta, icono, 1, es_por_defecto, orden
        FROM plantilla_cuentas
        ORDER BY orden, id;

    INSERT INTO cuenta_palabras (usuario_id, cuenta_id, palabra)
        SELECT NEW.id, c.id, p.palabra
        FROM plantilla_cuenta_palabras p
        JOIN cuentas c ON c.usuario_id = NEW.id AND c.nombre = p.cuenta_nombre;

    INSERT INTO presupuesto_diario_historial (usuario_id, fecha_local, monto, motivo)
        VALUES (NEW.id, date('now','-5 hours'), NEW.presupuesto_diario, 'inicial');
END;

CREATE TRIGGER IF NOT EXISTS trg_usuarios_budget_hist
AFTER UPDATE OF presupuesto_diario ON usuarios
WHEN OLD.presupuesto_diario IS NOT NEW.presupuesto_diario
BEGIN
    INSERT INTO presupuesto_diario_historial (usuario_id, fecha_local, monto, motivo)
        VALUES (NEW.id, date('now','-5 hours'), NEW.presupuesto_diario, 'ajuste')
        ON CONFLICT (usuario_id, fecha_local)
        DO UPDATE SET monto = excluded.monto,
                      motivo = excluded.motivo,
                      actualizado_en = strftime('%Y-%m-%dT%H:%M:%SZ','now');
END;

CREATE TRIGGER IF NOT EXISTS trg_tx_versionar
AFTER UPDATE OF tipo, monto, categoria_id, meta_id, concepto, fecha_hora, fecha_local ON transacciones
FOR EACH ROW
WHEN OLD.tipo         IS NOT NEW.tipo
  OR OLD.monto        IS NOT NEW.monto
  OR OLD.categoria_id IS NOT NEW.categoria_id
  OR OLD.meta_id      IS NOT NEW.meta_id
  OR OLD.concepto     IS NOT NEW.concepto
  OR OLD.fecha_hora   IS NOT NEW.fecha_hora
  OR OLD.fecha_local  IS NOT NEW.fecha_local
BEGIN
    INSERT INTO transacciones_versiones
        (usuario_id, transaccion_id, version, tipo, monto, categoria_id, cuenta_id, meta_id,
         concepto, fecha_hora, fecha_local, estado)
    VALUES
        (OLD.usuario_id, OLD.id, OLD.version, OLD.tipo, OLD.monto, OLD.categoria_id,
         OLD.cuenta_id, OLD.meta_id, OLD.concepto, OLD.fecha_hora, OLD.fecha_local, OLD.estado);
    UPDATE transacciones SET version = OLD.version + 1 WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_dispositivos_fabrica
AFTER UPDATE OF usuario_id ON dispositivos
WHEN NEW.usuario_id IS NULL AND OLD.usuario_id IS NOT NULL
BEGIN
    UPDATE dispositivos
       SET vinculado_en = NULL,
           metodo_vinculacion = NULL,
           token_hash = NULL,
           token_actualizado_en = NULL,
           estado_conexion = 'desconectado',
           registros_pendientes = 0,
           actualizado_en = strftime('%Y-%m-%dT%H:%M:%SZ','now')
     WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_tx_usuario_inmutable
BEFORE UPDATE OF usuario_id ON transacciones
WHEN OLD.usuario_id <> NEW.usuario_id
BEGIN
    SELECT RAISE(ABORT, 'usuario_id es inmutable en transacciones');
END;

CREATE TRIGGER IF NOT EXISTS trg_cuentas_usuario_inmutable
BEFORE UPDATE OF usuario_id ON cuentas
WHEN OLD.usuario_id <> NEW.usuario_id
BEGIN
    SELECT RAISE(ABORT, 'usuario_id es inmutable en cuentas');
END;

CREATE TRIGGER IF NOT EXISTS trg_categorias_usuario_inmutable
BEFORE UPDATE OF usuario_id ON categorias
WHEN OLD.usuario_id <> NEW.usuario_id
BEGIN
    SELECT RAISE(ABORT, 'usuario_id es inmutable en categorias');
END;

CREATE TRIGGER IF NOT EXISTS trg_metas_usuario_inmutable
BEFORE UPDATE OF usuario_id ON metas
WHEN OLD.usuario_id <> NEW.usuario_id
BEGIN
    SELECT RAISE(ABORT, 'usuario_id es inmutable en metas');
END;

CREATE TRIGGER IF NOT EXISTS trg_categorias_sistema_bloqueada
BEFORE UPDATE OF nombre, tipo ON categorias
WHEN OLD.es_sistema = 1 AND (NEW.nombre <> OLD.nombre OR NEW.tipo <> OLD.tipo)
BEGIN
    SELECT RAISE(ABORT, 'Las categorias predeterminadas no se pueden renombrar');
END;

CREATE TRIGGER IF NOT EXISTS trg_tx_puntos_insert
AFTER INSERT ON transacciones
FOR EACH ROW
WHEN NEW.estado = 'confirmado' AND NEW.is_deleted = 0
BEGIN
    INSERT OR IGNORE INTO puntos_log
        (usuario_id, transaccion_id, fecha_local, puntos, motivo, detalle_json)
    VALUES
        (NEW.usuario_id, NEW.id, NEW.fecha_local, 1, 'registro_valido', '{"origen":"transaccion"}');
END;

CREATE TRIGGER IF NOT EXISTS trg_tx_puntos_confirm
AFTER UPDATE OF estado ON transacciones
FOR EACH ROW
WHEN NEW.estado = 'confirmado' AND NEW.is_deleted = 0 AND OLD.estado <> 'confirmado'
BEGIN
    INSERT OR IGNORE INTO puntos_log
        (usuario_id, transaccion_id, fecha_local, puntos, motivo, detalle_json)
    VALUES
        (NEW.usuario_id, NEW.id, NEW.fecha_local, 1, 'registro_valido', '{"origen":"transaccion"}');
END;
