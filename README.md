# Novinky z KLDR — statický Hugo web

Statická verze blogu [kcna.ondralinek.cz](https://kcna.ondralinek.cz/) — 1040 zpráv původně
publikovaných na Bloggeru, převedených do [Hugo](https://gohugo.io/). Všechny adresy zpráv
zůstávají stejné (`/RRRR/MM/slug.html`), obrázky jsou stažené lokálně, takže web nezávisí
na žádné externí službě.

## Požadavky

- **Hugo 0.146.0** (přesně tato verze — novější mění generování URL, viz
  [deploy/DEPLOY.md](deploy/DEPLOY.md#why-hugo-is-pinned-to-01460); extended není potřeba)

## Přidání nového článku

Nový článek = nový soubor v `content/zpravy/RRRR/MM/nazev.html` commitnutý do
`main`. Server se na GitHub dívá každých 5 minut, sám spustí `hugo` a web
aktualizuje — není potřeba se nikam přihlašovat.

Podrobný návod včetně šablony: [docs/AUTHORING.md](docs/AUTHORING.md).

## Vývoj

```bash
hugo server
# → http://localhost:1313
```

## Build

```bash
hugo --minify
# výstup v public/
```

## Struktura

```
content/zpravy/RRRR/MM/slug.html   jednotlivé zprávy (HTML tělo beze změny)
archetypes/zpravy.html             šablona pro `hugo new content`
content/zpravy/_index.md           nastavení archivu (/archiv.html)
docs/AUTHORING.md                  jak přidat článek přes GitHub
content/hledat.md                  stránka hledání (/hledat.html)
data/comments/                     původní komentáře z Bloggeru (read-only)
data/links.yaml                    odkazy v sidebaru „Kam dále“
deploy/                            nginx, systemd units a deploy skripty pro VPS
static/img/                        lokálně zrcadlené obrázky z Bloggeru
static/js/search.js                klientské hledání nad /index.json
assets/css/main.css                vzhled (moderní, s palubními barvami KLDR)
layouts/                           šablony
tools/import_blogger.py            opakovatelný import z Bloggeru
```

## Import / aktualizace obsahu z Bloggeru

Skript stahuje Atom feedy (zprávy + komentáře) a všechny obrázky, přepisuje odkazy na
lokální cesty a zapisuje front matter. Opakované spuštění je bezpečné (používá cache).

```bash
python3 tools/import_blogger.py            # pouze doplní, co chybí
python3 tools/import_blogger.py --refresh  # stáhne feedy i obrázky znovu
```

Nedostupné obrázky (mrtvé servery `kcna.kp` apod.) zůstanou odkázané původní URL a jejich
seznam se zapíše do `.cache/blogger/dead-images.txt`.

## Nasazení na VPS

Web běží na VPS (`deploy@ondralinek.cz`), nginx servíruje `/var/www/kcna`.
Konfigurace nginxu i skripty jsou v repozitáři:

```bash
cd ~/kcna
./deploy/deploy.sh          # git pull + hugo build + rsync do /var/www/kcna
./deploy/enable-tls.sh      # jednorázově po přepnutí DNS (certbot + HTTPS)
```

Nasazení běží samo: `kcna-autodeploy.timer` každých 5 minut zkontroluje
`origin/main`, a když je nový commit, spustí `deploy.sh`. Když build selže,
web zůstane na předchozí verzi a přijde upozornění e-mailem.

Podrobnosti (DNS cutover, TLS, rollback, pinned Hugo): [deploy/DEPLOY.md](deploy/DEPLOY.md).

## Poznámky

- Komentáře jsou v repozitáři jen jako data ([data/comments](data/comments)); nový
  komentovací systém se doplní později.
- 209 obrázků z původních příspěvků bylo na serverech, které už neexistují
  (`kcna.kp`, `rodong.rep.kp`); místo nich se zobrazuje neutrální zástupný obrázek.
- Zdrojový blog na Bloggeru zůstává nedotčený — tento repozitář je nezávislá kopie.
