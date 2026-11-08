# Jak přidat novou zprávu

Web se sám aktualizuje: server každých 5 minut zkontroluje GitHub, a když je
v repozitáři nový commit, sám spustí `hugo` a nahraje novou verzi. Není potřeba
se na server přihlašovat ani nic spouštět.

## Přes webové rozhraní GitHubu

1. Otevřete <https://github.com/ondrej-li/kcna> a v adresáři `content/zpravy/`
   zvolte složku `RRRR/MM` (rok a měsíc, např. `2026/11`). Když neexistuje,
   vytvoří se při vytváření souboru.
2. **Add file → Create new file**, název souboru je zároveň adresa článku:
   `muj-novy-clanek.html` → `https://kcna.ondralinek.cz/2026/11/muj-novy-clanek.html`

   Pravidla pro název: malá písmena, čísla a pomlčky, bez diakritiky a mezer.
   Čím kratší, tím lepší. Stejné jméno nesmí existovat v jiném měsíci.
3. Vložte tuto šablonu a upravte ji:

```html
---
title: "Titulek zprávy"
date: 2026-11-08T18:00:00+01:00
description: "První věta nebo perex, zobrazuje se v seznamu a ve vyhledávání."
popisky:
  - "Zpravy"
  - "Kim Jong Un"
---
<p>Text zprávy. Odstavce oddělujte takto, <b>tučné písmo</b> a <i>kurzíva</i>
fungují jako dřív.</p>

<p>Obrázek vložíte takto:</p>
<img src="/img/2026/11/muj-novy-clanek-1.jpg" alt="Popis obrázku" width="600">
```

4. Commitněte (klidně přímo do `main`). Do ~5 minut je článek na webu.

## Pravidla pro front matter

| Pole | Povinné | Význam |
|---|---|---|
| `title` | ano | Titulek, zobrazuje se v seznamu i v `<title>` |
| `date` | ano | Datum publikace; **budoucí datum = článek se objeví až po něm** (do hodiny) |
| `description` | ano | Perex do seznamu, do hledání a do náhledu na sociálních sítích |
| `popisky` | ne | Štítky; nový název automaticky vytvoří novou stránku `/popisky/...` |

Adresa článku se bere z názvu souboru a data (`/RRRR/MM/nazev-souboru.html`),
proto soubor vždy ukládejte do složky odpovídající datu.

## Obrázky

- Nahrajte je přes GitHub do `static/img/RRRR/MM/` a odkazujte cestou
  `/img/RRRR/MM/nazev.jpg`.
- Velikost držte rozumnou (do ~300 kB na obrázek); server obrázky nezmenšuje.
- Externí obrázky fungují také, ale mohou zmizet — archiv je má rád lokální.

## Náhled před publikováním

```bash
hugo server          # http://localhost:1313
```

Nebo přes archetyp (jen pro ty, kdo mají repozitář naklonovaný):

```bash
hugo new content zpravy/2026/11/muj-novy-clanek.html
```

## Když se něco pokazí

- Když nový článek neprojde buildem, web zůstane na předchozí verzi a na
  `ondrej.linek@gmail.com` přijde upozornění s výstupem buildu.
- Log nasazení: `journalctl -u kcna-autodeploy -n 100`.
- Ruční spuštění: `sudo systemctl start kcna-autodeploy.service`.
