import 'package:flutter/material.dart';
import '../services/audio_service.dart';

class PushToTalkButton extends StatefulWidget {
  final String accessToken;
  final Function(String data)? onSuccess;

  const PushToTalkButton({
    super.key,
    required this.accessToken,
    this.onSuccess,
  });

  @override
  State<PushToTalkButton> createState() => _PushToTalkButtonState();
}

class _PushToTalkButtonState extends State<PushToTalkButton> {
  final AudioService _audioService = AudioService();
  bool _isRecording = false;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) async {
        setState(() => _isRecording = true);
        await _audioService.startRecording();
      },
      onTapUp: (_) async {
        setState(() => _isRecording = false);

        // Generamos un ID único basado en el tiempo actual para el backend
        String messageIdDateTime = DateTime.now().millisecondsSinceEpoch.toString();

        var resultado = await _audioService.stopAndSendRecording(
          accessToken: widget.accessToken,
          messageId: messageIdDateTime,
        );

        if (resultado != null && resultado['success'] == true) {
          if (widget.onSuccess != null) {
            widget.onSuccess!(resultado['data']);
          }
        }
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        decoration: BoxDecoration(
          color: _isRecording ? Colors.redAccent : Colors.deepPurple,
          borderRadius: BorderRadius.circular(30),
        ),
        child: Text(
          _isRecording ? "Grabando voz..." : "Mantén para hablar",
          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
      ),
    );
  }
}