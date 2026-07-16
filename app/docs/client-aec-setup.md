# Echo / Duplex Audio — Client-Side Fix

## Problem

When the agent speaks (TTS), the audio plays through the **user's device speaker**.
That same speaker audio leaks into the **user's device microphone** and is sent
back to the agent through LiveKit. The agent's VAD (Voice Activity Detection)
mistakes this echo for real user speech, causing:

- The agent to interrupt itself
- False triggers of `user_state_changed` → client orb flickers
- Broken turn-taking

## Root Cause

| Layer | Problem |
|---|---|
| **User's device** | Speaker output bleeds into mic input (physical acoustics) |
| **LiveKit pipeline** | Agent receives the echoed audio as a regular user audio frame |
| **Agent VAD** | Cannot distinguish echo from real speech — both look like audio energy |

## Architecture Overview

```
Agent publishes TTS audio ──► LiveKit ──► User's device plays through speaker
                                                │
                                                ▼ (acoustic leakage)
User's mic picks up echo ──► LiveKit ──► Agent hears "user is speaking"
```

## Client-Side Fix (Frontend Team)

The browser has a built-in WebRTC Audio Processing Module (APM) with Acoustic
Echo Cancellation (AEC). **It must be enabled** when setting up the user's
microphone.

### LiveKit JS SDK — `RemoteParticipant`

When creating or joining a room, ensure `getUserMedia` (or LiveKit's
`createLocalAudioTrack`) uses these constraints:

```js
const audioTrack = await LocalAudioTrack.create({
  // This is the critical part:
  echoCancellation: true,
  noiseSuppression: true,
  autoGainControl: true,
});
```

If using LiveKit's `Room.connect` with defaults, AEC is usually on, but verify:

```js
const room = new Room({
  audioCaptureDefaults: {
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true,
  },
});
await room.connect(url, token);
```

### Mobile SDKs (Android / iOS / React Native)

| Platform | API |
|---|---|
| **iOS / LiveKit Swift SDK** | `AudioCaptureOptions(echoCancellation: true)` |
| **Android / LiveKit Android SDK** | `AudioCaptureOptions.Builder().setEchoCancellation(true)` |
| **React Native** | `roomOptions?.audioCaptureDefaults?.echoCancellation ?? true` |

### How AEC Works (so you understand the timing)

1. User starts speaking → agent starts playing TTS reply
2. For the **first ~3 seconds**, browser AEC is calibrating — it learns the
   acoustic path from speaker to microphone
3. After calibration, AEC subtracts the echo from the mic signal

The agent's `aec_warmup_duration=3.0s` matches this calibration window:
- During warmup, the agent blocks interruptions
- This prevents the agent from "hearing" its own echo and interrupting itself
- Once warmup expires, AEC should be calibrated and echo-free

## Agent-Side Behavior (for reference)

The agent already handles its side:

| Mechanism | What it does |
|---|---|
| `aec_warmup_duration=3.0` | Ignores interruptions for 3s after agent starts speaking |
| Client-side chime (`lk.agent_ready` attribute) | Avoids TTS audio for welcome message → zero echo |
| `TurnDetector(v1-mini)` | ML-based end-of-turn detection (not VAD-only, reduces false positives) |
| VAD thresholds tuned | `activation=0.4`, `deactivation=0.2`, `min_silence=0.6s` |

## Verification Checklist

Before marking this done, test with **speakerphone / no headphones**:

| Test | Expected behavior |
|---|---|
| User stays silent while agent speaks | No "listening" state change, no orb animation |
| User says "stop" while agent speaks | Agent stops immediately (interruption works) |
| Conversation over 30s | No echo buildup, quality stays consistent |

Hear echo at the start of each turn but it clears up after ~3s → AEC is
working, just slow to calibrate. Increase `aec_warmup_duration` on the agent
side if needed.

## If Echo Persists Despite AEC

| Root cause | Fix |
|---|---|
| Device has poor acoustic isolation | Use headphones |
| AEC not enabled (see above) | Fix constraints |
| AEC enabled but not calibrating | Ensure `getUserMedia` promise resolves **before** the agent starts speaking |
| Multiple audio output paths | Ensure only one speaker is active |
