import 'package:flutter/material.dart';

import '../../theme/app_colors.dart';
import '../services/audio_service.dart';

class VoiceRecordingModal extends StatefulWidget {
  final String accessToken;
  final Function(Map<String, dynamic> data) onSuccess;
  final VoidCallback onManualRegister;

  const VoiceRecordingModal({
    super.key,
    required this.accessToken,
    required this.onSuccess,
    required this.onManualRegister,
  });

  @override
  State<VoiceRecordingModal> createState() =>
      _VoiceRecordingModalState();
}

class _VoiceRecordingModalState extends State<VoiceRecordingModal> {
  final AudioService _audioService = AudioService();

  bool _isRecording = false;
  bool _isSending = false;

  String _nancyMessage = 'Te escucho...';
  String? _transcribedText;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _startRecording();
  }

  Future<void> _startRecording() async {
    if (!mounted) return;

    try {
      await _audioService.startRecording();

      if (!mounted) return;

      setState(() {
        _isRecording = true;
        _isSending = false;
        _errorMessage = null;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _isRecording = false;
        _isSending = false;
        _errorMessage = e.toString();
        _nancyMessage = 'No pude activar el micrófono.';
      });
    }
  }

  Future<void> _stopAndSend() async {
    if (_isSending || !_isRecording) return;

    setState(() {
      _isSending = true;
      _isRecording = false;
      _errorMessage = null;
      _nancyMessage = 'Nancy está escuchando tu mensaje...';
    });

    try {
      final messageId =
      DateTime.now().microsecondsSinceEpoch.toString();

      final resultado =
      await _audioService.stopAndSendRecording(
        accessToken: widget.accessToken,
        messageId: messageId,
      );

      if (!mounted) return;

      if (resultado != null && resultado['success'] == true) {
        final data = Map<String, dynamic>.from(
          resultado['data'] as Map,
        );

        final mensaje =
            data['mensaje_nancy']?.toString() ??
                'Ya recibí tu mensaje.';

        final transcripcion =
        data['texto_transcrito']?.toString();

        final tipoRespuesta =
        data['tipo_respuesta']?.toString();

        final intent = data['intent']?.toString();

        setState(() {
          _nancyMessage = mensaje;
          _transcribedText = transcripcion;
          _errorMessage = null;
        });

        // Solo actualizamos Home cuando el movimiento
        // ya fue confirmado y guardado.
        if (tipoRespuesta == 'resultado' &&
            intent == 'registrar') {
          widget.onSuccess(data);
        }
      } else {
        setState(() {
          _errorMessage =
              resultado?['error']?.toString() ??
                  'No pude enviar el audio.';
          _nancyMessage = 'No pude procesar tu grabación.';
        });
      }
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _errorMessage = e.toString();
        _nancyMessage = 'Ocurrió un problema al enviar el audio.';
      });
    }

    // Nancy vuelve a escuchar para que puedas confirmar,
    // corregir o hacer otra consulta.
    if (mounted) {
      await _startRecording();
    }
  }

  Future<void> _retryRecording() async {
    if (_isSending) return;

    try {
      await _audioService.stopRecording();

      if (!mounted) return;

      setState(() {
        _nancyMessage = 'Te escucho de nuevo...';
        _transcribedText = null;
        _errorMessage = null;
      });

      await _startRecording();
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _errorMessage = e.toString();
      });
    }
  }

  Future<void> _closeModal() async {
    await _audioService.stopRecording();

    if (!mounted) return;

    Navigator.pop(context);
  }

  Future<void> _openManualRegisterModal() async {
    await _audioService.stopRecording();

    if (!mounted) return;

    // Home se encarga de cerrar este modal y abrir el manual.
    widget.onManualRegister();
  }

  @override
  void dispose() {
    _audioService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
      decoration: const BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(32),
        ),
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Barra superior
            Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: AppColors.mutedPink,
                borderRadius: BorderRadius.circular(10),
              ),
            ),

            const SizedBox(height: 14),

            // Título y botón cerrar
            Row(
              children: [
                const Icon(
                  Icons.mic,
                  color: AppColors.wine,
                  size: 22,
                ),
                const SizedBox(width: 8),
                Text(
                  _isSending
                      ? 'Procesando...'
                      : _isRecording
                      ? 'Grabando (activo)'
                      : 'Micrófono detenido',
                  style: const TextStyle(
                    color: AppColors.wine,
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const Spacer(),
                InkWell(
                  onTap: _closeModal,
                  borderRadius: BorderRadius.circular(20),
                  child: Container(
                    width: 32,
                    height: 32,
                    decoration: BoxDecoration(
                      color: AppColors.mutedPink.withOpacity(0.5),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.close,
                      color: AppColors.wine,
                      size: 18,
                    ),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 12),

            // Chips superiores
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  _buildChip('a) No se escuchó'),
                  const SizedBox(width: 8),
                  _buildChip('b) Sin monto'),
                  const SizedBox(width: 8),
                  _buildChip('c) Sin conexión'),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // Nancy escuchando
            Container(
              width: 145,
              height: 145,
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: AppColors.mutedPink.withOpacity(0.25),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(
                  color: AppColors.wine.withOpacity(0.4),
                  width: 1.5,
                ),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(18),
                child: Image.asset(
                  'assets/images/nancy_perfil_escuchando_microfono 1.png',
                  fit: BoxFit.contain,
                ),
              ),
            ),

            const SizedBox(height: 12),

            Text(
              _isSending
                  ? 'Un momento...'
                  : _isRecording
                  ? 'Te escucho...'
                  : 'Preparando micrófono...',
              style: const TextStyle(
                color: AppColors.wine,
                fontSize: 18,
                fontWeight: FontWeight.w800,
              ),
            ),

            const SizedBox(height: 12),

            // Respuesta de Nancy
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppColors.cardCream,
                borderRadius: BorderRadius.circular(18),
                border: Border.all(
                  color: AppColors.wine.withOpacity(0.2),
                ),
              ),
              child: Column(
                children: [
                  const Text(
                    'Nancy dice:',
                    style: TextStyle(
                      color: AppColors.wine,
                      fontWeight: FontWeight.w800,
                      fontSize: 12,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    _nancyMessage,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      color: AppColors.darkGreen,
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  if (_transcribedText != null &&
                      _transcribedText!.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    const Divider(),
                    const Text(
                      'Entendí:',
                      style: TextStyle(
                        color: AppColors.wine,
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      _transcribedText!,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        color: AppColors.darkGreen,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ],
              ),
            ),

            if (_errorMessage != null) ...[
              const SizedBox(height: 8),
              Text(
                _errorMessage!,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: AppColors.wine,
                  fontSize: 11,
                ),
              ),
            ],

            const SizedBox(height: 14),

            // Botón para enviar
            GestureDetector(
              onTap: _isRecording ? _stopAndSend : null,
              child: Opacity(
                opacity: _isRecording ? 1 : 0.5,
                child: Container(
                  width: 70,
                  height: 70,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: AppColors.lime.withOpacity(0.3),
                    border: Border.all(
                      color: AppColors.darkGreen.withOpacity(0.2),
                      width: 1.5,
                    ),
                  ),
                  child: Center(
                    child: Container(
                      width: 48,
                      height: 48,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        color: AppColors.lime,
                      ),
                      child: Icon(
                        _isSending
                            ? Icons.hourglass_top
                            : Icons.mic,
                        color: AppColors.darkGreen,
                        size: 24,
                      ),
                    ),
                  ),
                ),
              ),
            ),

            const SizedBox(height: 8),

            Text(
              _isSending
                  ? 'Enviando grabación...'
                  : 'Toca para enviar',
              style: const TextStyle(
                color: AppColors.darkGreen,
                fontSize: 12,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 10),

            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16),
              child: Text(
                'Di, por ejemplo: “Almuerzo corriente 14 mil con Nequi”',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: AppColors.darkGreen,
                  fontSize: 11,
                  height: 1.3,
                ),
              ),
            ),

            const SizedBox(height: 14),

            // Intentar de nuevo
            Container(
              decoration: const BoxDecoration(
                borderRadius: BorderRadius.all(
                  Radius.circular(30),
                ),
                border: Border(
                  bottom: BorderSide(
                    color: AppColors.darkGreen,
                    width: 3.5,
                  ),
                ),
              ),
              child: SizedBox(
                width: double.infinity,
                height: 44,
                child: ElevatedButton(
                  onPressed: _isSending ? null : _retryRecording,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.lime,
                    elevation: 0,
                    shape: const StadiumBorder(),
                  ),
                  child: const Text(
                    'Intentar de nuevo ↻',
                    style: TextStyle(
                      color: AppColors.darkGreen,
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                    ),
                  ),
                ),
              ),
            ),

            const SizedBox(height: 8),

            TextButton(
              onPressed: _isSending
                  ? null
                  : _openManualRegisterModal,
              child: const Text(
                'Registrar manualmente',
                style: TextStyle(
                  color: AppColors.wine,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  decoration: TextDecoration.underline,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChip(String label) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: 12,
        vertical: 6,
      ),
      decoration: BoxDecoration(
        color: AppColors.cardCream,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: AppColors.wine.withOpacity(0.3),
        ),
      ),
      child: Text(
        label,
        style: const TextStyle(
          color: AppColors.wine,
          fontSize: 11,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}