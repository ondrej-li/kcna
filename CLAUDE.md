# CLAUDE.md — kcna

Static Hugo archive of a KCNA (North Korean news agency) blog, published at
**kcna.ondralinek.cz**. The [README](README.md) is Czech and is the author's
guide; [`docs/AUTHORING.md`](docs/AUTHORING.md) is the article template;
[`deploy/DEPLOY.md`](deploy/DEPLOY.md) is the deployment map.

## Layout

| Path | What |
|---|---|
| `content/zpravy/RRRR/MM/slug.html` | the posts — HTML files with Hugo front matter, ~1040 of them |
| `content/zpravy/_index.md`, `content/hledat.md` | the archive page and the search page |
| `layouts/` | templates, incl. the archive and search views |
| `assets/`, `static/` | CSS, JS and the locally downloaded images — the site depends on no external service |
| `data/comments/`, `data/links.yaml` | the original Blogger comments (read-only) and the sidebar links |
| `tools/import_blogger.py` | re-imports content from Blogger; needs the cache in `.cache/` |
| `hugo.toml` | config: `uglyURLs`, `removePathAccents`, permalinks `/:year/:month/:contentbasename` |
| `deploy/` | nginx vhost + headers, `deploy.sh`, `autodeploy.sh` (the VPS timer) |

## Build

Hugo **0.146.0** exactly — newer versions change URL generation, which is why it
is pinned in CI and on the box (see `deploy/DEPLOY.md`). Extended is not needed.

```sh
hugo --minify --cleanDestinationDir    # → public/
hugo server                            # preview on :1313
```

CI (`.github/workflows/ci.yml`, `ubuntu-latest`) builds with the pinned Hugo and
compiles `tools/` with `python3 -m compileall`.

## Workflow

This is a hobby site: **commit directly to `main`**. No feature branch and no
pull request are needed for content or routine site changes; every push to
`main` is published by the autodeploy timer within ~5 minutes.

## Adding a post

A new file in `content/zpravy/RRRR/MM/slug.html`, front matter copied from a
neighbouring post (`title`, `slug`, `url`, `date`, optional `lastmod`,
`description`), then push to `main`. That is the whole workflow — see
[`docs/AUTHORING.md`](docs/AUTHORING.md).

## Translating a KCNA dispatch

A pasted KCNA text is translated into Czech, not copied. The detailed workflow
lives in the [`kcna-article`](.claude/skills/kcna-article/SKILL.md) skill; the
house rules are:

- Translate the whole dispatch faithfully, in the agency's formal register;
  add or omit nothing. Keep the archive's spellings (Pjongjang, Kim Čong Un,
  KSP, KLDR, Ústřední lidové shromáždění, …).
- **Bold every mention of Kim Čong Un** in the body (`<b>Kim Čong Un</b>`) —
  KCNA's own typographic tradition.
- Finish the body with `<hr />` and `<p>Džuče je věčné!</p>`.
- Use the archive front matter (`title`, `slug`, `url`, `date`, `description`,
  `popisky`) and file under `content/zpravy/RRRR/MM/`; the URL is
  `/RRRR/MM/<slug>.html`.
- Download images into `static/img/RRRR/MM/` and credit KCNA; never hot-link.
- Check the front matter, HTML and `git diff --check`, commit directly to
  `main`, push, and confirm the CI build. The autodeploy timer publishes it.

## Deploy

`kcna-autodeploy.timer` on `deploy@ondralinek.cz` polls `main` every five minutes,
runs Hugo and rsyncs into `/var/www/kcna`. There is no manual step and no staging;
`make deploy` exists but only repeats what the timer does.

## Conventions

- Czech for content; English for code, config and commits.
- URLs are load-bearing: `uglyURLs`, the permalink pattern and the `url:` field
  in each post keep fifteen years of links alive. Do not "tidy" them.
- Images belong next to the post or in `static/`, downloaded — never hot-linked.
- `data/comments/` is an archive of Blogger comments. Read it, do not edit it.
- The import tool is best-effort and cached; if it fails, say so instead of
  hand-editing a thousand files.

## Before this site goes live

This repository is served publicly at https://kcna.ondralinek.cz. A change that adds or alters a
page, a form, a script, a header or a vhost passes the launch gate before it
ships:

```sh
web-launch-check https://kcna.ondralinek.cz
```

- `FAIL` blocks the publish; `WARN` is a decision to state in the reply, not
  something to leave unmentioned.
- The `web-launch-checklist` skill has the 25 items the checker cannot judge:
  privacy and terms content, colour contrast, real-device speed, spam
  protection, analytics and error monitoring, one clear call to action, and the
  signup/login/reset flows.
- Run it again after publishing: it checks the live vhost, headers and
  certificate, not the working tree.
- A preview vhost passes the same gate before DNS moves.

## Deploying this site

https://kcna.ondralinek.cz is published by the **deploy** account from this repository's
`main` branch — the `site-deploy` timer, every five minutes. Merge is
deploy: there is no publish command, and `sudo vps-site publish` refuses this
web root (one writer per root, and it is not this account).

Verify after merging, and give it up to ten minutes:

```sh
site-status --site kcna
curl -fsS https://kcna.ondralinek.cz/deployed.json           # {"commit": "...", "deployed_at": "..."}
git -C ~/repos/kcna rev-parse origin/main
```

The three commits must match. If it has not moved after two timer cycles, read
`journalctl -u site-deploy -n 50`, report the commit that should be live and the
one that is, and do not rsync into `/var/www` or edit a live file to compensate.
The `static-site-deploy` skill has the full procedure.
