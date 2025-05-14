import argparse
import requests
import os
import sys
import json
from tqdm import tqdm

def main():
    parser = argparse.ArgumentParser(description="DiaSpeak CLI - Batch TTS Processor")
    parser.add_argument('--file', type=str, help='Input text, md, or json file')
    parser.add_argument('--format', type=str, default='wav', help='Audio format: wav, mp3, ogg')
    parser.add_argument('--quality', type=str, default='medium', help='Audio quality: low, medium, high')
    parser.add_argument('--tone', type=str, help='Tone (optional)')
    parser.add_argument('--prompt', type=str, help='Prompt/context (optional)')
    parser.add_argument('--voice', type=str, help='Voice (optional)')
    parser.add_argument('--speed', type=str, help='Speed (optional)')
    parser.add_argument('--pitch', type=str, help='Pitch (optional)')
    parser.add_argument('--output', type=str, default='outputs', help='Output directory')
    parser.add_argument('--api', type=str, default='http://localhost:8000/speak-file', help='API endpoint')
    parser.add_argument('--batch', type=str, help='Directory for batch processing')
    args = parser.parse_args()

    files_to_process = []
    if args.batch:
        for fname in os.listdir(args.batch):
            if fname.endswith(('.txt', '.md', '.json')):
                files_to_process.append(os.path.join(args.batch, fname))
    elif args.file:
        files_to_process = [args.file]
    else:
        print('No input file or batch directory specified.')
        sys.exit(1)

    for fpath in tqdm(files_to_process, desc='Processing files'):
        with open(fpath, 'rb') as fin:
            data = {
                'format': args.format,
                'quality': args.quality,
            }
            if args.tone: data['tone'] = args.tone
            if args.prompt: data['prompt'] = args.prompt
            if args.voice: data['voice'] = args.voice
            if args.speed: data['speed'] = args.speed
            if args.pitch: data['pitch'] = args.pitch
            files = {'file': (os.path.basename(fpath), fin)}
            resp = requests.post(args.api, data=data, files=files)
            if resp.status_code == 200:
                result = resp.json()
                print(f"Success: {fpath} -> {result.get('file_path')}")
                # Optionally download the file
                url = result.get('url')
                if url:
                    outdir = args.output
                    os.makedirs(outdir, exist_ok=True)
                    outname = os.path.join(outdir, os.path.basename(result['file_path']))
                    audio_resp = requests.get(url)
                    if audio_resp.status_code == 200:
                        with open(outname, 'wb') as fout:
                            fout.write(audio_resp.content)
                        print(f"Downloaded: {outname}")
            else:
                print(f"Error processing {fpath}: {resp.text}")

if __name__ == '__main__':
    main()
