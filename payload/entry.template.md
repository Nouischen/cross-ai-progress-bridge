<!-- CROSS-AI-PROGRESS-BRIDGE:START -->
# Cross-AI Progress Bridge

Mode: {{MODE}}
Trigger prefix: {{TRIGGER_PREFIX_DISPLAY}}

When the user uses a Cross-AI Progress Bridge command, first read
`.ai-progress/INSTRUCTIONS.md` and follow it. Canonical task data lives under
`AI_PROGRESS/` as local Markdown files.

{{TRIGGER_RULE}}

Never store passwords, API keys, unredacted medical records, or other sensitive
personal data in progress files. All writes use per-task locks and revision guards.
<!-- CROSS-AI-PROGRESS-BRIDGE:END -->
