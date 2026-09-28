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
            self.assertEqual(1, len(payload["entries"]))
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
            self.assertEqual(1, len(rows))
            self.assertEqual(
                "How to configure the approved option", rows[0]["title"]
            )

            page = (out / "meeting-moments-library.html").read_text(
                encoding="utf-8"
            )
            self.assertIn("How to configure the approved option", page)
            self.assertNotIn("Held private discussion", page)
            self.assertNotIn(
                "Held private discussion",
                (out / "meeting-moments-library.json").read_text(
                    encoding="utf-8"
                ),
            )
            self.assertNotIn(
                "Held private discussion",
                (out / "meeting-moments-library.csv").read_text(
                    encoding="utf-8-sig"
                ),
            )

    def test_nonapproved_states_are_excluded_from_all_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            config = self.make_config(root)
            entries = []
            for index, (verification, approval) in enumerate(
                (
                    ("verified", "held"),
                    ("verified", "rejected"),
                    ("needs-review", "approved"),
                    ("blocked", "approved"),
                ),
                1,
            ):
                entries.append(
                    {
                        "title": f"Excluded candidate {index}",
                        "captureType": "how-to",
                        "session": "Review",
                        "startSeconds": index,
                        "recordingUrl": f"https://contoso.example/{index}",
                        "outcome": "Must not leave the review gate.",
                        "verification": verification,
                        "approval": approval,
                    }
                )
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
            self.assertEqual(4, summary["candidatesProcessed"])
            self.assertEqual(0, summary["entriesPublished"])
            payload = json.loads(
                (out / "meeting-moments-library.json").read_text(encoding="utf-8")
            )
            self.assertEqual([], payload["entries"])
            with (out / "meeting-moments-library.csv").open(
                encoding="utf-8-sig", newline=""
            ) as handle:
                self.assertEqual([], list(csv.DictReader(handle)))
            page = (out / "meeting-moments-library.html").read_text(
                encoding="utf-8"
            )
            self.assertNotIn("Excluded candidate", page)

    def test_unsafe_url_rejects_entry_before_output(self):
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
            with self.assertRaises(subprocess.CalledProcessError):
                run_script(
                    "build_library.py",
                    "--entries",
                    source,
                    "--config",
                    config,
                    "--out-dir",
                    out,
                )
            self.assertFalse((out / "meeting-moments-library.html").exists())
            self.assertFalse((out / "meeting-moments-library.json").exists())

    def test_entry_without_recording_link_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            config = self.make_config(root)
            source = root / "entries.json"
            source.write_text(
                json.dumps(
                    [
                        {
                            "title": "Transcript-only candidate",
                            "captureType": "how-to",
                            "session": "Demo",
                            "startSeconds": 15,
                            "outcome": "Verified in the transcript but no recording exists.",
                            "verification": "verified",
                            "approval": "approved",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            out = root / "output"
            with self.assertRaises(subprocess.CalledProcessError):
                run_script(
                    "build_library.py",
                    "--entries",
                    source,
                    "--config",
                    config,
                    "--out-dir",
                    out,
                )
            self.assertFalse((out / "meeting-moments-library.json").exists())

    def test_malformed_and_credential_bearing_urls_are_validation_issues(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            config = self.make_config(root)
            for index, recording_url in enumerate(
                (
                    "https://[",
                    "https://user:password@contoso.example/recording",
                    "https://contoso.example:99999/recording",
                    "https://contoso.example/\nrecording",
                )
            ):
                with self.subTest(recording_url=recording_url):
                    source = root / f"entries-{index}.json"
                    source.write_text(
                        json.dumps(
                            [
                                {
                                    "title": "Unsafe URL",
                                    "captureType": "custom",
                                    "session": "Demo",
                                    "startSeconds": 1,
                                    "recordingUrl": recording_url,
                                    "outcome": "URL validation test.",
                                    "verification": "verified",
                                    "approval": "approved",
                                }
                            ]
                        ),
                        encoding="utf-8",
                    )
                    out = root / f"output-{index}"
                    with self.assertRaises(subprocess.CalledProcessError):
                        run_script(
                            "build_library.py",
                            "--entries",
                            source,
                            "--config",
                            config,
                            "--out-dir",
                            out,
                        )
                    self.assertFalse(
                        (out / "meeting-moments-library.json").exists()
                    )

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

    def test_fractional_timestamps_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            config = self.make_config(root)
            source = root / "entries.json"
            source.write_text(
                json.dumps(
                    [
                        {
                            "title": "Precise moment",
                            "captureType": "how-to",
                            "session": "Demo",
                            "startSeconds": 5.5,
                            "endSeconds": 34.75,
                            "recordingUrl": "https://contoso.example/demo",
                            "outcome": "Preserves transcript timing.",
                            "verification": "verified",
                            "approval": "approved",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            out = root / "output"
            run_script(
                "build_library.py",
                "--entries",
                source,
                "--config",
                config,
                "--out-dir",
                out,
            )
            entry = json.loads(
                (out / "meeting-moments-library.json").read_text(encoding="utf-8")
            )["entries"][0]
            self.assertEqual(5.5, entry["startSeconds"])
            self.assertEqual(34.75, entry["endSeconds"])
            self.assertEqual(29.25, entry["durationSeconds"])
            self.assertEqual("0:05.5", entry["startTimestamp"])

    def test_invalid_duration_and_over_limit_entries_fail_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            config = self.make_config(root)
            for duration in ("five", 301):
                with self.subTest(duration=duration):
                    source = root / f"entries-{duration}.json"
                    source.write_text(
                        json.dumps(
                            [
                                {
                                    "title": "Invalid duration",
                                    "captureType": "how-to",
                                    "session": "Demo",
                                    "startSeconds": 0,
                                    "durationSeconds": duration,
                                    "recordingUrl": "https://contoso.example/demo",
                                    "outcome": "Validation test.",
                                    "verification": "verified",
                                    "approval": "approved",
                                }
                            ]
                        ),
                        encoding="utf-8",
                    )
                    with self.assertRaises(subprocess.CalledProcessError):
                        run_script(
                            "build_library.py",
                            "--entries",
                            source,
                            "--config",
                            config,
                            "--out-dir",
                            root / f"output-{duration}",
                        )

    def test_output_base_name_cannot_escape_output_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            config_data = json.loads(CONFIG.read_text(encoding="utf-8"))
            config_data["output"]["baseName"] = "../../outside"
            config = root / "config.json"
            config.write_text(json.dumps(config_data), encoding="utf-8")
            source = root / "entries.json"
            source.write_text(
                json.dumps(
                    [
                        {
                            "title": "Safe entry",
                            "captureType": "how-to",
                            "session": "Demo",
                            "startSeconds": 0,
                            "recordingUrl": "https://contoso.example/demo",
                            "outcome": "Should not be written outside output.",
                            "verification": "verified",
                            "approval": "approved",
                        }
                    ]
                ),
                encoding="utf-8",
            )
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
            self.assertFalse((root.parent / "outside.json").exists())

    def test_csv_formula_fields_are_neutralized(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            config = self.make_config(root)
            source = root / "entries.json"
            source.write_text(
                json.dumps(
                    [
                        {
                            "title": "=HYPERLINK(\"https://bad.example\")",
                            "captureType": "custom",
                            "session": "+SUM(1,1)",
                            "startSeconds": 0,
                            "recordingUrl": "https://contoso.example/demo",
                            "outcome": "@unsafe",
                            "verification": "verified",
                            "approval": "approved",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            out = root / "output"
            run_script(
                "build_library.py",
                "--entries",
                source,
                "--config",
                config,
                "--out-dir",
                out,
            )
            with (out / "meeting-moments-library.csv").open(
                encoding="utf-8-sig", newline=""
            ) as handle:
                row = next(csv.DictReader(handle))
            self.assertTrue(row["title"].startswith("'="))
            self.assertTrue(row["session"].startswith("'+"))
            self.assertTrue(row["outcome"].startswith("'@"))

    def test_json_privacy_setting_removes_evidence_notes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            config_data = json.loads(CONFIG.read_text(encoding="utf-8"))
            config_data["output"]["includeEvidenceNotesInJson"] = False
            config = root / "config.json"
            config.write_text(json.dumps(config_data), encoding="utf-8")
            source = root / "entries.json"
            source.write_text(
                json.dumps(
                    [
                        {
                            "title": "Privacy setting",
                            "captureType": "how-to",
                            "session": "Demo",
                            "startSeconds": 0,
                            "recordingUrl": "https://contoso.example/demo",
                            "outcome": "Evidence note should be omitted.",
                            "verification": "verified",
                            "approval": "approved",
                            "evidenceNote": "Sensitive supporting detail",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            out = root / "output"
            run_script(
                "build_library.py",
                "--entries",
                source,
                "--config",
                config,
                "--out-dir",
                out,
            )
            entry = json.loads(
                (out / "meeting-moments-library.json").read_text(encoding="utf-8")
            )["entries"][0]
            self.assertNotIn("evidenceNote", entry)

    def test_generated_controls_have_accessible_names(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            config = self.make_config(root)
            source = root / "entries.json"
            source.write_text("[]", encoding="utf-8")
            out = root / "output"
            run_script(
                "build_library.py",
                "--entries",
                source,
                "--config",
                config,
                "--out-dir",
                out,
            )
            page = (out / "meeting-moments-library.html").read_text(
                encoding="utf-8"
            )
            self.assertIn('aria-label="Search moments"', page)
            self.assertIn('aria-label="Filter by category"', page)

    def test_template_json_files_are_valid(self):
        json.loads(CONFIG.read_text(encoding="utf-8"))
        json.loads((ROOT / "assets" / "entries.example.json").read_text(encoding="utf-8"))
        metadata = json.loads((ROOT / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(["Cowork"], metadata["platforms"])
        self.assertEqual("1.2.0", metadata["version"])
        self.assertTrue((ROOT / "references" / "meeting-discovery.md").exists())
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        discovery = (ROOT / "references" / "meeting-discovery.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("excludes the meeting before candidate extraction", skill)
        self.assertIn("skip the meeting before", discovery)
        self.assertNotIn("authorized recording/recap URL", readme)
        self.assertIn(
            "resolve the correct transcript and recording file automatically",
            readme,
        )
        version = metadata["version"]
        self.assertIn(f"v{version}", readme)
        self.assertIn(f"/releases/download/v{version}/", readme)
        self.assertNotRegex(readme, r"\bv(?!1\.2\.0)\d+\.\d+\.\d+\b")


if __name__ == "__main__":
    unittest.main()
