import os
import importlib.util


def import_srt_tools():
    # Locate the extension main.py within the extension folder
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tts_webui_extension', 'srt_tools', 'main.py'))
    spec = importlib.util.spec_from_file_location('srt_tools_main', base)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def test_parse_srt_basic():
    mod = import_srt_tools()
    srt = """1\n00:00:01,000 --> 00:00:03,500\nHello world.\n\n2\n00:00:04,000 --> 00:00:05,000\nSecond line here\n"""
    segments = mod.parse_srt_content(srt)
    assert isinstance(segments, list)
    assert len(segments) == 2
    assert segments[0]['index'] == 1
    assert segments[0]['start'] == '00:00:01,000'
    assert segments[0]['end'] == '00:00:03,500'
    assert 'Hello world' in segments[0]['text']


def test_parse_srt_tolerant_missing_index():
    mod = import_srt_tools()
    srt = """00:00:00,000 --> 00:00:01,000\nNo index line\n\n99\n00:00:01,000 --> 00:00:02,000\nWith index\n"""
    segments = mod.parse_srt_content(srt)
    # Should parse both blocks and reindex sequentially
    assert len(segments) == 2
    assert segments[0]['index'] == 1
    assert segments[1]['index'] == 2


def test_parse_srt_ignores_malformed():
    mod = import_srt_tools()
    srt = """1\nThis is not a timecode line\nText\n\n2\n00:00:01,000 --> 00:00:02,000\nValid block\n"""
    segments = mod.parse_srt_content(srt)
    assert len(segments) == 1
    assert segments[0]['text'].startswith('Valid')
