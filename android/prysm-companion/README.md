# PRYSM Android Companion

This directory will host the Jetpack Compose Android application for PRYSM.

## Architecture
- **Language**: Kotlin
- **UI**: Jetpack Compose
- **Network**: WebSockets (authenticated and encrypted with AES-GCM)
- **Background**: Foreground Service for stable WS connections

## Getting Started
For Phase 6, the Python Desktop backend has been fully implemented and verified using a `mock_device.py` client which implements the identical X25519 pairing and AES-GCM encryption protocol.

Open this directory in Android Studio to begin fleshing out the Android UI and connecting the Android system permissions (SMS, Location, Notifications) to the PRYSM WebSocket protocol.
