# Cross-machine memory

These files are a synced mirror of the Claude Code auto-memory for this
project, kept in the repo so they travel between machines.

## What's in here

- `MEMORY.md` — the index Claude Code loads at session start. Each line
  points at one of the per-topic memory files below.
- `project_*.md` — durable project facts (architecture state, theme
  taxonomy, etc.).
- `feedback_*.md` — accumulated style and delivery preferences (doc
  format, story actionability bar, clean-canonical-doc preference,
  etc.).

These are read by Claude Code automatically — you don't need to
reference them when prompting. The point of mirroring them in the repo
is so they are not lost when you switch machines.

## Installing on a new machine

Claude Code looks for memory at:

    ~/.claude/projects/<encoded-cwd>/memory/

where `<encoded-cwd>` is your working directory with `/` replaced by
`-`. If you clone this repo to `/home/<you>/optum_labreqs` the encoded
path is `-home-<you>-optum-labreqs`. If you clone it to
`/Users/<you>/optum_labreqs` (Mac) the encoded path is
`-Users-<you>-optum-labreqs`.

To install:

    # 1. Pick the target dir based on YOUR cwd on this machine.
    #    Example for /home/rajneesh/optum_labreqs:
    TARGET=~/.claude/projects/-home-rajneesh-optum-labreqs/memory

    # 2. Create it and copy.
    mkdir -p "$TARGET"
    cp memory/*.md "$TARGET/"

After that, Claude Code on the new machine will pick up the memory
automatically next session.

## Keeping the mirror in sync

When Claude updates a memory file in
`~/.claude/projects/.../memory/` during a session, the in-repo copy
under `memory/` does NOT auto-update. To re-sync before pushing:

    cp ~/.claude/projects/-home-rajneesh-optum-labreqs/memory/*.md memory/
    git add memory/ && git commit -m "Sync memory snapshot"

Or just ask Claude to do it at the end of a session.
