# Meeting Moments Library Builder for Cowork

Create a searchable library of the valuable moments buried in meeting recordings—without
deploying infrastructure.

Cowork searches the authorized Microsoft 365 meeting window and series you choose, reads
available transcripts for the selected meetings, proposes verified moments, asks you to
approve them, and returns:

- a searchable HTML library;
- a CSV ready for Microsoft Lists or another system; and
- a JSON source of truth.

Nothing is cut or re-hosted. Entries point back to the original recording and include the
verified timestamp.

## Validation status

Version **1.2.0** adds discovery-first meeting/transcript retrieval and mandatory automatic
recording-link resolution. Cowork only extracts candidates after both the transcript and a
matching authorized recording file are available. Attachment upload remains available
when native transcript access is blocked, but users are never asked to find recording URLs.
This release also includes all fixes requested by the Copilot review on CAT Agent Skills
PR #347.

Validation now includes:

- fifteen neutral fixture and security regression tests;
- CAT Agent Skills metadata validation and production site build;
- bundle inspection confirming no tests, caches, private identifiers, or internal host
  assumptions; and
- a real Cowork acceptance test using a synthetic VTT transcript.
- bounded Microsoft 365 meeting discovery;
- successful transcript-object discovery for an organizer-owned meeting; and
- a verified permission-denied fallback for a meeting whose transcript was not accessible.
- automatic recording-file resolution through authorized Microsoft 365 file search.

The real Cowork discovery-only test invoked the custom skill, found the exact bounded
calendar occurrence, confirmed one associated transcript object, and completed without
reading, quoting, summarizing, or displaying transcript content.

A separate automatic resolver test used a recurring meeting series with multiple
occurrences. Cowork selected the intended occurrence, matched the transcript by creation
time rather than array order, found the corresponding authorized MP4 in Microsoft 365
file search, distinguished it from the previous week's recording, and returned the
existing recording URL without asking for manual input. No transcript content was read.

In the Cowork test, the skill invoked successfully, selected the correct timestamped
how-to, excluded an unrelated decision, displayed the review table, required explicit
approval, and generated HTML, CSV, and JSON with one approved entry and zero warnings.

Security and quality regression coverage includes output-path traversal, CSV formula
injection, fractional timestamps, invalid and over-limit durations, accessible controls,
evidence-note privacy settings, malformed and credential-bearing URLs, unsafe links,
HTML/script injection, and required-field validation.

## Install

### Option A — CAT Agent Skills gallery

Download the skill bundle from the CAT Agent Skills gallery when published.

### Option B — OneDrive

1. Download and unzip the bundle.
2. Copy the complete `meeting-moments-library-builder-cowork` folder to:

   `Documents/Cowork/skills/meeting-moments-library-builder-cowork/`

3. Start a new Cowork session.

### Option C — Ask Cowork

Attach the downloaded bundle in Cowork and ask it to install the custom skill.

Keep the folder name unchanged; it must match the `name` in `SKILL.md`.

## Use

Ask Cowork to search a bounded date range and named meeting series:

> Build a how-to library from the Architecture Office Hours meetings in the last 30 days.

The skill shows matching meetings, asks which ones to process when needed, reads accessible
transcripts, shows every proposed entry for approval, then delivers the three files.

If Cowork cannot reach a transcript or durable recording link, attach `.vtt`, `.srt`, or
`.txt` captions and the authorized recording/recap URL.

Because this is a video library, Cowork only extracts candidates after it has automatically
resolved both the transcript and the recording file. Meetings with transcripts but no
accessible recording are skipped and reported as blockers. Users may attach captions when
transcript access is blocked, but they are not asked to find recording links manually.

Other capture types include decision logs, customer voice, demo highlights, lessons
learned, onboarding moments, and custom criteria.

## Customer deployment

The default deployment requires:

- Microsoft 365 Copilot Cowork with custom skills;
- meeting transcripts, captions, or recordings the user is authorized to use; and
- no external server, Dataverse environment, MCP tool, tunnel, or separate agent.

Native meeting discovery depends on the customer's Microsoft 365 permissions and Cowork
runtime capabilities. The skill reports access blockers and falls back to attachments
rather than silently returning an empty library.

### Fastest customer deployment

1. Install the skill from CAT Agent Skills or upload its ZIP in Cowork.
2. Start a new Cowork session.
3. Ask Cowork to search an authorized date window and named meeting series.
4. Select meetings when multiple occurrences match.
5. Let Cowork read accessible transcripts; attach captions only for blocked meetings.
6. Review, approve, edit, hold, or reject proposed moments.
7. Download the HTML, CSV, and JSON files.
8. Optionally upload approved files to SharePoint or OneDrive after confirming the exact
   destination.

### Acceptance checklist

- [ ] Skill is visible in a new Cowork session
- [ ] Bounded discovery returns the intended meeting series
- [ ] Transcript metadata resolves to the correct occurrence
- [ ] Transcript segments are readable or an attachment fallback is offered
- [ ] Every candidate has transcript evidence and an exact timestamp
- [ ] No presenter is guessed
- [ ] Review is shown before final generation
- [ ] Only approved, verified entries with HTTPS recording links appear in HTML
- [ ] CSV and JSON contain consistent IDs and timestamps
- [ ] Full transcript text is absent from final files
- [ ] Optional upload is explicitly confirmed

## Privacy

- Access does not automatically grant permission to republish.
- The output contains meeting titles, names, timestamps, and recording links when approved.
- Recording links retain their original permissions.
- Full transcript text is not included in the generated library.
- External-customer content stays excluded unless explicitly approved.
- SharePoint or OneDrive upload is optional and confirmation-gated.

## Code-workspace fallback

The Python scripts use only the standard library. Customers without Cowork custom skills
can run them in a code workspace against exported VTT/SRT/TXT files. That mode builds the
portable files but does not discover meetings or publish to Microsoft 365 automatically.

## Support boundary

This community skill is provided as-is under MIT. It is not an official Microsoft product,
certification, or support commitment. Customers remain responsible for recording consent,
privacy, information protection, retention, licensing, and approval to publish content.
