import os

# Prevent the Dia-1.6B model (~5–10 GB) from being downloaded during tests.
# The dummy backend returns a synthetic audio file without loading any model.
os.environ.setdefault("TTS_BACKEND", "dummy")
