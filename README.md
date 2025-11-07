# SRT Tools

Multi-SRT import utility for [TTS Generation WebUI](https://github.com/rsxdalv/tts-webui).

## Features

- Select multiple `.srt` subtitle files in the UI.
- Each file is parsed into structured segments: `index`, `start`, `end`, `text`.
- Outputs a JSON file per SRT (same basename) inside a target directory.
- Default output directory: `processed_srt` within the extension folder (auto-created).
- Graceful handling of minor format issues (skips malformed blocks rather than failing).
- TTS integration intentionally deferred; will be added in a follow-up.

## Usage

1. Install / enable the extension.
2. Restart TTS Generation WebUI (if needed).
3. Open the "SRT Tools" tab.
4. Select one or more `.srt` files.
5. Optionally enter an output directory path.
6. Click "Import & Process SRTs" to generate JSON outputs.
7. Review the summary panel for segment counts and output paths.

## Output JSON Format

```json
[
	{
		"index": 1,
		"start": "00:00:01,000",
		"end": "00:00:03,500",
		"text": "Hello world."
	}
]
```

## API Endpoint

UI exposes a function `multi_srt_import`:

- Inputs: `(files: List[File], output_dir_text: str)`
- Returns: summary dict `{ output_dir, files: [{file, segments, output_json}], total_segments, file_count }`

## Development

Run standalone for rapid UI iteration:

```bash
cd tts_webui_extension/srt_tools
python main.py
```

### Local Tests (Extension-Scoped)

Tests live in `workspace/tts_webui_extension.srt_tools/tests/`:

```bash
pytest workspace/tts_webui_extension.srt_tools/tests
```

## License

MIT License
