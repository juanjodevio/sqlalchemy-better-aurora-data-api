SHELL=/bin/bash -eo pipefail

release-major:
	$(eval export TAG=$(shell git describe --tags --match 'v*.*.*' | perl -ne '/^v(\d+)\.(\d+)\.(\d+)/; print "v@{[$$1+1]}.0.0"'))
	$(MAKE) release

release-minor:
	$(eval export TAG=$(shell git describe --tags --match 'v*.*.*' | perl -ne '/^v(\d+)\.(\d+)\.(\d+)/; print "v$$1.@{[$$2+1]}.0"'))
	$(MAKE) release

release-patch:
	$(eval export TAG=$(shell git describe --tags --match 'v*.*.*' | perl -ne '/^v(\d+)\.(\d+)\.(\d+)/; print "v$$1.$$2.@{[$$3+1]}"'))
	$(MAKE) release

release:
	@if ! git diff --cached --exit-code; then echo "Commit staged files before proceeding"; exit 1; fi
	@if [[ -z $$TAG ]]; then echo "Use release-{major,minor,patch}"; exit 1; fi
	@if ! type -P uv; then echo "Please install uv"; exit 1; fi
	@if ! type -P sponge; then echo "Please install moreutils"; exit 1; fi
	@if ! type -P gh; then echo "Please install gh"; exit 1; fi
	@if ! type -P twine; then echo "Please install twine"; exit 1; fi
	git pull
	git clean -x --force sqlalchemy_better_aurora_data_api
	sed -i -e "s/^version = \"[0-9][^\"]*\"/version = \"$${TAG:1}\"/" pyproject.toml
	uv lock
	git add pyproject.toml uv.lock
	TAG_MSG=$$(mktemp); \
	    echo "# Changes for ${TAG} ($$(date +%Y-%m-%d))" > $$TAG_MSG; \
	    git log --pretty=format:%s $$(git describe --abbrev=0)..HEAD >> $$TAG_MSG; \
	    $${EDITOR:-emacs} $$TAG_MSG; \
	    if [[ -f CHANGES.md ]]; then cat $$TAG_MSG <(echo) CHANGES.md | sponge CHANGES.md; git add CHANGES.md; fi; \
	    git commit -m ${TAG}; \
	    git tag --annotate --file $$TAG_MSG ${TAG}
	git push --follow-tags
	$(MAKE) install
	gh release create ${TAG} dist/*.whl --notes="$$(git tag --list ${TAG} -n99 | perl -pe 's/^\S+\s*// if $$. == 1' | sed 's/^\s\s\s\s//')"
	$(MAKE) release-pypi
	$(MAKE) release-docs

release-pypi:
	uv build
	twine upload dist/*.tar.gz dist/*.whl --verbose

release-docs:
	$(MAKE) docs
	-git branch -D gh-pages
	git checkout -B gh-pages-stage
	touch docs/html/.nojekyll
	git add --force docs/html
	git commit -m "Docs for ${TAG}"
	git push --force origin $$(git subtree split --prefix docs/html --branch gh-pages):refs/heads/gh-pages
	git checkout -

.PHONY: release
