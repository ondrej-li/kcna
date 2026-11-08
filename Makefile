.PHONY: serve build clean import deploy

serve: ## lokální náhled na http://localhost:1313
	hugo server

build: ## produkční build do public/
	hugo --minify --cleanDestinationDir

clean: ## smazat build a cache
	rm -rf public resources .hugo_build.lock

import: ## znovu stáhnout chybějící obsah z Bloggeru
	python3 tools/import_blogger.py

deploy: build ## nahrát public/ na VPS
	rsync -avz --delete public/ deploy@ondralinek.cz:/var/www/kcna/
