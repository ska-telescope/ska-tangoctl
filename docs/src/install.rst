Installing *tangoctl*
*********************

.. image:: https://readthedocs.org/projects/ska-tangoctl/badge/?version=latest
    :target: https://developer.skatelescope.org/projects/ska-tangoctl/en/latest/?badge=latest

Getting the code
================

Clone the repository::

    $ git clone https://gitlab.com/ska-telescope/ska-tangoctl.git
    $ cd ska-tangoctl
    $ git submodule update --init --recursive

Build and view doumentation::

    $ make docs-build html
    $ firefox docs/build/html/index.html


Installation of **tangoctl**
============================

Requirements for installation
-----------------------------

Install PyTango:

* pytango 9.4.2 or higher

Get it `here <https://pytango.readthedocs.io/en/latest/installation.html>`_.

Run in poetry environment
-------------------------

Activate poetry::

    $ poetry install
    $ poetry lock
    $ poetry shell
    $ source .venv/bin/activate

Inside the poetry shell, any of the following should work::

    # tangoctl.py -h
    # ./src/ska_mid_itf_engineering_tools/tango_control/tangoctl.py -h


To use **tangoktl.py** in Poetry, you will need to log in on infra::

    # infra login https://boundary.skao.int --enable-ssh
    # infra use za-itf-k8s-master01-k8s
    # tangoctl.py -k

Run in Docker environment
-------------------------

Build a Docker image with your choice of Tango version (both of these have been tested to work)::

    $ docker build . -t tangoctl -f Dockerfile --build-arg OCI_IMAGE_VERSION="artefact.skao.int/ska-tango-images-pytango-builder:9.4.2"
    $ docker build . -t tangoctl -f Dockerfile --build-arg OCI_IMAGE_VERSION="artefact.skao.int/ska-tango-images-pytango-builder:9.5.0"

Run the Docker image::

    $ docker run --network host -it tangoctl /bin/bash
    root@346b0ffcf616:/app# ./src/ska_mid_itf_engineering_tools/tango_control/tangoctl.py -h

To use **tangoktl.py** in Docker, you will need to log in on infra::

    # infra login https://boundary.skao.int --enable-ssh
    # infra use za-itf-k8s-master01-k8s
    # tangoctl.py -k

Local installation
==================

To run **tangoctl.py** or **tangoktl.py** on your own computer::

    $ python -m pip install --user .

For a system-wide installation::

    $ sudo python -m pip install .

Manual installation
===================

To run **tangoctl.py** or **tangoktl.py** on your own computer::

    $ mkdir -p ${HOME}/bin
    $ export PATH=${HOME}/bin:${PATH}
    $ ln -s src/ska_mid_itf_engineering_tools/tango_control/tangoctl.py ${HOME}/bin/tangoctl.py
    $ ln -s src/ska_mid_itf_engineering_tools/tango_kontrol/tangoktl.py ${HOME}/bin/tangoktl.py

Also update the Python path and check::

    $ export PYTHONPATH=${PYTHONPATH}:{PWD}/src/ska_mid_itf_engineering_tools
    $ tangoctl.py -h
    $ ./src/ska_mid_itf_engineering_tools/tango_control/tangoctl.py -h

.. image:: img/logo.webp
