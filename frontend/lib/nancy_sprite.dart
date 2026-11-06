import 'dart:async';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Reproduce un spritesheet horizontal de pixel art sin perder nitidez.
/// Uso:
///   NancySprite(asset: 'assets/nancy/nancy_walk_1x.png',
///               frames: 4, frameSize: Size(48, 51), scale: 6, fps: 6)
class NancySprite extends StatefulWidget {
  final String asset;
  final int frames;
  final Size frameSize; // tamaño de UN frame en px del PNG
  final double scale;   // entero: 4, 6, 8...
  final int fps;
  final bool playing;
  final bool flipX;     // true = mira a la izquierda

  const NancySprite({
    super.key,
    required this.asset,
    this.frames = 4,
    this.frameSize = const Size(48, 51),
    this.scale = 6,
    this.fps = 6,
    this.playing = true,
    this.flipX = false,
  });

  @override
  State<NancySprite> createState() => _NancySpriteState();
}

class _NancySpriteState extends State<NancySprite> {
  ui.Image? _image;
  Timer? _timer;
  int _frame = 0;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final data = await rootBundle.load(widget.asset);
    final codec = await ui.instantiateImageCodec(data.buffer.asUint8List());
    final f = await codec.getNextFrame();
    if (!mounted) return;
    setState(() => _image = f.image);
    _syncTimer();
  }

  void _syncTimer() {
    _timer?.cancel();
    if (!widget.playing) return;
    _timer = Timer.periodic(
      Duration(milliseconds: (1000 / widget.fps).round()),
      (_) => setState(() => _frame = (_frame + 1) % widget.frames),
    );
  }

  @override
  void didUpdateWidget(covariant NancySprite old) {
    super.didUpdateWidget(old);
    if (old.playing != widget.playing || old.fps != widget.fps) _syncTimer();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final w = widget.frameSize.width * widget.scale;
    final h = widget.frameSize.height * widget.scale;
    if (_image == null) return SizedBox(width: w, height: h);
    return Transform.flip(
      flipX: widget.flipX,
      child: CustomPaint(
        size: Size(w, h),
        painter: _SpritePainter(_image!, widget.frameSize, _frame),
      ),
    );
  }
}

class _SpritePainter extends CustomPainter {
  final ui.Image image;
  final Size frameSize;
  final int frame;
  _SpritePainter(this.image, this.frameSize, this.frame);

  @override
  void paint(Canvas canvas, Size size) {
    final src = Rect.fromLTWH(
        frame * frameSize.width, 0, frameSize.width, frameSize.height);
    final dst = Offset.zero & size;
    // FilterQuality.none = vecino más cercano => pixel art perfecto
    canvas.drawImageRect(image, src, dst,
        Paint()..filterQuality = FilterQuality.none..isAntiAlias = false);
  }

  @override
  bool shouldRepaint(_SpritePainter o) => o.frame != frame || o.image != image;
}

/// Nancy caminando de lado a lado sobre un ancho disponible.
class NancyWalker extends StatefulWidget {
  const NancyWalker({super.key});
  @override
  State<NancyWalker> createState() => _NancyWalkerState();
}

class _NancyWalkerState extends State<NancyWalker>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(
      vsync: this, duration: const Duration(seconds: 6))
    ..repeat(reverse: true);

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    const spriteW = 48.0 * 6;
    return LayoutBuilder(builder: (context, box) {
      final range = (box.maxWidth - spriteW).clamp(0.0, double.infinity);
      return AnimatedBuilder(
        animation: _c,
        builder: (_, _) => Align(
          alignment: Alignment.bottomLeft,
          child: Transform.translate(
            offset: Offset(range * _c.value, 0),
            child: NancySprite(
              asset: 'assets/nancy/nancy_walk_1x.png',
              flipX: _c.status == AnimationStatus.reverse,
            ),
          ),
        ),
      );
    });
  }
}
