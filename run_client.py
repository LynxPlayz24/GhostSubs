from pathlib import Path
import sys
from whisper_live.client import TranscriptionClient
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', '-p',
                          type=int,
                          default=9090,
                          help="Websocket port to run the server on.")
    parser.add_argument('--server', '-s',
                          type=str,
                          default='localhost',
                          help='hostname or ip address of server')
    parser.add_argument('--files', '-f',
                          type=str,
                          nargs='+',
                          help='Files to transcribe, separated by spaces. '
                              'If not provided, will use microphone input.')
    parser.add_argument('--output_file', '-o',
                          type=str,
                          default='./output_recording.wav',
                          help='output recording filename, only used for microphone input.')
    parser.add_argument('--model', '-m',
                          type=str,
                          default='small',
                          help='Model to use for transcription, e.g., "tiny, small.en, large-v3".')
    parser.add_argument('--lang', '-l',
                          type=str,
                          default='en',
                          help='Language code for transcription, e.g., "en" for English.')
    parser.add_argument('--translate', '-t',
                          action='store_true',
                          help='Use Whisper built-in translation to English (sets task=translate). '
                              'For any-to-any translation, use --enable_translation instead.')
    parser.add_argument('--mute_audio_playback', '-a',
                          action='store_true',
                          help='Mute audio playback during transcription.') 
    parser.add_argument('--save_output_recording', '-r',
                          action='store_true',
                          help='Save the output recording, only used for microphone input.')
    parser.add_argument('--enable_translation',
                          action='store_true',
                          help='Enable any-to-any translation via M2M100 model (separate from Whisper --translate).')
    parser.add_argument('--target_language', '-tl',
                          type=str,
                          default='fr',
                          help='Target language for translation, e.g., "fr" for French.')
    parser.add_argument('--enable_timestamps',
                          action='store_true',
                          help='Show transcription with timestamps')
    parser.add_argument('--n_display_segments',
                          type=int,
                          default=4,
                          help='Number of transcript segments to display in terminal (default: 4).')
    parser.add_argument('--initial_prompt',
                          type=str,
                          default=None,
                          help='Initial prompt for the whisper model (e.g., to guide context or translation).')

    args = parser.parse_args()

    if args.translate and args.enable_translation:
        print("[WARN]: Both --translate and --enable_translation are set. "
              "--translate uses Whisper's built-in to-English translation, "
              "while --enable_translation uses M2M100 for any-to-any. "
              "Both will be active.")

    def save_transcription(text, segments):
        """Save Japanese transcription to a debug file."""
        recent = segments[-2:]
        lines = "\n".join(seg["text"].strip() for seg in recent if seg.get("text", "").strip())
        with open("transcription.txt", "w", encoding="utf-8") as f:
            f.write(lines + "\n")

    def save_translation(text, segments):
        """Save English translation to the overlay file."""
        recent = segments[-2:]
        lines = "\n".join(seg["text"].strip() for seg in recent if seg.get("text", "").strip())
        with open("translation.txt", "w", encoding="utf-8") as f:
            f.write(lines + "\n")

    client = TranscriptionClient(
        args.server,
        args.port,
        lang=args.lang,
        translate=args.translate,
        model=args.model,
        use_vad=True,
        vad_parameters={"threshold": 0.4, "min_speech_duration_ms": 100, "min_silence_duration_ms": 200},
        save_output_recording=args.save_output_recording,
        output_recording_filename=args.output_file,
        mute_audio_playback=args.mute_audio_playback,
        enable_translation=args.enable_translation,
        target_language=args.target_language,
        transcription_callback=save_transcription,
        translation_callback=save_translation,
        enable_timestamps=args.enable_timestamps,
        display_segments=args.n_display_segments,
        same_output_threshold=3,
        initial_prompt=args.initial_prompt,
    )

    try:
        if args.files is None:
            client()
            sys.exit(0)

        # Validate audio files
        valid_files = []
        for file_path in args.files:
            path = Path(file_path)
            if path.exists() and path.is_file():
                valid_files.append(str(path))
            else:
                print(f"Warning: File not found: {file_path}")

        if not valid_files:
            print("Error: No valid audio files found!")
            sys.exit(1)

        print(f"Found {len(valid_files)} audio file(s) to stream:")
        for file_path in valid_files:
            print(f"  - {file_path}")

        for f in valid_files:
            client(f)
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down client and background servers...")
        import subprocess
        subprocess.run('taskkill /FI "WINDOWTITLE eq WhisperLive Server*" /T /F', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run('taskkill /FI "WINDOWTITLE eq Subtitle Overlay*" /T /F', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sys.exit(0)
