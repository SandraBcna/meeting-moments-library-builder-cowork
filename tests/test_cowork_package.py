import base64
import csv
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
import urllib.parse


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
CONFIG = ROOT / "assets" / "library-config.example.json"


def run_script(name, *args):
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *map(str, args)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


class TranscriptParserTests(unittest.TestCase):
    def test_vtt_parser_preserves_timing_and_evidenced_speaker(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            source = root / "meeting.vtt"
            output = root / "segments.json"
            source.write_text(
                """WEBVTT

00:00:01.000 --> 00:00:04.500
<v Alex Example>Open the configuration page.

00:00:04.500 --> 00:00:08.000
Select the approved option.
""",
                encoding="utf-8",
            )
            run_script(
                "parse_transcript.py",
                "--input",
                source,
                "--output",
                output,
                "--source-label",
                "Weekly Demo",
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(2, payload["timedSegmentCount"])
            self.assertEqual("Alex Example", payload["segments"][0]["speaker"])
            self.assertEqual(1.0, payload["segments"][0]["startSeconds"])
            self.assertNotIn("<v", payload["segments"][0]["text"])

    def test_srt_parser_accepts_comma_timestamps(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            source = root / "meeting.srt"
            output = root / "segments.json"
            source.write_text(
                """1
00:01:02,500 --> 00:01:05,000
The group approved the proposal.
""",
                encoding="utf-8",
            )
            run_script(
                "parse_transcript.py", "--input", source, "--output", output
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(62.5, payload["segments"][0]["startSeconds"])

    def test_plain_text_is_marked_untimed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            source = root / "notes.txt"
            output = root / "segments.json"
            source.write_text("First paragraph.\n\nSecond paragraph.", encoding="utf-8")
            run_script(
                "parse_transcript.py", "--input", source, "--output", output
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(0, payload["timedSegmentCount"])
            self.assertFalse(payload["segments"][0]["timed"])


class LibraryBuilderTests(unittest.TestCase):
    def make_config(self, root):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        path = root / "config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        return path

    def test_outputs_are_consistent_and_html_shows_only_publishable_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            config = self.make_config(root)
            entries = [
                {
                    "title": "How to configure the approved option",
                    "captureType": "how-to",
                    "session": "Weekly Demo",
                    "date": "2026-01-15",
                    "presenter": "Alex Example",
                    "startSeconds": 720,
                    "endSeconds": 960,
                    "recordingUrl": (
                        "https://contoso.sharepoint.com/_layouts/15/stream.aspx"
                        "?id=%2Fsites%2Fteam%2Fdemo.mp4&share=approved-link"
                    ),
                    "outcome": "Shows the configuration and validation steps.",
                    "category": "Configuration",
                    "verification": "verified",
                    "approval": "approved",
                    "sourceLabel": "Weekly Demo transcript",
                },
                {
                    "title": "Held private discussion",
                    "captureType": "how-to",
                    "session": "Private Review",
                    "startSeconds": 60,
                    "recordingUrl": "https://contoso.example/private",
                    "outcome": "Not approved for publication.",
                    "verification": "verified",
                    "approval": "held",
                },
            ]
            source = root / "entries.json"
            source.write_text(json.dumps(entries), encoding="utf-8")
            out = root / "output"
            result = run_script(
                "build_library.py",
                "--entries",
                source,
                "--config",
                config,
                "--out-dir",
                out,
            )
            summary = json.loads(result.stdout)
            self.assertEqual(1, summary["approvedForHtml"])

            payload = json.loads(
                (out / "meeting-moments-library.json").read_text(encoding="utf-8")
            )
            self.assertEqual(2, len(payload["entries"]))
            approved = payload["entries"][0]
            query = urllib.parse.parse_qs(
                urllib.parse.urlparse(approved["recordingUrl"]).query
            )
            nav = json.loads(base64.b64decode(query["nav"][0]))
            self.assertEqual(720, nav["playbackOptions"]["startTimeInSeconds"])

            with (out / "meeting-moments-library.csv").open(
                encoding="utf-8-sig", newline=""
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(2, len(rows))

            page = (out / "meeting-moments-library.html").read_text(
                encoding="utf-8"
            )
            self.assertIn("How to configure the approved option", page)
            self.assertNotIn("Held private discussion", page)

    def test_html_escapes_script_content_and_unsafe_url_is_not_published(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            config = self.make_config(root)
            entries = [
                {
                    "title": "</script><script>alert(1)</script>",
                    "captureType": "custom",
                    "session": "Demo",
                    "startSeconds": 1,
                    "recordingUrl": "javascript:alert(1)",
                    "outcome": "Unsafe input test.",
                    "verification": "verified",
                    "approval": "approved",
                }
            ]
            source = root / "entries.json"
            source.write_text(json.dumps(entries), encoding="utf-8")
            out = root / "output"
            result = run_script(
                "build_library.py",
                "--entries",
                source,
                "--config",
                config,
                "--out-dir",
                out,
            )
            summary = json.loads(result.stdout)
            self.assertEqual(0, summary["approvedForHtml"])
            page = (out / "meeting-moments-library.html").read_text(
                encoding="utf-8"
            )
            self.assertNotIn("</script><script>alert(1)</script>", page)
            payload = json.loads(
                (out / "meeting-moments-library.json").read_text(encoding="utf-8")
            )
            self.assertEqual("", payload["entries"][0]["recordingUrl"])

    def test_missing_required_field_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            config = self.make_config(root)
            source = root / "entries.json"
            source.write_text(json.dumps([{"title": "Incomplete"}]), encoding="utf-8")
            with self.assertRaises(subprocess.CalledProcessError):
                run_script(
                    "build_library.py",
                    "--entries",
                    source,
                    "--config",
                    config,
                    "--out-dir",
                    root / "output",
                )

    def test_template_json_files_are_valid(self):
        json.loads(CONFIG.read_text(encoding="utf-8"))
        json.loads((ROOT / "assets" / "entries.example.json").read_text(encoding="utf-8"))
        json.loads((ROOT / "metadata.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
