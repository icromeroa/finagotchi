import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/api/api_client.dart';
import 'package:frontend/api/grabador.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// La interpretacion con el modelo de lenguaje local tarda entre 7 y 15
/// segundos, asi que estas pruebas necesitan mas margen que el de 30 segundos
/// que trae flutter_test por defecto.
const _margen = Timeout(Duration(minutes: 3));

/// Pruebas del cliente de la API contra el backend real.
///
/// Si el backend no esta levantado, las pruebas se saltan con un aviso: es
/// preferible a que fallen y tapen el resto de la suite.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const direccion = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:5000/api/v1',
  );

  late ApiClient cliente;

  setUpAll(() async {
    SharedPreferences.setMockInitialValues({});
    // flutter_test intercepta HttpClient y devuelve 400 en todas las
    // peticiones. Estas pruebas talk to the real backend, so that override is
    // removed here.
    HttpOverrides.global = null;
  });

  setUp(() {
    cliente = ApiClient(direccionBase: direccion);
  });

  Future<bool> backendArriba() async {
    try {
      final peticion = await HttpClient()
          .getUrl(Uri.parse('$direccion/health'))
          .timeout(const Duration(seconds: 3));
      await peticion.close();
      return true;
    } catch (_) {
      return false;
    }
  }

  group('Cliente de la API', () {
    test('el backend responde el estado', () async {
      if (!await backendArriba()) {
        markTestSkipped('El backend no esta levantado en $direccion');
        return;
      }
      final correo =
          'prueba-yo-${DateTime.now().millisecondsSinceEpoch}@finagotchi.local';
      await cliente.registrar('Prueba Yo', correo, 'secreto123');
      final datos = await cliente.yo();
      expect(datos.containsKey('usuario'), isTrue);
    });

    test('registra, consulta el home y confirma un movimiento', () async {
      if (!await backendArriba()) {
        markTestSkipped('El backend no esta levantado en $direccion');
        return;
      }
      final correo =
          'prueba-app-${DateTime.now().millisecondsSinceEpoch}@finagotchi.local';
      final registro = await cliente.registrar('Prueba App', correo, 'secreto123');
      expect(registro['usuario'], isNotNull);
      expect(cliente.haySesion, isTrue);

      final home = await cliente.home();
      final hoy = home['hoy'] as Map<String, dynamic>;
      expect(hoy.containsKey('gastos'), isTrue);
      expect(hoy.containsKey('ingresos'), isTrue);

      final mensaje = await cliente.enviarTexto(
        'gasté 12000 en almuerzo',
        messageId: 'app-test-${DateTime.now().millisecondsSinceEpoch}',
      );
      final transacciones = mensaje['transacciones'] as List<dynamic>;
      expect(transacciones, isNotEmpty);
      expect((transacciones.first as Map<String, dynamic>)['monto'], 12000);

      final id = (mensaje['id'] as num).toInt();
      final confirmado = await cliente.confirmarMensaje(id);
      expect(confirmado['puntos_otorgados'], 1);

      final tras = await cliente.home();
      final hoyTras = tras['hoy'] as Map<String, dynamic>;
      expect((hoyTras['gastos'] as num).toInt(), greaterThanOrEqualTo(12000));
    }, timeout: _margen);

    test('devuelve el error del backend cuando las credenciales son malas',
        () async {
      if (!await backendArriba()) {
        markTestSkipped('El backend no esta levantado en $direccion');
        return;
      }
      await expectLater(
        cliente.login('no-existe@finagotchi.local', 'malaclave'),
        throwsA(isA<ApiError>()),
      );
    });
  });

  group('WAV', () {
    test('la cabecera WAV es valida', () {
      final pcm = Uint8List.fromList(List<int>.filled(16000 * 2, 0));
      final wav = wavDesdePcm(pcm, 16000);
      expect(wav.lengthInBytes, 44 + pcm.lengthInBytes);
      expect(String.fromCharCodes(wav.sublist(0, 4)), 'RIFF');
      expect(String.fromCharCodes(wav.sublist(8, 12)), 'WAVE');
      expect(duracionWav(wav), closeTo(1.0, 0.01));
    });

    test('el WAV generado es aceptado por el backend', () async {
      if (!await backendArriba()) {
        markTestSkipped('El backend no esta levantado en $direccion');
        return;
      }
      final correo =
          'prueba-wav-${DateTime.now().millisecondsSinceEpoch}@finagotchi.local';
      await cliente.registrar('Prueba WAV', correo, 'secreto123');

      final pcm = Uint8List.fromList(List<int>.filled(16000 * 2, 0));
      final wav = wavDesdePcm(pcm, 16000);
      // Con silencio el modelo no devuelve texto y el backend responde
      // STT_SIN_TEXTO. Lo que se comprueba es que el archivo fue aceptado
      // como WAV valido: si el formato estuviera mal, seria AUDIO_INVALIDO.
      try {
        final mensaje = await cliente.enviarAudio(
          wav,
          messageId: 'wav-test-${DateTime.now().millisecondsSinceEpoch}',
          duracion: duracionWav(wav),
        );
        expect(mensaje.containsKey('id'), isTrue);
      } on ApiError catch (e) {
        expect(e.codigo, isNot('AUDIO_INVALIDO'),
            reason: 'El backend rechazo el WAV por formato: ${e.mensaje}');
        expect(e.codigo, 'STT_SIN_TEXTO');
      }
    }, timeout: _margen);
  });
}
