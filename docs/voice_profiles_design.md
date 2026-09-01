# SpeechForge Voice Profile Storage & Provider-Aware TTS Architecture Design

## 1. Overview & Objectives

SpeechForge requires a flexible, unified architecture to manage voice profiles and Text-to-Speech (TTS) configurations across both on-device (local model) execution and external cloud providers (Azure Cognitive Services, AWS Polly, Google Cloud Text-to-Speech).

This design specification defines:
- A standardized **Voice Profile Data Model** supporting provider-neutral and provider-specific parameters.
- Storage, lifecycle management, and multi-tenant persistence strategies.
- A dynamic **Provider Capability Model** exposing voices, languages, styles, formats, and hardware/quota limitations.
- Strategies for handling differences between local on-device TTS and cloud APIs.
- Fallback mechanics, validation rules, and error handling.
- Frontend (React) and Backend (Flask) integration specifications.
- A clear path toward integrating Azure, AWS, and Google TTS backends without constraining provider-specific features.

---

## 2. Voice Profile Data Model

A Voice Profile abstracts voice configuration into a reusable, named configuration entity scoped to a user or tenant.

### 2.1 JSON Schema Structure

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "VoiceProfile",
  "type": "object",
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "name": { "type": "string", "minLength": 1, "maxLength": 100 },
    "description": { "type": "string", "maxLength": 500 },
    "user": { "type": "string" },
    "tenant": { "type": "string" },
    "is_default": { "type": "boolean" },
    "provider": { 
      "type": "string", 
      "enum": ["local_dia", "dummy", "azure", "aws", "google"] 
    },
    "voice_id": { "type": "string" },
    "language": { "type": "string", "pattern": "^[a-z]{2}(-[A-Z]{2})?$" },
    "gender": { "type": "string", "enum": ["female", "male", "neutral", "unspecified"] },
    "settings": {
      "type": "object",
      "properties": {
        "speaking_rate": { "type": "number", "minimum": 0.25, "maximum": 4.0, "default": 1.0 },
        "pitch": { "type": "number", "minimum": -20.0, "maximum": 20.0, "default": 0.0 },
        "volume": { "type": "number", "minimum": 0.0, "maximum": 100.0, "default": 100.0 },
        "output_format": { "type": "string", "enum": ["wav", "mp3", "ogg", "pcm", "flac"], "default": "wav" },
        "sample_rate": { "type": "integer", "enum": [8000, 16000, 22050, 24000, 44100, 48000], "default": 22050 }
      },
      "required": ["output_format"]
    },
    "provider_params": {
      "type": "object",
      "description": "Provider-specific parameters preserved without loss of fidelity",
      "properties": {
        "azure": {
          "type": "object",
          "properties": {
            "style": { "type": "string" },
            "style_degree": { "type": "number", "minimum": 0.0, "maximum": 2.0 },
            "role": { "type": "string" },
            "use_ssml": { "type": "boolean" }
          }
        },
        "aws": {
          "type": "object",
          "properties": {
            "engine": { "type": "string", "enum": ["standard", "neural", "long-form", "generative"] },
            "lexicon_names": { "type": "array", "items": { "type": "string" } },
            "speech_mark_types": { "type": "array", "items": { "type": "string" } }
          }
        },
        "google": {
          "type": "object",
          "properties": {
            "ssml_gender": { "type": "string" },
            "audio_encoding": { "type": "string" },
            "effects_profile_id": { "type": "array", "items": { "type": "string" } }
          }
        },
        "local_dia": {
          "type": "object",
          "properties": {
            "temperature": { "type": "number", "minimum": 0.1, "maximum": 2.0 },
            "guidance_scale": { "type": "number", "minimum": 1.0, "maximum": 10.0 },
            "reference_audio_path": { "type": "string" }
          }
        }
      }
    },
    "fallback_config": {
      "type": "object",
      "properties": {
        "fallback_profile_id": { "type": ["string", "null"] },
        "allow_provider_fallback": { "type": "boolean", "default": true },
        "fallback_provider": { "type": "string", "default": "local_dia" }
      }
    },
    "created_at": { "type": "string", "format": "date-time" },
    "updated_at": { "type": "string", "format": "date-time" }
  },
  "required": ["id", "name", "provider", "voice_id", "language"]
}
```

---

## 3. Provider Capabilities & Registry Model

To prevent hardcoding vendor features in the application logic, SpeechForge introduces a **TTS Provider Capability Registry**. The API exposes `GET /tts/providers`, returning available backends and their features.

### 3.1 Capability Schema

```json
{
  "providers": {
    "local_dia": {
      "name": "Local Dia (On-Device)",
      "type": "local",
      "supports_offline": true,
      "supports_ssml": false,
      "supported_formats": ["wav", "mp3", "ogg"],
      "sample_rates": [22050, 44100],
      "languages": [
        { "code": "en-US", "name": "English (US)" },
        { "code": "es-ES", "name": "Spanish" }
      ],
      "voices": [
        { "id": "dia-default", "name": "Dia Voice 1", "gender": "neutral", "styles": [] }
      ],
      "custom_params": {
        "temperature": { "type": "float", "min": 0.1, "max": 2.0, "default": 0.7 },
        "guidance_scale": { "type": "float", "min": 1.0, "max": 10.0, "default": 3.0 }
      }
    },
    "azure": {
      "name": "Azure Speech Services",
      "type": "cloud",
      "supports_offline": false,
      "supports_ssml": true,
      "supported_formats": ["wav", "mp3", "ogg", "pcm"],
      "sample_rates": [16000, 24000, 44100, 48000],
      "languages": [
        { "code": "en-US", "name": "English (US)" },
        { "code": "fr-FR", "name": "French" },
        { "code": "de-DE", "name": "German" }
      ],
      "voices": [
        { 
          "id": "en-US-JennyNeural", 
          "name": "Jenny (Neural)", 
          "gender": "female", 
          "styles": ["cheerful", "sad", "empathetic", "chat", "newscast"] 
        },
        { 
          "id": "en-US-GuyNeural", 
          "name": "Guy (Neural)", 
          "gender": "male", 
          "styles": ["newscast", "angry", "cheerful"] 
        }
      ],
      "custom_params": {
        "style": { "type": "string" },
        "style_degree": { "type": "float", "min": 0.0, "max": 2.0, "default": 1.0 }
      }
    },
    "aws": {
      "name": "AWS Polly",
      "type": "cloud",
      "supports_offline": false,
      "supports_ssml": true,
      "supported_formats": ["mp3", "ogg", "pcm"],
      "sample_rates": [8000, 16000, 22050, 24000],
      "languages": [
        { "code": "en-US", "name": "English (US)" },
        { "code": "es-US", "name": "Spanish (US)" }
      ],
      "voices": [
        { "id": "Joanna", "name": "Joanna", "gender": "female", "engines": ["standard", "neural"] },
        { "id": "Matthew", "name": "Matthew", "gender": "male", "engines": ["standard", "neural", "generative"] }
      ],
      "custom_params": {
        "engine": { "type": "enum", "options": ["standard", "neural", "generative"], "default": "neural" }
      }
    },
    "google": {
      "name": "Google Cloud Text-to-Speech",
      "type": "cloud",
      "supports_offline": false,
      "supports_ssml": true,
      "supported_formats": ["mp3", "wav", "ogg"],
      "sample_rates": [16000, 24000, 48000],
      "languages": [
        { "code": "en-US", "name": "English (US)" },
        { "code": "ja-JP", "name": "Japanese" }
      ],
      "voices": [
        { "id": "en-US-Neural2-F", "name": "Neural2 Female F", "gender": "female" },
        { "id": "en-US-Studio-O", "name": "Studio Male O", "gender": "male" }
      ],
      "custom_params": {
        "effects_profile_id": { "type": "array_string" }
      }
    }
  }
}
```

---

## 4. On-Device vs. Cloud TTS Processing Architecture

| Metric / Dimension | On-Device TTS (`local_dia`) | Cloud TTS (Azure, AWS, Google) |
|---|---|---|
| **Execution Environment** | Local GPU/CPU container | External REST/gRPC Cloud APIs |
| **Network Dependence** | Fully offline capable | Requires persistent internet & API key |
| **Latency Profile** | Variable depending on hardware (500ms–3s) | Network roundtrip + remote inference (200ms–800ms) |
| **Authentication** | Local JWT / Tenant authorization | API Keys, IAM Roles, Service Accounts |
| **Cost & Quota** | Computation bound (GPU load) | Per-character API billing & rate limits |
| **Feature Richness** | Model-specific parameters (temp, guidance) | SSML, Neural emotion styles, custom lexicons |

---

## 5. Persistence, Storage, and Multi-Tenancy

1. **Storage Mechanics**:
   - Profiles are stored persistently in JSON storage (`outputs/voice_profiles.json`) with thread-safe file locking, extensible to SQL DB (PostgreSQL / SQLite).
2. **Tenant & User Isolation**:
   - Each voice profile is scoped to `user` and `tenant`. Users can only access, edit, or select profiles belonging to their tenant or marked as global defaults.
3. **Session & Deployment Persistence**:
   - Profiles persist across container restarts.
   - S3 export and backup capability allows profiles to be archived alongside audio catalogs.
4. **Environment Defaults**:
   - Environment variables (e.g. `DEFAULT_VOICE_PROFILE_ID`, `TTS_BACKEND`) define deployment-wide defaults when no profile is explicitly specified.

---

## 6. Recommended Validation, Configuration, and Fallback Rules

### 6.1 Validation Pipeline
Before creating or updating a Voice Profile:
1. Verify `provider` exists in `TTS_PROVIDER_REGISTRY`.
2. Check if selected `voice_id` and `language` are valid for the given provider.
3. Validate settings (`speaking_rate`, `pitch`, `sample_rate`) against allowed ranges.
4. Validate provider-specific parameters (`provider_params`).

### 6.2 Provider & Voice Fallback Logic
When a TTS request specifies a profile or provider:
```
1. Attempt synthesis with requested Voice Profile & Provider.
2. IF cloud provider fails (e.g. quota, timeout, network error, missing API key):
   a. IF `fallback_config.allow_provider_fallback` is true:
      i. Switch to fallback_provider (default: `local_dia` or `dummy`).
      ii. Log warning and notify caller in response metadata.
   b. ELSE: Return 502 Bad Gateway with diagnostic error message.
3. IF requested voice_id is unsupported on provider:
   a. Fall back to provider default voice (e.g. `dia-default` or `en-US-JennyNeural`).
```

---

## 7. API Endpoints Specification

- **`GET /voice-profiles`**: List voice profiles for authenticated user/tenant. Query parameters: `provider`, `language`, `is_default`.
- **`POST /voice-profiles`**: Create a new voice profile.
- **`GET /voice-profiles/<id>`**: Fetch voice profile details by ID.
- **`PUT /voice-profiles/<id>`**: Update an existing voice profile.
- **`DELETE /voice-profiles/<id>`**: Delete a voice profile by ID.
- **`GET /tts/providers`**: List supported TTS providers, capabilities, available voices, styles, and parameter specs.

In `/speak` and `/speak-async`, clients can pass `voice_profile_id`. The backend automatically loads the profile settings, validates capabilities, applies fallbacks, and executes synthesis.

---

## 8. Path Toward Azure, AWS, and Google Support

The architecture provides a provider interface extension:

```python
class BaseTTSProvider:
    def synthesize(self, text: str, settings: dict, provider_params: dict) -> dict:
        raise NotImplementedError

class LocalDiaProvider(BaseTTSProvider): ...
class AzureTTSProvider(BaseTTSProvider): ...
class AWSPollyProvider(BaseTTSProvider): ...
class GoogleTTSProvider(BaseTTSProvider): ...
```

By abstracting provider calls into concrete provider classes implementing `BaseTTSProvider`, SpeechForge can easily add full Azure, AWS, and Google Cloud implementations with zero breaking changes to existing endpoints or frontend components.
