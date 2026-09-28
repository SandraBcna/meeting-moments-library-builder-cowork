# Customer deployment

## Fastest path

1. Install the skill in Cowork.
2. Start a new Cowork session.
3. Attach authorized transcripts or caption files.
4. Ask Cowork to build the desired library type.
5. Review the proposed moments.
6. Approve, edit, hold, or reject each candidate.
7. Download the HTML, CSV, and JSON files.
8. Optionally upload the approved files to SharePoint or OneDrive after confirming the
   exact destination.

## No infrastructure required

The default path does not require:

- Scout;
- a Power Platform environment;
- Dataverse;
- an MCP server;
- a public tunnel;
- a deployed Copilot Studio agent; or
- a custom website host.

## Inputs

Preferred: WebVTT or SRT captions because they contain exact timestamps.

Supported:

- `.vtt`;
- `.srt`;
- `.txt` transcripts or notes;
- pasted transcript text;
- audio/video if Cowork can transcribe it in the customer's runtime; and
- an existing library JSON file for updates.

## Outputs

The three files are portable and can be:

- opened locally;
- attached to email or Teams under organization policy;
- stored in OneDrive or SharePoint;
- imported into Microsoft Lists from CSV; or
- used later as the source for an agent or application.

## Acceptance checklist

- [ ] Skill is visible in a new Cowork session
- [ ] VTT or SRT timestamps parse correctly
- [ ] Capture criteria are confirmed
- [ ] Every entry has transcript evidence
- [ ] No presenter is guessed
- [ ] Review table is shown before final generation
- [ ] Only approved and verified entries appear in HTML
- [ ] CSV and JSON contain consistent IDs and timestamps
- [ ] No full transcript text appears in final files
- [ ] Recording links are HTTPS and retain original permissions
- [ ] Optional SharePoint/OneDrive upload is explicitly confirmed

## Optional next phase

After the portable library proves useful, the customer may separately choose to:

- import CSV into Microsoft Lists;
- ground a declarative agent on approved entries;
- build a live SharePoint or Dataverse experience; or
- schedule a recurring curation process with human approval.

Do not lead with these options. Ship the simple portable library first.
