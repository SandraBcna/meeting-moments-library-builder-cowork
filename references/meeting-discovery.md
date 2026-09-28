# Cowork meeting and transcript discovery

## Goal

Find authorized meeting occurrences and their transcripts without requiring the customer
to export files manually. Discovery is bounded and user-directed; it is not a tenant-wide
scan.

## Required scope

Before searching, obtain:

- start and end dates;
- one or more meeting series, titles, organizers, or keywords;
- capture type;
- whether external meetings are allowed; and
- maximum number of meetings to inspect in one run.

Default to external meetings excluded and a maximum of 10 candidate meetings unless the
user chooses otherwise.

## Discovery sequence

Use equivalent native Microsoft 365 capabilities when tool names differ.

1. Call `workiq_list_meetings(startDate, endDate)` for the bounded window.
2. Filter locally using the approved title, series, organizer, or keyword criteria.
3. Present candidates before reading transcripts when multiple meetings match.
4. After selection, call `workiq_list_meeting_transcripts` using the strongest available
   meeting identifier:
   - `onlineMeetingId`;
   - `joinUrl`;
   - `joinMeetingId`; or
   - `calendarEventId`.
5. Match transcript metadata to the selected occurrence/date. Never assume the first
   transcript belongs to the intended recurring occurrence.
6. Call `workiq_get_meeting_transcript` using the selected `onlineMeetingId` and
   `transcriptId`.
7. Follow `nextSegmentIndex` until all required segments are read or the configured
   maximum is reached.
8. Record transcript availability and any speaker-attribution limitation.

## Recording or recap link

Transcript access and recording-link access are separate.

- Use a durable recording or recap URL only when native metadata or attached work context
  provides it.
- Never substitute a Teams join URL for a recording URL.
- Never derive, scrape, or manufacture an access token.
- If the transcript is available but the recording URL is not, the candidate may be
  reviewed but must stay `needs-review` or `held` until the user supplies or approves a
  durable link.

## Fallbacks

If native discovery is unavailable:

1. Ask the user to add the meeting as Cowork work context.
2. Ask for the transcript/captions (`.vtt`, `.srt`, `.txt`).
3. Ask for the authorized recording or recap link.
4. Continue with the attachment workflow.

Report whether the blocker is:

- no meeting match;
- no transcript object;
- transcript permission denied;
- transcript content unavailable;
- recording/recap link unavailable; or
- runtime meeting capability unavailable.

Do not collapse these into “no transcript found.”

## Privacy

- Treat meeting metadata and transcript text as private user data.
- Use transcript content only to verify candidate moments.
- Do not include full transcript segments in the final library.
- Do not inspect unrelated meetings outside the approved scope.
- Do not change meeting responses, membership, sharing, or retention.

