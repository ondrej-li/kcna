# Novinky z KLDR — statický Hugo web

Statická verze blogu [kcna.ondralinek.cz](https://kcna.ondralinek.cz/) — 1040 zpráv původně
publikovaných na Bloggeru, převedených do [Hugo](https://gohugo.io/). Všechny adresy zpráv
zůstávají stejné (`/RRRR/MM/slug.html`), obrázky jsou stažené lokálně, takže web nezávisí
na žádné externí službě.

## Požadavky

- Hugo ≥ 0.146 (extended není potřeba)

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
content/zpravy/_index.md           nastavení archivu (/archiv.html)
content/hledat.md                  stránka hledání (/hledat.html)
data/comments/                     původní komentáře z Bloggeru (read-only)
data/links.yaml                    odkazy v sidebaru „Kam dále“
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

## Nasazení na VPS (nginx)

```bash
hugo --minify
rsync -avz --delete public/ deploy@ondralinek.cz:/var/www/kcna/
```

Ukázková konfigurace `/etc/nginx/sites-available/kcna.ondralinek.cz`:

```nginx
server {
    listen 443 ssl http2;
    server_name kcna.ondralinek.cz;

    root /var/www/kcna;
    index index.html;

    charset utf-8;

    location / {
        try_files $uri $uri/ $uri.html =404;
    }

    # staré Blogger endpointy pro čtečky RSS
    location /feeds/posts/default {
        return 301 /index.xml;
    }

    # staré štítky Bloggeru → nové popisky
    location /search/label/ {
        return 301 /popisky/;
    }

    error_page 404 /404.html;
    location = /404.html {
        internal;
    }
}
```

## Poznámky

- Komentáře jsou v repozitáři jen jako data ([data/comments](data/comments)); nový
  komentovací systém se doplní později.
- Zdrojový blog na Bloggeru zůstává nedotčený — tento repozitář je nezávislá kopie.
