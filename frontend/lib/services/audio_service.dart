
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

class AudioService {
  final AudioRecorder _audioRecorder = AudioRecorder();

  // IMPORTANTE: esta dirección debe quedar escrita así, sin corchetes
  // ni formato de enlace.
  final String baseUrl = 'http://10.0.2.2:5000/api/v1';

  Future<void> startRecording() async {
    try {
      if (await _audioRecorder.isRecording()) {
        debugPrint('AUDIO: Ya existe una grabación activa.');
        return;
      }

      final permission = await _audioRecorder.hasPermission();

      if (!permission) {
        throw Exception('No tenemos permiso para usar el micrófono.');
      }

      final dir = await getApplicationDocumentsDirectory();

      final path = '${dir.path}/audio_gasto.wav';

      await _audioRecorder.start(
        const RecordConfig(
          encoder: AudioEncoder.wav,
        ),
        path: path,
      );

      debugPrint('AUDIO: Grabación iniciada.');
      debugPrint('AUDIO: Archivo: $path');
    } catch (e) {
      debugPrint('ERROR AL INICIAR GRABACIÓN: $e');
      rethrow;
    }
  }

  Future<void> stopRecording() async {
    if (await _audioRecorder.isRecording()) {
      await _audioRecorder.stop();
      debugPrint('AUDIO: Grabación detenida sin enviar.');
    }
  }

  Future<Map<String, dynamic>?> stopAndSendRecording({
    required String accessToken,
    required String messageId,
  }) async {
    try {
      debugPrint('AUDIO: Deteniendo grabación...');

      final path = await _audioRecorder.stop();

      if (path == null) {
        debugPrint('ERROR: No se encontró ninguna grabación.');
        return {
          'success': false,
          'error': 'No se encontró ninguna grabación.',
        };
      }

      final file = File(path);

      if (!await file.exists()) {
        debugPrint('ERROR: El archivo de audio no existe.');
        return {
          'success': false,
          'error': 'No se encontró el archivo de audio.',
        };
      }

      final fileSize = await file.length();

      debugPrint('AUDIO: Archivo creado. Tamaño: $fileSize bytes.');

      if (fileSize == 0) {
        return {
          'success': false,
          'error': 'La grabación está vacía.',
        };
      }

      final url = Uri.parse('$baseUrl/messages');

      debugPrint('AUDIO: Enviando petición a $url');

      final request = http.MultipartRequest('POST', url);

      request.headers['Authorization'] = 'Bearer $accessToken';

      request.fields['message_id'] = messageId;
      request.fields['origen'] = 'app_voz';
      request.fields['idioma'] = 'es';

      request.files.add(
        await http.MultipartFile.fromPath(
          'audio',
          file.path,
        ),
      );

      debugPrint('AUDIO: Enviando archivo al backend...');

      final streamedResponse = await request.send();

      final response = await http.Response.fromStream(
        streamedResponse,
      );

      debugPrint('AUDIO: Código HTTP: ${response.statusCode}');
      debugPrint('AUDIO: Respuesta: ${response.body}');

      dynamic decoded;

      try {
        decoded = jsonDecode(response.body);
      } catch (e) {
        return {
          'success': false,
          'error': 'El servidor devolvió una respuesta no válida: ${response.body}',
        };
      }

      if (response.statusCode >= 200 &&
          response.statusCode < 300 &&
          decoded is Map &&
          decoded['ok'] == true) {
        final data = decoded['data'];

        debugPrint('AUDIO: El backend recibió el audio correctamente.');

        return {
          'success': true,
          'data': data is Map
              ? Map<String, dynamic>.from(data)
              : <String, dynamic>{},
        };
      }

      final errorMessage = decoded is Map
          ? (decoded['mensaje'] ??
          decoded['message'] ??
          decoded['error'] ??
          response.body)
          .toString()
          : response.body;

      debugPrint('ERROR DEL BACKEND: $errorMessage');

      return {
        'success': false,
        'error': 'HTTP ${response.statusCode}: $errorMessage',
      };
    } catch (e) {
      debugPrint('ERROR AL ENVIAR AUDIO: $e');

      return {
        'success': false,
        'error': 'No se pudo enviar el audio: $e',
      };
    }
  }

  Future<void> dispose() async {
    await _audioRecorder.dispose();
  }
}
