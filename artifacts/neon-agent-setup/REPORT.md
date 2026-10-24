# Relas — Neon agent tooling setup

## Requested skill

Fetched HTTP 200 from the exact requested URL:
https://neon.com/.well-known/agent-skills/neon/SKILL.md

The fetched content matched the existing cached `neon` skill after line-ending normalization. SHA-256: `bffc8ca162bd668262a17bb6b098a0519c168f1ceb3e5194773d31bd86b30048`.

Instructions followed: inspect existing tooling/configuration first; preserve project linking and application architecture; install only missing tooling; use OAuth for project-scoped MCP instead of storing an API key; do not launch browser login unattended or create a replacement database/project.

## Initial findings

- A cached Neon plugin, version 2.3.0, contained nine skill directories and `mcp.json` for `https://mcp.neon.tech/mcp`.
- User Codex config had `plugins."neon-postgres@plugins-cli".enabled=true`.
- However, `codex plugin list --json` did **not** report Neon as an installed plugin, and `codex mcp list --json` reported no Neon server. Cached files and a config entry were not accepted as proof of a working registration.
- No project-level `.agents/skills`, `.codex/config.toml`, or MCP overrides existed at the start.
- Existing `.neon` links to the requested organization/project and branch `production`. It was preserved.
- The Neon CLI now reports an authenticated profile. No account identifiers, credentials or connection strings were printed or copied into project configuration.

## Changes made in this setup task

1. Created a backup outside the repository at `~/.codex/.tmp/relas-neon-setup-20261024-203034/`. It preserves the existing `.gitignore`, `.neon`, `neon.ts`, `package.json`, `package-lock.json` and user Codex config, plus hashes. The backup is not committed or copied into this project.
2. Installed the two relevant agent skills for Codex in this project:
   - `.agents/skills/neon/`
   - `.agents/skills/neon-postgres/`
   Their supporting references are included. `verification.json` lists every installed file.
3. Created `skills-lock.json` with the installer’s source/integrity metadata.
4. Created `.codex/config.toml` with a single project MCP entry:

```toml
[mcp_servers.Neon]
type = "http"
url = "https://mcp.neon.tech/mcp?projectId=shy-art-03849128"
```

   This is OAuth URL-only configuration, pinned to the existing project. No token, API key, DATABASE_URL or password was written into it.
5. Added the trust entry for **only Relas** to `~/.codex/config.toml`, after the user explicitly approved ?Trust only the Relas project?. Every byte of the previous user config remains as an unchanged prefix. No other project's trust setting was changed. The exact added path and backup hashes are recorded in the private backup.
6. Added this report and `verification.json` under `artifacts/neon-agent-setup/`.

The existing cached plugin and unrelated MCP integrations were retained. No application code, database, migration, runtime dependencies, `neon.ts`, project link or existing npm manifest was changed. No Neon service was deployed and no database branch was created or switched. Nothing was committed or pushed in this setup task.

## Installation commands and workaround

The first skill install using nested `npx -c` failed with `npm EUSAGE` before installing skills. It did not justify changing the app’s Node or Python versions.

Successful retry: used the already downloaded Node 22.20.0 binary to run the installed Neon CLI directly, with its directory added only to the temporary shell PATH:

```text
neon skills -s neon -s neon-postgres --agent codex -y
neon mcp --oauth --project --agent codex --project-id shy-art-03849128 -y
```

Both commands reported installed. The system Node version and permanent PATH were not changed. The MCP command requires no CLI-generated API key.

## Preservation verification

SHA-256 comparisons against the backup confirmed byte-for-byte preservation of:

- `.gitignore`
- `.neon`
- `neon.ts`
- `package.json`
- `package-lock.json`

The user Codex config was initially byte-identical, then received only the approved appended Relas trust entry. `codex-before-trust.toml` preserves its exact previous contents outside the repository.

Pre-existing uncommitted migration/setup files were left intact. New files contain agent instructions, source metadata and the public MCP endpoint; they do not contain credentials.

## Runtime verification and current status

**Installed and recognized by Codex. MCP OAuth approval is pending on first use.**

The initial read-only app-server `config/read` returned a disabled project layer because Relas was not trusted. The user was asked before changing this security setting, and explicitly approved trusting only this project.

After adding that one entry:

- `codex mcp list --json` reports `Neon`, `enabled=true`, transport `streamable_http`, pinned to the existing project.
- MCP auth status is `not_logged_in`, as expected for OAuth URL-only setup. No bearer-token field or header is configured.
- App-server `skills/list` recognizes **neon** and **neon-postgres** at repo scope, both enabled, with **zero discovery errors**.
- Existing unrelated MCP entries remain present.
- The existing project link, Neon service config, npm manifests and ignore file remain byte-for-byte unchanged.

Start/reload a Codex session in this repository to load the new skills/tools into the session. Complete Neon OAuth when prompted; alternatively run `codex mcp login Neon` yourself from this project. CLI login is already detected and is distinct from the MCP authorization. No live MCP database operation or OAuth handshake was claimed. The skill instructs: ?An unattended agent must not launch browser authentication.?

The generic `debug prompt-input` output did not expose the skills catalog; the authoritative app-server `skills/list` discovery check above was used instead.

Official Codex configuration guidance: https://developers.openai.com/codex/config-basic
Official MCP guidance: https://developers.openai.com/codex/mcp

## Evidence

[verification.json](verification.json) includes every installed file, the endpoint, preservation checks, the user-approved trust change, and final runtime discovery/authentication states. Existing SQLite and all Relas data remain unchanged. No deployment, schema migration, commit or push was performed in this setup task.
