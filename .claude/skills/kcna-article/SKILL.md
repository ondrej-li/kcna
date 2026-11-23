---
name: kcna-article
description: Translate a KCNA dispatch into Czech and add it to the kcna Hugo archive, including front matter, local images, the bold Kim Jong Un convention and the closing slogan. Use when asked to add, translate or publish a KCNA article, attach a KCNA photo to an article, or change an existing article's text.
---

# Adding a KCNA article

`kcna` is a Czech-language Hugo archive of KCNA dispatches. When asked to add a
dispatch, translate it and publish it directly on `main`; this hobby site does
not use feature branches or pull requests.

## Source and placement

- Check `content/zpravy/` for an existing translation before writing.
- If the request links `kcna.kp`, read the original there; use its dateline for
  `date` when it has one, otherwise today.
- The post is `content/zpravy/RRRR/MM/<slug>.html`; the URL is
  `/RRRR/MM/<slug>.html` (`uglyURLs` plus the permalink pattern).
- Slug: lowercase ASCII, hyphen-separated, short, and unique across months.

## Translation

- Translate the whole text into Czech. Keep KCNA's formal register; add or
  omit nothing. The only house addition is the closing slogan.
- Keep the archive's spellings and terms:

| English | Czech |
|---|---|
| DPRK | KLDR |
| Pyongyang | Pjongjang |
| Kim Jong Un / Kim Jong Il / Kim Il Sung | Kim Čong Un / Kim Čong Il / Kim Il Sung |
| Workers' Party of Korea (WPK) | Korejská strana pracujících (KSP) |
| Central Committee | Ústřední výbor |
| Supreme People's Assembly | Nejvyšší lidové shromáždění |
| President of the State Affairs | prezident Státních záležitostí |
| Foreign Minister | ministr / ministryně zahraničí |
| credentials | pověřovací listiny |
| respected comrade | vážený soudruh |
| general secretary | generální tajemník |
| Central Zoo | Ústřední zoo |

- **Bold every mention of Kim Čong Un** in the body:
  `<b>Kim Čong Un</b>`. KCNA does this in its own copy; it is a house rule.
- One paragraph per `<p>…</p>`.
- End the article with:

```html
<hr />
<p>Džuče je věčné!</p>
```

## Front matter

```html
---
title: "Czech title in sentence case"
slug: "<slug>"
url: "/2026/11/<slug>.html"
date: 2026-11-23T13:00:00+01:00
description: "Czech perex, one or two sentences."
popisky:
  - "Kim Jong Un"
  - "Zpravy"
---
```

The `date` controls publication: a future time keeps the post out of the build,
so use a past time. Reuse taxonomy names already in the archive (`Kim Jong Un`,
`Zpravy`, …) rather than inventing variants.

## Images

- Download every image; never hot-link.
- Save under `static/img/RRRR/MM/<name>.jpg`; keep each under ~300 kB.
- `kcna.kp/photo/...` requires a `Referer` header (the gallery page); without
  it the server returns an empty file. For example:
  `curl -e '<gallery-url>' 'http://www.kcna.kp/photo/<hash>' -o image.jpg`.
- Galleries often contain several uncaptioned portraits. The order usually
  follows the country list in the dispatch, but verify the person against
  another official photo before attaching the image.
- Markup:
  `<img src="/img/RRRR/MM/<name>.jpg" alt="…" width="…" loading="lazy" decoding="async">`
  followed by a short caption: `<p><i>… Foto: KCNA</i></p>`.
- If the caption names Kim Čong Un, bold that mention too.

## Verify and publish

- Check that the front matter parses, the HTML tags balance, and
  `git diff --check` is clean.
- Do not run Hugo on this box; CI builds with Hugo 0.146.0.
- Commit directly to `main` and push.
- Check the `CI` run on `main`, wait for `kcna-autodeploy.timer` (up to ~5
  minutes), and confirm both the live article URL and the image URL return
  HTTP 200.
- Do not open a pull request, tag a release, or edit `data/comments/`.

## Reference

- [`docs/AUTHORING.md`](../../../docs/AUTHORING.md) — the author's template and
  field rules.
- [`deploy/DEPLOY.md`](../../../deploy/DEPLOY.md) — deployment map.
- [`CLAUDE.md`](../../../CLAUDE.md) — repository conventions.
