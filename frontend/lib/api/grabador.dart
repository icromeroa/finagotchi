import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:record/record.dart';

/// Grabador de voz que produce el WAV que espera el backend.
///
/// El backend solo acepta WAV de 16 kHz, mono y 16 bits. Por eso se graba
/// PCM crudo con esos parametros y aqui se envelopa en la cabecera WAV.
///
/// En web el navegador solo ofrece webm/opus, que el backend no acepta: en ese
/// caso [puedeGrabar] es false y la app ofrece escribir la frase a mano.
class GrabadorVoz {
  GrabadorVoz({this.muestraRate = 16000, this.duracionMaxima = 40});

  final int muestraRate;
  final int duracionMaxima;

  final AudioRecorder _grabador = AudioRecorder();
  StreamSubscription<Uint8List>? _suscripcion;
  final List<Uint8List> _trozos = [];
  bool _grabando = false;

  bool get grabando => _grabando;

  /// True si la plataforma puede entregar PCM de 16 kHz.
  bool get puedeGrabar => !kIsWeb;

  Future<void> iniciar() async {
    if (_grabando) return;
    if (!puedeGrabar) {
      throw StateError(
        'La grabacion de voz no esta disponible en web. Escribe la frase a mano.',
      );
    }
    _trozos.clear();
    final flujo = await _grabador.startStream(
      const RecordConfig(
        encoder: AudioEncoder.pcm16bits,
        sampleRate: 16000,
        numChannels: 1,
      ),
    );
    _suscripcion = flujo.listen(_trozos.add);
    _grabando = true;
  }

  /// Detiene la grabacion y devuelve el WAV listo para enviar.
  Future<Uint8List> detener() async {
    if (!_grabando) return Uint8List(0);
    await _grabador.stop();
    await _suscripcion?.cancel();
    _suscripcion = null;
    _grabando = false;
    final total = _trozos.fold<int>(0, (suma, t) => suma + t.lengthInBytes);
    final pcm = Uint8List(total);
    var offset = 0;
    for (final trozo in _trozos) {
      pcm.setRange(offset, offset + trozo.lengthInBytes, trozo);
      offset += trozo.lengthInBytes;
    }
    return wavDesdePcm(pcm, muestraRate);
  }

  Future<void> cancelar() async {
    if (!_grabando) return;
    await _grabador.cancel();
    await _suscripcion?.cancel();
    _suscripcion = null;
    _grabando = false;
  }

  void dispose() {
    _suscripcion?.cancel();
    _grabador.dispose();
  }
}

/// Envolve un PCM de 16 bits mono en un archivo WAV completo.
Uint8List wavDesdePcm(Uint8List pcm, int muestraRate) {
  const bytesPorMuestra = 2;
  final numeroBytes = pcm.lengthInBytes;

  final cabecera = ByteData(44);
  void escribirTexto(int offset, String texto) {
    for (var i = 0; i < texto.length; i++) {
      cabecera.setUint8(offset + i, texto.codeUnitAt(i));
    }
  }

  escribirTexto(0, 'RIFF');
  cabecera.setUint32(4, 36 + numeroBytes, Endian.little);
  escribirTexto(8, 'WAVE');
  escribirTexto(12, 'fmt ');
  cabecera.setUint32(16, 16, Endian.little); // tamaño del bloque fmt
  cabecera.setUint16(20, 1, Endian.little); // PCM sin comprimir
  cabecera.setUint16(22, 1, Endian.little); // un canal
  cabecera.setUint32(24, muestraRate, Endian.little);
  cabecera.setUint32(28, muestraRate * bytesPorMuestra, Endian.little);
  cabecera.setUint16(32, bytesPorMuestra, Endian.little);
  cabecera.setUint16(34, 16, Endian.little); // bits por muestra
  escribirTexto(36, 'data');
  cabecera.setUint32(40, numeroBytes, Endian.little);

  final salida = Uint8List(44 + numeroBytes);
  salida.setRange(0, 44, cabecera.buffer.asUint8List());
  salida.setRange(44, 44 + numeroBytes, pcm);
  return salida;
}

/// Calcula la duracion de un WAV de 16 kHz mono de 16 bits.
double duracionWav(Uint8List wav) {
  if (wav.lengthInBytes < 44) return 0;
  final bytes = wav.buffer.asByteData();
  final bytesDeAudio = bytes.getUint32(40, Endian.little);
  // 16 kHz con 2 bytes por muestra son 32000 bytes por segundo.
  return bytesDeAudio / (16000 * 2);
}
