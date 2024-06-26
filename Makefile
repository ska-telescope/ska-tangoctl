# supporting scripts for changelog generation using git-chglog and GitLab release pages
#include .make/release.mk

PYTHON_LINE_LENGTH = 99
OCI_BUILD_ADDITIONAL_ARGS=--build-arg OCI_IMAGE_VERSION=$(SKA_K8S_TOOLS_BUILD_DEPLOY)
PYTHON_RUNNER := poetry run
DOCS_SPHINXBUILD := poetry run python -m sphinx
DOCS_SPHINXOPTS=-n -W --keep-going

# include OCI Images support
include .make/oci.mk

# include k8s support
include .make/k8s.mk

# include Helm Chart support
include .make/helm.mk

# Include Python support
include .make/python.mk

# include docs support
include .make/docs.mk

# include raw support
include .make/raw.mk

# include core make support
include .make/base.mk

# include your own private variables for custom deployment configuration
-include PrivateRules.mak
