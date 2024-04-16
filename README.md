# Readme

![pytango](/docs/src/img/logo.webp "Built with pytango")

[![Documentation Status](https://readthedocs.org/projects/ska-tangoctl/badge/?version=latest)](https://developer.skatelescope.org/projects/ska-tangoctl/en/latest/?badge=latest)

## Getting started

Clone this repo:

```
$ git clone https://gitlab.com/ska-telescope/ska-tangoctl.git
$ cd ska-tangoctl
$ git submodule update --init --recursive
```

Build and view doumentation:

```
$ make docs-build html
$ firefox docs/build/html/index.html
```

## Description

This repo provides a suite of utilities for use with Tango:

* *tangoctl*, a utility to query and test Tanfo devices
* *tangoktl*, a utility to query and test Tanfo devices running in a Kubernetes cluster

![tangoktl running](/docs/src/img/list_devices.png "List devices")

## Installation

### Requirements

Install the following:

* pytango 9.4.2 or higher

https://pytango.readthedocs.io/en/latest/installation.html

### Docker container

Build a new Docker image for the project:

```
$ make oci-build
[...]
[+] Building 111.7s (14/14) FINISHED 
[...]
```

### Local install

To run *tangoctl* or *tangoktl* on your own computer:

```
$ sudo setup.py install
```

## Usage

Here are some examples of using this package:

```
$ tangoktl --namespace=integration --show-dev
$ tangoktl --namespace=integration -D talon -l
$ tangoktl --namespace=integration -A timeout
$ tangoktl --namespace=integration -C Telescope
$ tangoktl --namespace=integration -P Power
$ tangoktl --namespace=integration -D mid_csp_cbf/talon_lru/001 -f
$ tangoktl --namespace=integration -D mid_csp_cbf/talon_lru/001 -s
$ tangoktl --namespace=integration -D mid_csp_cbf/talon_lru/001 -q
$ tangoktl --namespace=integration -D mid_csp_cbf/talon_board/001 -f
$ tangoktl --namespace=integration -D mid_csp_cbf/talon_board/001 -f --dry-run
$ ADMIN_MODE=1 tangoctl --k8s-ns=integration -D mid_csp_cbf/talon_board/001 -f --in resources/dev_online.json -V
```

## Support

Go to this Slack group for help:

https://skao.slack.com/archives/C023L1N3H60

## Roadmap

This is the first release. Releases in the future will be made available for new features or bug fixes.

## Contributing

This project is open to contributions, see:

https://developer.skatelescope.org/en/latest/getting-started/contrib-guidelines.html

Use these commands to lint the code or run tests:

```
$ make python-lint
$ make python-test
```

## Authors and acknowledgment

Team Atlas, SARAO

## License

Copyright 2020 SKA Observatory

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

## Project status

This project is under active development.

***

## Integrate with other tools

- [ ] [Set up project integrations](https://gitlab.com/ska-telescope/ska-tangoctl/-/settings/integrations)

## Collaborate with teams

- [ ] [Invite team members and collaborators](https://docs.gitlab.com/ee/user/project/members/)
- [ ] [Create a new merge request](https://docs.gitlab.com/ee/user/project/merge_requests/creating_merge_requests.html)
- [ ] [Automatically close issues from merge requests](https://docs.gitlab.com/ee/user/project/issues/managing_issues.html#closing-issues-automatically)
- [ ] [Enable merge request approvals](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/)
- [ ] [Set auto-merge](https://docs.gitlab.com/ee/user/project/merge_requests/merge_when_pipeline_succeeds.html)

## Test and Deploy

Use the built-in continuous integration in GitLab.

- [ ] [Get started with GitLab CI/CD](https://docs.gitlab.com/ee/ci/quick_start/index.html)
- [ ] [Analyze your code for known vulnerabilities with Static Application Security Testing (SAST)](https://docs.gitlab.com/ee/user/application_security/sast/)
- [ ] [Deploy to Kubernetes, Amazon EC2, or Amazon ECS using Auto Deploy](https://docs.gitlab.com/ee/topics/autodevops/requirements.html)
- [ ] [Use pull-based deployments for improved Kubernetes management](https://docs.gitlab.com/ee/user/clusters/agent/)
- [ ] [Set up protected environments](https://docs.gitlab.com/ee/ci/environments/protected_environments.html)

![SKA](/docs/src/img/ska_logo.jpg "Square Kilometer Array")
