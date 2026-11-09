# FinaGotchi · Frontend (Flutter)

Aplicación Flutter que consume la API de FinaGotchi.

## Requisitos

- Flutter 3.47 o superior (`flutter --version`).
- El backend levantado en el puerto **5001**:

  ```bash
  cd ..                      # raíz del repositorio
  .venv/bin/python backend/server.py
  ```

  Comprueba con `curl http://127.0.0.1:5001/api/v1/health`.

## Cómo ejecutarla

Siempre desde **esta carpeta** (`frontend`), no desde la raíz:

```bash
cd frontend
flutter pub get
flutter run -d macos
```

- `-d macos` abre la app de escritorio en tu Mac.
- `-d chrome` abre la versión web (la grabación de voz no está disponible en web).
- `flutter devices` lista los dispositivos disponibles.

Para el emulador de Android:

```bash
flutter run -d emulator-5554
```

La app usa `10.0.2.2:5001` automáticamente, que es cómo el emulador ve el
`localhost` del Mac.

Para un teléfono físico en la misma red Wi-Fi, indica la IP del Mac:

```bash
flutter run -d <id-del-dispositivo> \
  --dart-define=API_BASE_URL=http://192.168.1.22:5001/api/v1
```

## Dirección del backend

`lib/services/api_config.dart` decide la URL según la plataforma:

| Plataforma | URL |
| --- | --- |
| macOS, iOS, escritorio, web | `http://127.0.0.1:5001/api/v1` |
| Emulador Android | `http://10.0.2.2:5001/api/v1` |
| Dispositivo físico | `--dart-define=API_BASE_URL=...` |

## Permisos de macOS

Ya están configurados en:

- `macos/Runner/DebugProfile.entitlements` y `Release.entitlements`:
  `com.apple.security.network.client` y `com.apple.security.device.audio-input`.
- `macos/Runner/Info.plist` e `ios/Runner/Info.plist`:
  `NSMicrophoneUsageDescription`.

La primera vez que uses el micrófono, macOS pedirá permiso. Acéptalo.

La grabación se configura en **WAV mono, 16 kHz y 16 bits** porque es el
formato que valida el backend. Si ves `AUDIO_INVALIDO` con
`{"channels": 2}`, revisa que `RecordConfig` en
`lib/services/audio_service.dart` conserve `numChannels: 1` y
`sampleRate: 16000`.
