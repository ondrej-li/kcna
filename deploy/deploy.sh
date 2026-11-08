#!/usr/bin/env bash
# Build the site and publish it to /var/www/kcna.
#
#   ./deploy/deploy.sh              # git pull + build + publish + nginx config
#   SKIP_NGINX=1 ./deploy/deploy.sh # content only
#
# Runs on the VPS as the deploy user (member of sudo).
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/kcna}"
WEB_ROOT="${WEB_ROOT:-/var/www/kcna}"
HUGO_VERSION="0.146.0"

cd "$REPO_DIR"

echo "==> fetching"
git pull --ff-only

installed="$(hugo version | awk '{print $2}' | sed 's/^v//')"
if [ "$installed" != "$HUGO_VERSION" ]; then
    echo "ERROR: Hugo $installed is installed, but the build is verified against $HUGO_VERSION." >&2
    echo "       Newer Hugo releases change URL generation (home -> /index.html," >&2
    echo "       taxonomy lists -> /popisky/index.html), so the version is pinned." >&2
    exit 1
fi

echo "==> building with hugo $installed"
rm -rf public
hugo --minify --cleanDestinationDir

echo "==> publishing to $WEB_ROOT"
sudo install -d -o deploy -g www-data -m 0755 "$WEB_ROOT"
rsync -a --delete public/ "$WEB_ROOT/"

if [ "${SKIP_NGINX:-0}" = "1" ]; then
    echo "==> nginx skipped (SKIP_NGINX=1)"
    exit 0
fi

echo "==> nginx configuration"
sudo install -m 0644 -o root -g root deploy/nginx/kcna-headers.conf /etc/nginx/snippets/kcna-headers.conf

if sudo test -f /etc/letsencrypt/live/kcna.ondralinek.cz/fullchain.pem; then
    sudo install -m 0644 -o root -g root deploy/nginx/kcna.conf /etc/nginx/sites-available/kcna
else
    sudo install -m 0644 -o root -g root deploy/nginx/kcna-http.conf /etc/nginx/sites-available/kcna
fi

sudo ln -sfn /etc/nginx/sites-available/kcna /etc/nginx/sites-enabled/kcna
sudo nginx -t
sudo systemctl reload nginx

echo "==> done: $(find "$WEB_ROOT" -name '*.html' | wc -l) pages published"
