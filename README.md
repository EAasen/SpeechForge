# DiaSpeak

DiaSpeak is a self-hosted Dockerized application that uses the [`nari-labs/Dia-1.6B`](https://huggingface.co/nari-labs/Dia-1.6B) text-to-speech model to generate high-quality speech audio from text inputs. The output is saved as organized audio files into a structured library for easy access and use.

---

## 🚀 Features

✅ Translate any text into natural-sounding speech using Dia-1.6B  
✅ Save output as high-quality `.wav` or `.mp3` files  
✅ Automatically organize files into a user-defined library structure  
✅ REST API endpoint for integration into other applications  
✅ Configurable output formats, voice settings, and file naming schemes  
✅ Run locally via Docker with no external API dependency

---

## 📦 Quickstart

```bash
git clone https://github.com/yourusername/diaspeak.git
cd diaspeak
docker-compose up --build
