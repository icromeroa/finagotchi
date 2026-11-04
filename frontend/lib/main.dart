import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'screens/onboarding/splash_screen.dart';
import 'theme/app_colors.dart';

void main() {
  runApp(const FinaGotchiApp());
}

class FinaGotchiApp extends StatelessWidget {
  const FinaGotchiApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'FinaGotchi',
      theme: ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: AppColors.cream,
        // Aplicamos la tipografía de Google Fonts (Outfit) globalmente
        textTheme: GoogleFonts.outfitTextTheme(
          ThemeData.light().textTheme,
        ),
        colorScheme: ColorScheme.fromSeed(
          seedColor: AppColors.lime,
          primary: AppColors.darkGreen,
        ),
      ),
      home: const SplashScreen(),
    );
  }
}