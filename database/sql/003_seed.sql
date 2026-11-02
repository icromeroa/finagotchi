INSERT OR IGNORE INTO plantilla_categorias (nombre, tipo, icono, es_fija, orden) VALUES
 ('Alimentación',        'gasto',   '🍽️', 0,  1),
 ('Transporte',          'gasto',   '🚌',  0,  2),
 ('Familia y detalles',  'gasto',   '🎁',  0,  3),
 ('Ocio y gustos',       'gasto',   '🎉',  0,  4),
 ('Vivienda y fijos',    'gasto',   '🏠',  1,  5),
 ('Suscripciones',       'gasto',   '🍿',  1,  6),
 ('Salud y aseo',        'gasto',   '💊',  0,  7),
 ('Deudas',              'gasto',   '💳',  0,  8),
 ('Finanzas',            'gasto',   '🏦',  0,  9),
 ('Préstamos',           'gasto',   '🤝',  0, 10),
 ('Ahorro e inversión',  'gasto',   '🐷',  0, 11),
 ('Otros',               'gasto',   '📦',  0, 12),
 ('Trabajo',             'ingreso', '💼',  0,  1),
 ('Apoyo familiar',      'ingreso', '👨‍👩‍👧', 0,  2),
 ('Beca',                'ingreso', '🎓',  0,  3),
 ('Otros ingresos',      'ingreso', '✨',  0,  4);

INSERT OR IGNORE INTO plantilla_categoria_palabras (categoria_nombre, tipo, palabra) VALUES
 ('Alimentación','gasto','almuerzo'), ('Alimentación','gasto','desayuno'),
 ('Alimentación','gasto','cena'),     ('Alimentación','gasto','comida'),
 ('Alimentación','gasto','restaurante'), ('Alimentación','gasto','café'),
 ('Alimentación','gasto','cafe'),     ('Alimentación','gasto','empanada'),
 ('Alimentación','gasto','mercado'),  ('Alimentación','gasto','corrientazo'),
 ('Transporte','gasto','transporte'), ('Transporte','gasto','pasaje'),
 ('Transporte','gasto','bus'),        ('Transporte','gasto','transmilenio'),
 ('Transporte','gasto','uber'),       ('Transporte','gasto','taxi'),
 ('Transporte','gasto','viaje'),      ('Transporte','gasto','gasolina'),
 ('Transporte','gasto','parqueadero'),
 ('Ocio y gustos','gasto','cine'),    ('Ocio y gustos','gasto','fiesta'),
 ('Ocio y gustos','gasto','bar'),     ('Ocio y gustos','gasto','cerveza'),
 ('Ocio y gustos','gasto','juego'),   ('Ocio y gustos','gasto','salida'),
 ('Ocio y gustos','gasto','concierto'), ('Ocio y gustos','gasto','helado'),
 ('Salud y aseo','gasto','farmacia'), ('Salud y aseo','gasto','drogueria'),
 ('Salud y aseo','gasto','medicina'), ('Salud y aseo','gasto','medico'),
 ('Salud y aseo','gasto','salud'),    ('Salud y aseo','gasto','gimnasio'),
 ('Vivienda y fijos','gasto','arriendo'), ('Vivienda y fijos','gasto','alquiler'),
 ('Vivienda y fijos','gasto','servicios'), ('Vivienda y fijos','gasto','luz'),
 ('Vivienda y fijos','gasto','agua'),  ('Vivienda y fijos','gasto','gas'),
 ('Vivienda y fijos','gasto','internet'),
 ('Suscripciones','gasto','netflix'),  ('Suscripciones','gasto','spotify'),
 ('Suscripciones','gasto','suscripción'), ('Suscripciones','gasto','suscripcion'),
 ('Trabajo','ingreso','sueldo'),       ('Trabajo','ingreso','salario'),
 ('Trabajo','ingreso','trabajo'),      ('Trabajo','ingreso','quincena'),
 ('Trabajo','ingreso','pagaron'),      ('Trabajo','ingreso','honorarios'),
 ('Apoyo familiar','ingreso','mesada'),('Apoyo familiar','ingreso','apoyo'),
 ('Beca','ingreso','beca');

INSERT OR IGNORE INTO plantilla_cuentas (nombre, tipo_cuenta, icono, es_por_defecto, orden) VALUES
 ('Efectivo',    'efectivo',          '💵', 1, 1),
 ('Nequi',       'billetera_digital', '📱', 0, 2),
 ('Daviplata',   'billetera_digital', '📱', 0, 3),
 ('Nu',          'cuenta_ahorros',    '💜', 0, 4),
 ('Bancolombia', 'cuenta_ahorros',    '🏦', 0, 5);

INSERT OR IGNORE INTO plantilla_cuenta_palabras (cuenta_nombre, palabra) VALUES
 ('Efectivo','efectivo'), ('Efectivo','en efectivo'),
 ('Nequi','nequi'), ('Nequi','por nequi'), ('Nequi','con nequi'),
 ('Daviplata','daviplata'), ('Daviplata','por daviplata'), ('Daviplata','con daviplata'),
 ('Nu','con nu'), ('Nu','por nu'),
 ('Bancolombia','bancolombia'), ('Bancolombia','por bancolombia'), ('Bancolombia','con bancolombia');

INSERT OR REPLACE INTO schema_migrations (version, descripcion, aplicado_en)
VALUES (2, 'Esquema v2 con mensajes por dispositivo, salud auditable y presupuesto historico',
        strftime('%Y-%m-%dT%H:%M:%SZ','now'));
