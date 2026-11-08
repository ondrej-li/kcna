# kcna.ondralinek.cz

Static Hugo build of the KCNA blog archive. No PHP, no database, no runtime —
nginx serves plain files, the source lives in git and the build runs on the VPS.

| | |
|---|---|
| Host | kcna.ondralinek.cz |
| Web root | `/var/www/kcna` (deploy:www-data) |
| Source checkout | `~/kcna` (deploy user, clone of github.com/ondrej-li/kcna) |
| vhost | `/etc/nginx/sites-available/kcna` → `sites-enabled/kcna` |
| headers | `/etc/nginx/snippets/kcna-headers.conf` (HSTS + CSP + …) |
| TLS | `/etc/letsencrypt/live/kcna.ondralinek.cz/` |
| renewal | `certbot.timer`; deploy hook reloads nginx |
| logs | `/var/log/nginx/kcna.access.log`, `kcna.error.log` |
| build tool | Hugo **0.146.0** in `/usr/local/bin/hugo` (pinned, see below) |

Everything nginx-related is versioned in this repository under `deploy/`; the
server copies are installed by `deploy/deploy.sh`.

## Deploy an update

On the VPS, as `deploy`:

```bash
cd ~/kcna
./deploy/deploy.sh                 # git pull, build, publish, nginx config
SKIP_NGINX=1 ./deploy/deploy.sh    # content only
```

The web root is replaced with `rsync --delete`, so anything that must survive a
deploy belongs outside `/var/www/kcna`.

## Why Hugo is pinned to 0.146.0

The archive keeps the exact Blogger URLs (`/YYYY/MM/slug.html`), which relies on
`uglyURLs` plus explicit `url:` front matter. Hugo 0.169 changes the same
settings to emit `/index.html` for the home page and `/popisky/index.html` for
taxonomy lists, which would break the hard-coded navigation. The deploy script
refuses to build with a different version; upgrade both the VPS and your local
machine together and re-check the URL parity first.

```bash
# install / upgrade on the VPS
curl -sSL -o /tmp/hugo.tar.gz \
  https://github.com/gohugoio/hugo/releases/download/v0.146.0/hugo_0.146.0_linux-arm64.tar.gz
tar xzf /tmp/hugo.tar.gz -C /tmp hugo
sudo install -m 0755 /tmp/hugo /usr/local/bin/hugo
```

## DNS cutover (Blogger → this server)

`kcna.ondralinek.cz` is currently a **CNAME to `ghs.google.com`** (Blogger).
Replace it — a CNAME cannot coexist with the A/AAAA records:

| Type | Name | Value |
|---|---|---|
| A | kcna.ondralinek.cz | `2.31.33.21` |
| AAAA | kcna.ondralinek.cz | `2a01:4f8:c016:e828::1` |

DNS is managed at WebSupport (`ns1.websupport.cz`). The Blogger blog itself stays
untouched, so reverting the record is the rollback plan.

## TLS

Run once, after DNS points here:

```bash
cd ~/kcna
./deploy/enable-tls.sh
```

It checks DNS, requests the certificate with the nginx authenticator, installs
`deploy/nginx/kcna.conf` (HTTPS + 301 from HTTP) and verifies both.

```bash
sudo certbot certificates
sudo certbot renew --dry-run
```

## Verification

```bash
curl -sSI https://kcna.ondralinek.cz/ | head -5
curl -sS  https://kcna.ondralinek.cz/2016/05/divadelni-hra-krvinka-byla-vytvorena-v.html -o /dev/null -w '%{http_code}\n'
# legacy Blogger shapes
curl -sSI https://kcna.ondralinek.cz/feeds/posts/default | grep -i location   # -> /index.xml
curl -sSI https://kcna.ondralinek.cz/search/label/Zpravy | grep -i location   # -> /popisky/
curl -sSI https://kcna.ondralinek.cz/2016/05/ | grep -i location              # -> /archiv.html
```

## Notes

- Comments were imported as static data (`data/comments/`); there is no comment
  endpoint on this server. A replacement commenting system is still to be chosen.
- 209 images from the original posts lived on hosts that no longer exist
  (`kcna.kp`, `rodong.rep.kp`); those render a neutral placeholder.
- `deploy/deploy.sh` runs as `deploy`, which has passwordless sudo on this host.
