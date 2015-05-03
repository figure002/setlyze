=======
SETLyze
=======

The purpose of SETLyze is to provide the people involved with the SETL project
an easy and fast way of getting useful information from the data stored in the
SETL database. The SETL database at GiMaRIS contains data about the settlement
of species in Dutch waters. SETLyze helps provide more insight in a set of
biological questions by performing a set of analyses on this data.

.. image:: https://readthedocs.org/projects/setlyze/badge/?version=latest
        :target: https://readthedocs.org/projects/setlyze/?badge=latest
        :alt: Documentation Status


Requirements
============

SETLyze has the following dependencies:

* GTK+ (>=2.24.0,!=2.24.8,!=2.24.10)

* R

* Python (>=2.6 & <2.8)

  * appdirs

  * PyGTK, PyCairo, and PyGObject

  * pandas

  * RPy2

  * xlrd (>=0.8)

On Debian (based) systems, the dependencies can be installed from the software
repository::

    sudo apt-get install python-appdirs python-gtk2 python-pandas python-rpy2 \
    python-xlrd r-base-core

More recent versions of some Python packages can be obtained via the Python
Package Index::

    pip install -r requirements.txt

Windows users can install the PyGTK_ all-in-one Windows installer. Then use
``pip`` as described above to install the remaining dependencies. Note that this
step is not needed if you have the Windows installer for SETLyze, which comes
bundeled with the requirements.


Installation
============

From the GitHub repository::

    git clone https://github.com/figure002/setlyze.git
    pip install setlyze/

Or if you have a source archive file::

    pip install setlyze-x.x.tar.gz


Documentation
=============

The documentation can be found here:

http://setlyze.readthedocs.org/

Alternatively, the same documentation can be built using Sphinx_::

    $ python setup.py build_sphinx

Then launch ``build/sphinx/html/index.html`` in your browser.


Contributing
============

Please follow the next steps:

1. Fork the project on github.com.
2. Create a new branch.
3. Commit changes to the new branch.
4. Send a `pull request`_.

Follow the next steps to run and develop SETLyze within a virtualenv_ isolated
Python environment::

    $ git clone https://github.com/figure002/setlyze.git
    $ cd setlyze/
    $ virtualenv --system-site-packages env
    $ source env/bin/activate
    (env)$ pip install -r requirements.txt
    (env)$ python setup.py develop
    (env)$ setlyze


License
=======

SETLyze is free software. See LICENSE.txt for details.


.. _PyGTK: http://www.pygtk.org/downloads.html
.. _Sphinx: http://sphinx-doc.org/
.. _virtualenv: https://virtualenv.pypa.io/
.. _`pull request`: https://help.github.com/articles/creating-a-pull-request/
