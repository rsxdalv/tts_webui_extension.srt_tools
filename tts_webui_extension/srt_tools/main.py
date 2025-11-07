import gradio as gr
import os
import json
import re
from typing import List, Dict, Tuple


TIMECODE_PATTERN = re.compile(
    r"^(?P<start>\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(?P<end>\d{2}:\d{2}:\d{2},\d{3})$"
)


def parse_srt_content(content: str) -> List[Dict]:
    """Parse raw SRT file content into a list of segment dicts.

    Each segment dict contains: index (int), start (str), end (str), text (str).

    The parser is intentionally tolerant: it skips malformed blocks instead of raising.
    """
    segments: List[Dict] = []
    # Normalize newlines
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    # Split on blank lines (two or more newlines)
    raw_blocks = re.split(r"\n{2,}", content.strip())

    for block in raw_blocks:
        lines = [l.strip("\ufeff ") for l in block.split("\n") if l.strip() != ""]
        if len(lines) < 3:
            # Need at least index, timecode, one text line
            continue
        # First line: index (may be numeric) – tolerate non-numeric by assigning sequential later
        try:
            index = int(lines[0])
            line_offset = 1
        except ValueError:
            # Fallback: treat as missing index; we will not rely on it for parsing timecodes
            index = len(segments) + 1
            line_offset = 0  # timecode might be on first line

        # Timecode line
        if line_offset >= len(lines):
            continue
        m = TIMECODE_PATTERN.match(lines[line_offset])
        if not m:
            # If missing proper timecode, skip block
            continue
        start = m.group("start")
        end = m.group("end")
        text_lines = lines[line_offset + 1 :]
        text = " ".join(text_lines).strip()
        if not text:
            continue
        segments.append({"index": index, "start": start, "end": end, "text": text})

    # Reassign indices sequentially to ensure consistency
    for i, seg in enumerate(segments, start=1):
        seg["index"] = i
    return segments


def write_segments_to_json(segments: List[Dict], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)


def process_srt_files(file_paths: List[str], output_dir: str) -> Dict:
    """Process multiple SRT files sequentially and write JSON per file.

    Args:
        file_paths: list of raw .srt file paths.
        output_dir: destination directory for JSON outputs (created if absent).

    Returns summary dict including per-file stats.
    """
    os.makedirs(output_dir, exist_ok=True)
    summary = {"output_dir": output_dir, "files": []}
    for path in file_paths:
        if not path.lower().endswith(".srt"):
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            segments = parse_srt_content(content)
            base = os.path.splitext(os.path.basename(path))[0]
            out_path = os.path.join(output_dir, f"{base}.json")
            write_segments_to_json(segments, out_path)
            summary["files"].append(
                {
                    "file": os.path.basename(path),
                    "segments": len(segments),
                    "output_json": out_path,
                }
            )
        except Exception as e:
            summary["files"].append(
                {
                    "file": os.path.basename(path),
                    "error": str(e),
                    "segments": 0,
                }
            )
    return summary


def multi_srt_import(files: List[Tuple[str]], output_dir_text: str):
    """Gradio interface function to import & parse multiple SRT files.

    Parameters:
        files: Provided by gr.Files; each element is a TemporaryFile wrapper with a .name attribute.
        output_dir_text: Optional directory path string; if blank, defaults to a 'processed_srt' folder within this extension.

    Returns: JSON-serializable summary dict.

    Note: TTS integration intentionally omitted; TODO placeholder for next steps.
    """
    # Resolve output directory
    if not output_dir_text.strip():
        # Place inside extension directory for isolation
        default_dir = os.path.join(os.path.dirname(__file__), "processed_srt")
        output_dir = default_dir
    else:
        output_dir = os.path.abspath(output_dir_text.strip())

    file_paths = []
    for f in files or []:
        # gr.Files returns objects; attempt to extract path safely
        path = getattr(f, "name", None)
        if path and os.path.isfile(path):
            file_paths.append(path)

    summary = process_srt_files(file_paths, output_dir)
    # Simple aggregate stats
    total_segments = sum(x.get("segments", 0) for x in summary["files"])
    summary["total_segments"] = total_segments
    summary["file_count"] = len(summary["files"])
    return summary


def srt_tools_ui():
    gr.Markdown(
        """
    # SRT Tools

    Import and parse multiple `.srt` subtitle files at once. Each file is processed sequentially and saved
    as a JSON list of segments (`index`, `start`, `end`, `text`). This prepares structured input for later TTS batching.

    1. Select one or more `.srt` files.
    2. Optionally set an output directory (else a `processed_srt` folder is used inside the extension).
    3. Click 'Import & Process SRTs'.

    TTS integration is intentionally deferred. TODO: For each segment, route text into chosen voice pipeline.
    """
    )

    with gr.Row():
        srt_files = gr.Files(label="SRT files", file_types=[".srt"], file_count="multiple")
        output_dir = gr.Textbox(label="Output directory (optional)", placeholder="Leave blank to use default processed_srt")

    process_btn = gr.Button("Import & Process SRTs", variant="primary")
    summary_json = gr.JSON(label="Processing Summary")

    process_btn.click(
        fn=multi_srt_import,
        inputs=[srt_files, output_dir],
        outputs=[summary_json],
        api_name="multi_srt_import",
    )


def extension__tts_generation_webui():
    srt_tools_ui()
    
    return {
        "package_name": "tts_webui_extension.srt_tools",
        "name": "SRT Tools",
        "requirements": "git+https://github.com/rsxdalv/tts_webui_extension.srt_tools@main",
        "description": "Import and parse multiple SRT files into JSON segments for later TTS batching.",
        "extension_type": "interface",
        "extension_class": "tools",
        "author": "rsxdalv",
        "extension_author": "rsxdalv",
        "license": "MIT",
        "website": "https://github.com/rsxdalv/tts_webui_extension.srt_tools",
        "extension_website": "https://github.com/rsxdalv/tts_webui_extension.srt_tools",
        "extension_platform_version": "0.0.1",
    }


if __name__ == "__main__":
    if "demo" in locals():
        locals()["demo"].close()
    with gr.Blocks() as demo:
        with gr.Tab("SRT Tools", id="srt_tools"):
            srt_tools_ui()

    demo.launch(
        server_port=7772,  # Change this port if needed
    )
