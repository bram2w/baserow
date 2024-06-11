ifeq ($(shell uname -s),Darwin)
    REALPATH:=grealpath -em
else
    REALPATH:=realpath -em
endif

SHELL=/bin/bash
WORKDIR:=$(shell $(REALPATH) $(shell pwd))

SUBDIRS:=backend web-frontend
DOCKERCLI:=docker
DOCKERC:=$(DOCKERCLI) compose

DOCKER_SPLIT_CONF:=-f docker-compose.yml -f docker-compose.dev.yml

.PHONY: install build .callsubcmd $(SUBDIRS) help package-build test tests\
		lint lint-fix docker-lint\
		docker-status docker-build docker-start docker-clean docker-stop docker-kill \
		deps deps-upgrade \
		clean clean-all

help:
	@echo "baserow make. available targets:"
	@echo "targets that are executed in backend/frontend dirs:"
	@echo " make install - install locally with dependencies"
	@echo " make package-build - build packages locally"
	@echo " make lint - check code style"
	@echo " make test - run test suite"
	@echo " make clean-all - remove docker images, venv and frontend node_modules dir"
	@echo " "
	@echo "targets that are executed at top-dir level:"
	@echo ""
	@echo " make docker-build - build docker images for dev env"
	@echo " make docker-start - start local dev env"
	@echo " make docker-stop - stop local dev env"
	@echo " make docker-status - show current docker containers"
	@echo " make docker-clean - remove docker images"


# create .env file with default values if no file exists
.env:
	@cat .env.example > .env
	@echo "### DEV VARS" >> .env
	@cat .env.dev.example >> .env
	@sed -i'' -e 's/replace me with your uid/$(shell id -u)/g' .env
	@sed -i'' -e 's/replace me with your gid/$(shell id -g)/g' .env
	@echo "Created .env file with default values"
	@echo "Please review contents of .env"
	@echo ""


# execute $(SUBCMD) in subdirs with make
# NOTE: SUBCMD is substituted at rule level while $SDIR is shell variable
.subcmd:
	@echo "calling $(SUBCMD) in subdirs"
	for SDIR in $(SUBDIRS); do echo "$$SDIR/$(SUBCMD)"; \
		cd $(WORKDIR) && cd $$SDIR && $(MAKE) $(SUBCMD) && cd ..; \
	done

# NOTE: each target that need to call subdir mae

install: SUBCMD=install deps-install deps-install-dev
install: .subcmd

package-build: SUBCMD=package-build
package-build: .subcmd

lint: SUBCMD=lint
lint: .subcmd docker-lint

lint-fix: SUBCMD=lint-fix
lint-fix: .subcmd

test: SUBCMD=test
test: .subcmd

tests: test

.docker-build: .env
	$(DOCKERC) $(DOCKER_CONFIG_FILES) build

.docker-start: .env
	$(DOCKERC) $(DOCKER_CONFIG_FILES) up -d

.docker-stop: .env
	$(DOCKERC) $(DOCKER_CONFIG_FILES) stop

.docker-kill: .env
	$(DOCKERC) $(DOCKER_CONFIG_FILES) kill

.docker-clean: .env
	$(DOCKERC) $(DOCKER_CONFIG_FILES) rm -f -v

docker-build: DOCKER_CONFIG_FILES=$(DOCKER_SPLIT_CONF)
docker-build: .docker-build

docker-start: DOCKER_CONFIG_FILES=$(DOCKER_SPLIT_CONF)
docker-start: docker-build .docker-start

docker-stop: DOCKER_CONFIG_FILES=$(DOCKER_SPLIT_CONF)
docker-stop: .docker-stop

docker-kill: DOCKER_CONFIG_FILES=$(DOCKER_SPLIT_CONF)
docker-kill: .docker-kill

docker-clean: DOCKER_CONFIG_FILES=$(DOCKER_SPLIT_CONF)
docker-clean: docker-stop .docker-clean

docker-lint:
	$(DOCKERCLI) run --rm -i -v "$(shell pwd)":/opt/hadolint/. -w /opt/hadolint \
        hadolint/hadolint:2.9.3-debian \
        hadolint -f tty \
        --ignore DL3008 \
        backend/Dockerfile \
        web-frontend/Dockerfile \
        heroku.Dockerfile \
        e2e-tests/Dockerfile \
        deploy/*/Dockerfile

clean: SUBCMD=clean
clean: .subcmd docker-clean

clean-all: SUBCMD=clean-all
clean-all: .subcmd docker-clean

deps: SUBCMD=deps
deps: .subcmd

deps-upgrade: SUBCMD=deps-upgrade
deps-upgrade: .subcmd

docker-status: .env
	$(DOCKERC) $(DOCKER_SPLIT_CONF) ps
