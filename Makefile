ORG := vivareal
REL := build
VERSION ?= latest
PROJ ?= $(shell basename ${PWD})

SHELL := /bin/bash

default: kubeval

kubeval-install:
	wget https://github.com/garethr/kubeval/releases/download/${KUBEVAL_VERSION}/kubeval-linux-amd64.tar.gz -O /tmp/kubeval.tar.gz &&	tar xf /tmp/kubeval.tar.gz || true

kubeval: kubeval-install
	find deploy -name "*.yaml" -not -name '*customresourcedefinition*' | xargs ./kubeval --kubernetes-version ${KUBE_VERSION}

login:
	docker login -u ${DOCKER_USER} -p ${DOCKER_PASS}

build: 
	docker build -t ${ORG}/${PROJ}:${REL} -f Dockerfile .

save-cache: build
	mkdir -p docker-cache
	docker save -o docker-cache/${PROJ}-${REL}.tar ${ORG}/${PROJ}:${REL}

load-cache:
	[[ -d docker-cache ]] && docker load < docker-cache/${PROJ}-${REL}.tar || true

publish: load-cache login
	docker tag ${ORG}/${PROJ}:${REL} ${ORG}/${PROJ}:${VERSION}
	docker push ${ORG}/${PROJ}:${VERSION}

.PHONY: default kubeval-install kubeval login build save-cache load-cache publish
