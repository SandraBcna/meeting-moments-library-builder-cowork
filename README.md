# Meeting Moments Library Builder for Cowork

Create a searchable library of the valuable moments buried in meeting recordings—without
deploying infrastructure.

Cowork reads the meeting transcripts or captions you provide, proposes verified moments,
asks you to approve them, and returns:

- a searchable HTML library;
- a CSV ready for Microsoft Lists or another system; and
- a JSON source of truth.

Nothing is cut or re-hosted. Entries point back to the original recording and include the
verified timestamp.

## Validation status

Version **1.0.0** passed:

- seven neutral fixture tests;
- CAT Agent Skills metadata validation and production site build;
- bundle inspection confirming no tests, caches, private identifiers, or internal host
  assumptions; and
- a real Cowork acceptance test using a synthetic VTT transcript.

In the Cowork test, the skill invoked successfully, selected the correct timestamped
how-to, excluded an unrelated decision, displayed the review table, required explicit
approval, and generated HTML, CSV, and JSON with one approved entry and zero warnings.

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

Attach one or more `.vtt`, `.srt`, or `.txt` transcripts, or content Cowork can access,
then ask:

> Build a how-to library from these meeting transcripts.

The skill asks what kind of moments to capture, shows every proposed entry for approval,
then delivers the three files.

Other capture types include decision logs, customer voice, demo highlights, lessons
learned, onboarding moments, and custom criteria.

## Customer deployment

The default deployment requires:

- Microsoft 365 Copilot Cowork with custom skills;
- meeting transcripts, captions, or recordings the user is authorized to use; and
- no external server, Dataverse environment, MCP tool, tunnel, or separate agent.

See `references/customer-deployment.md`.

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
