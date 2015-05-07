.. _installation:

============
Installation
============

------------
Requirements
------------

SETLyze runs on GNU/Linux, MacOS, and Microsoft Windows. The following software
is required to run SETLyze:

* GTK+ (>=2.24.0,!=2.24.8,!=2.24.10)

* R

* Python (>=2.6 & <2.8)

  * appdirs

  * PyGTK, PyCairo, and PyGObject

  * pandas

  * RPy2

  * xlrd (>=0.8)

Windows users can use the Windows installer for SETLyze, which installs all
dependencies and creates shortcuts in the Start menu and on the desktop.

On Debian (based) systems, the dependencies can be installed from the software
repository::

    sudo apt-get install python-appdirs python-gtk2 python-pandas python-rpy2 \
    python-xlrd r-base-core

More recent versions of some Python packages can be obtained via the Python
Package Index (preferably inside a Python virtualenv)::

    pip install -r requirements.txt

Windows users should install the PyGTK_ all-in-one Windows installer. Then use
``pip`` as described above to install the remaining dependencies. Note that this
step is not needed if you have the Windows installer for SETLyze, which comes
bundeled with the requirements.

------------
Installation
------------

Windows users can use the Windows installer for SETLyze, which installs all
dependencies and creates shortcuts in the Start menu and on the desktop.

If you want to install SETLyze from the GitHub repository::

    git clone https://github.com/figure002/setlyze.git
    pip install setlyze/

Or if you have a source archive file::

    pip install setlyze-x.x.tar.gz

Once installed, the ``setlyze`` executable should be available.

------------
Contributing
------------

Please follow these steps to start working on the SETLyze code base:

1. Fork the project on github.com.
2. Create a new branch.
3. Commit changes to the new branch.
4. Send a `pull request`_.

First make sure that all dependencies are installed as described above. Then
follow the next steps to run and develop SETLyze within a virtualenv_ isolated
Python environment::

    $ git clone https://github.com/figure002/setlyze.git
    $ cd setlyze/
    $ virtualenv --system-site-packages env
    $ source env/bin/activate
    (env)$ pip install -r requirements.txt
    (env)$ python setup.py develop
    (env)$ setlyze

.. _PyGTK: http://www.pygtk.org/downloads.html
.. _Sphinx: http://sphinx-doc.org/
.. _virtualenv: https://virtualenv.pypa.io/
.. _`pull request`: https://help.github.com/articles/creating-a-pull-request/
