#!/usr/bin/env bash
# Pull new articles from GitHub, rebuild and publish.
#
# Driven by kcna-autodeploy.timer (every 5 minutes). It is a no-op when nothing
# changed, except for a periodic rebuild (MAX_AGE_SECONDS, default 1 h) so that
# future-dated posts go live once their date arrives.
#
# Exit codes: 0 = nothing to do or published, 1 = deploy failed (live site kept).
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/kcna}"
BRANCH="${BRANCH:-main}"
MAIL_TO="${MAIL_TO:-}"
STATE_DIR="${STATE_DIR:-$HOME/.local/state/kcna-autodeploy}"
MAX_AGE_SECONDS="${MAX_AGE_SECONDS:-3600}"

cd "$REPO_DIR"
mkdir -p "$STATE_DIR"

# One deploy at a time: the timer and a manual deploy.sh must not interleave.
exec 9>"$STATE_DIR/lock"
if ! flock -n 9; then
    echo "[autodeploy] another run holds the lock, skipping"
    exit 0
fi

log() { printf '[autodeploy] %s %s\n' "$(date -Is)" "$*"; }

log_file="$(mktemp)"
trap 'rm -f "$log_file"' EXIT

publish() {
    if ./deploy/deploy.sh >"$log_file" 2>&1; then
        cat "$log_file"
        date +%s >"$STATE_DIR/last-build"
        rm -f "$STATE_DIR/last-failure"
        return 0
    fi
    echo "----- deploy.sh output -----"
    tail -60 "$log_file"
    return 1
}

notify_failure() {
    local sha="$1" stamp="$STATE_DIR/last-failure" now prev_sha prev_ts
    [ -n "$MAIL_TO" ] || return 0
    now="$(date +%s)"
    if [ -f "$stamp" ]; then
        read -r prev_sha prev_ts <"$stamp" || true
        if [ "${prev_sha:-}" = "$sha" ] && [ $((now - ${prev_ts:-0})) -lt 3600 ]; then
            log "failure for ${sha:0:8} already reported in the last hour"
            return 0
        fi
    fi
    printf '%s %s\n' "$sha" "$now" >"$stamp"
    {
        printf 'To: %s\n' "$MAIL_TO"
        printf 'Subject: [kcna] deploy failed for %s\n' "${sha:0:8}"
        printf 'X-KCNA: autodeploy\n\n'
        printf 'The live site was NOT updated; the previous build is still online.\n\n'
        printf 'commit: %s\nrepo:   %s\n\n' "$sha" "$REPO_DIR"
        printf -- '----- last 60 lines of deploy output -----\n'
        tail -60 "$log_file"
    } | /usr/sbin/sendmail -i -t || log "could not send the failure mail"
}

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    log "server checkout has local changes; refusing to auto-deploy"
    exit 1
fi

if ! git fetch --quiet origin "$BRANCH"; then
    log "git fetch failed (network?); keeping the current build"
    exit 0
fi

local_sha="$(git rev-parse HEAD)"
remote_sha="$(git rev-parse "origin/$BRANCH")"

if [ "$local_sha" != "$remote_sha" ]; then
    log "new commit ${remote_sha:0:8} (local ${local_sha:0:8})"
    if ! publish; then
        log "deploy of ${remote_sha:0:8} failed"
        notify_failure "$remote_sha"
        exit 1
    fi
    log "published ${remote_sha:0:8}"
    exit 0
fi

now="$(date +%s)"
last=0
[ -f "$STATE_DIR/last-build" ] && last="$(cat "$STATE_DIR/last-build")"
if [ $((now - last)) -ge "$MAX_AGE_SECONDS" ]; then
    log "no new commits; periodic rebuild (last build $(( (now - last) / 60 )) min ago)"
    if ! publish; then
        log "periodic rebuild failed"
        notify_failure "$local_sha"
        exit 1
    fi
    exit 0
fi

log "up to date at ${local_sha:0:8}"
