#!/usr/bin/env bash
# One-off cutover step: request the Let's Encrypt certificate and switch the
# vhost to HTTPS. Run it only after kcna.ondralinek.cz resolves to this server.
#
#   ./deploy/enable-tls.sh
#
# Renewals afterwards are handled by certbot.timer; the global deploy hook
# (/etc/letsencrypt/renewal-hooks/deploy/10-mail.sh) reloads nginx.
set -euo pipefail

DOMAIN="kcna.ondralinek.cz"
REPO_DIR="${REPO_DIR:-$HOME/kcna}"
WEB_ROOT="${WEB_ROOT:-/var/www/kcna}"
PUBLIC_IP="2.31.33.21"

cd "$REPO_DIR"

echo "==> checking DNS"
resolved="$(getent ahostsv4 "$DOMAIN" | awk 'NR==1{print $1}')"
if [ "$resolved" != "$PUBLIC_IP" ]; then
    cat >&2 <<EOF
ERROR: $DOMAIN resolves to ${resolved:-nothing}, expected $PUBLIC_IP.
       Remove the Blogger CNAME (ghs.google.com) and point the name at this
       server first:  A $PUBLIC_IP  /  AAAA 2a01:4f8:c016:e828::1
EOF
    exit 1
fi

echo "==> requesting certificate for $DOMAIN"
# Webroot mode: certbot drops the challenge into the site root, which the vhost
# already serves under /.well-known/acme-challenge/. No config rewriting, so the
# versioned vhost in this repo stays the single source of truth.
sudo certbot certonly --webroot -w "$WEB_ROOT" -d "$DOMAIN" --cert-name "$DOMAIN" \
    --non-interactive --agree-tos --deploy-hook "systemctl reload nginx"

echo "==> switching vhost to HTTPS"
sudo install -d -o deploy -g www-data -m 0755 "$WEB_ROOT"
sudo install -m 0644 -o root -g root deploy/nginx/kcna.conf /etc/nginx/sites-available/kcna
sudo ln -sfn /etc/nginx/sites-available/kcna /etc/nginx/sites-enabled/kcna
sudo nginx -t
sudo systemctl reload nginx

echo "==> verifying"
code="$(curl -sS -o /dev/null -w '%{http_code}' --resolve "$DOMAIN:443:127.0.0.1" "https://$DOMAIN/")"
echo "    https://$DOMAIN/ -> $code"
redirect="$(curl -sS -o /dev/null -w '%{http_code} %{redirect_url}' --resolve "$DOMAIN:80:127.0.0.1" "http://$DOMAIN/archiv.html")"
echo "    http://$DOMAIN/archiv.html -> $redirect"
