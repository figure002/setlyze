.. _distribution:

=======================
Distribution of SETLyze
=======================

This guide shows the developer how to distribute SETLyze, making it
available for the user.

The purpose of this document is to give the developers instructions on how to
distribute SETLyze. This includes building an installer for Windows, and source
packages mainly for GNU/Linux users and developers. New developers will have
to do this at some point, so this document was created for their convenience.

Distribution on Windows: Building an Installer
##############################################

SETLyze should be as easy as possible to install on Windows machines and
most users don't want to worry about downloading and installing SETLyze's
pre-requisites. Thus a Windows installer (also called a "setup") which installs
SETLyze along with all its pre-requisites is required. This guide explains how
to create the Windows installer for SETLyze using NSIS (Nullsoft Scriptable
Install System), a professional open source system to create Windows installers.

.. figure:: windows_installer.png
   :scale: 100 %
   :alt: Screenshot of the Windows installer for SETLyze
   :align: center

   Screenshot of the Windows installer for SETLyze

To start off, you'll need a Windows machine (preferably Windows XP or higher)
to build the installer. Once you have that, read on to the next part.

Preparing your Windows environment
==================================

Before you can start building the installer, we need to make some preparations.
You first need to make sure that SETLyze runs flawlesly on your Windows machine.
Let's try to get SETLyze running using only the source package. Do **not** use
the Windows installer to get SETLyze running on your system.

First download and install all of SETLyze's pre-requisites on the
Windows machine. You'll need to download and install the tools in the order
of this list below. Well actually the order doesn't matter, but the Python
modules (marked with an asterisk) need to be installed *after* Python itself
is installed. It is important that you get the right versions as well.
If no version number is given in the list below, than it means you can get the
latest version. The tools marked with an asterisk (*) are Python modules,
meaning they are available for different versions of Python. Since we're using
Python 2.6, it is required that you download the versions for Python 2.6.
Look at the suffix of the installer's filenames, they should end with "-py2.6.exe".
Download only 32bit versions of the tools below. The 32bit installers often
have "win32" or "x86" (not "x86-64") in the filename.

#. `Python <http://www.python.org/download/releases/2.6.6/>`_ (>=2.6 & <2.7)
#. `GTK2 Runtime <http://gtk-win.sourceforge.net/home/index.php/Downloads>`_ (>=2.22)
#. `R <http://cran.xl-mirror.nl/bin/windows/base/old/2.9.1/>`_ (=2.9.1)
#. `PyGTK <http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/>`_ (>=2.22) *
#. `PyCairo <http://ftp.gnome.org/pub/GNOME/binaries/win32/pycairo/>`_ (>=1.8.6) *
#. `PyGObject <http://ftp.gnome.org/pub/GNOME/binaries/win32/pygobject/>`_ (>=2.26) *
#. `setuptools <http://pypi.python.org/pypi/setuptools#files>`_ *
#. `RPy <http://sourceforge.net/projects/rpy/files/rpy/>`_ (>=1.0.3) *
#. `Python Win32 Extensions <http://sourceforge.net/projects/pywin32/files/pywin32/>`_ (>=214) *

You might wonder why Python 2.6, and not the latest version, Python 3. The
reason we're using an older version is because of the Python modules SETLyze
requires. Most are only available for Python 2.6 and Python 2.7. There's a
good chance that SETLyze runs on Python 2.7 as well, but for now Python 2.6 is
sufficient.

Also notice that we are specifically using R version 2.9.1. This is because
the RPy module must correspond to the version of R and Python you have
installed. The latest version of RPy at the time of writing this is version
1.0.3, which has the filename ``rpy-1.0.3-R-2.9.0-R-2.9.1-win32-py2.6.exe``.
This means it requires R versions 2.9.0 through 2.9.1. There is also RPy2, a
redesign and rewrite of RPy. During the development of the initial version
of SETLyze, it was too hard to get RPy2 working well on Windows, which is why
was decided to use the older but stable RPy. It is possible to migrate to RPy2
and newer versions of R, but this requires changes in the source code of
SETLyze, as RPy2 works slightly different.

Running and Testing SETLyze
===========================

Now that you have installed all of SETLyze's pre-requisites, you can try to
run SETLyze. First obtain SETLyze's source package. The source package is
called "setlyze-x.x.tar.gz" or "setlyze-x.x.zip" where ``x.x`` is the version
number. You can use `7-Zip <http://www.7-zip.org/>`_ to unpack the contents of
the source package. This should yield a new folder called ``setlyze-x.x``. This
folder contains SETLyze's source code. Run ``setlyze.pyw`` from the folder you
just extracted and see if it works. You should rename it to ``setlyze.py`` first
which shows the DOS window so you can see all error/warning/info messages
returned by SETLyze (as an alternative you can also run ``python setlyze.pyw``
from a DOS window). If you've thoroughly tested SETLyze and found no problems
or error messages, you can continue with the next step. But don't forget to
rename the executable back to ``setlyze.pyw`` if you've renamed it.

Preparing the Distribution Folder
=================================

A developer package for SETLyze (``setlyze-x.x-dev.tar.gz``) is available as a
separate download. This package was created for the developer. It contains the
source files of the Sphinx documentation and the files used to build the Windows
installer. Use 7-Zip to unpack the content of the package. This should yield a
new folder called ``setlyze-x.x-dev``. This folder contains the following files
and directories: ::

    setlyze-x.x-dev/
    |-- dependencies
    |-- head
    |   |-- icon.ico
    |   `-- setup-win.py
    |-- setlyze_setup_modern.nsi
    `-- sphinx-docs
        |-- make.bat
        |-- Makefile
        `-- source

Basically, this package, along with SETLyze's source package is all you need
to continue the development of SETLyze. I shall now explain each of the files
and directories present in the developer package.

dependencies
    This folder is for Windows installers of some of SETLyze's pre-requisites that
    will be incorporated in SETLyze's Windows installer. For SETLyze 0.1, this
    folder should just contain the installer for R. Later will be clear why
    not all of SETLyze's pre-requisites are put here.

head
    This folder should contain the contents of SETLyze's source package.
    Remember the folder ``setlyze-x.x`` we got after unpacking the source
    package? The contents of that folder should go into the ``head`` folder.

icon.ico
    This is the icon used for the Windows installer and for the Windows
    executable of SETLyze.

setup-win.py
    This script is used to build the Windows executable for SETLyze. This
    script uses py2exe for that. This script is *not* intended for installing
    SETLyze (opposed to "setup.py" in the source package).

setlyze_setup_modern.nsi
    This is the NSIS script we will use to build SETLyze's Windows installer.
    This script is a regular text file. You can open it in a text editor
    (e.g. Notepad++). This script contains all the information required for
    building the Windows installer.

sphinx-docs
    This folder contains the source of the Sphinx documentation for SETLyze.
    This folder is all you need to work on SETLyze's documentation. The
    subfolder ``source`` contains the source files of the documentation. The
    source files end with the extension ".rst". You can edit these with a text
    editor. After editing the source files, you can use the make files
    ("Makefile" on Linux, "make.bat" on Windows) to generate the actual
    documentation. Refer to the `Sphinx documentation <http://sphinx.pocoo.org/contents.html>`_
    for instructions.

Let's prepare the developer package folder. Follow these steps:

1. Copy the Windows installer for R 2.9.1 in the ``dependencies`` folder. The
   installer is called ``R-2.9.1-win32.exe``.
2. Copy SETLyze's source files in the ``head`` folder. This means, extract
   "setlyze-x.x.tar.gz" and copy the contents of the resulting ``setlyze-x.x``
   folder into the ``head`` folder.

Building the Windows Executable for SETLyze
===========================================

The next step is to create a Windows executable for SETLyze. At this point,
one can start SETLyze by running ``setlyze.pyw`` from the source package.
So ``setlyze.pyw`` is SETLyze's executable, but it is a regular Python script,
and one needs to have Python and all of SETLyze's pre-requisites installed to
run the script. We don't want Windows users to have to download and install
all these extra tools. So before creating the installer, we're going to create
a special Windows executable (``setlyze.exe``) which does *not* require users
to have Python and all the pre-requisites installed (with one exception). For
this purpose we're going to use `py2exe <http://www.py2exe.org/>`_. Download
the latest py2exe for Python 2.6 from `here <http://sourceforge.net/projects/py2exe/files/>`_
and install it on your Windows machine.

Once you have py2exe installed, building the Windows executable should be a
breeze with the provided ``head/setup-win.py``. Open up a DOS window and run the
following command: ::

    python setup-win.py py2exe

.. note::

   Running Python from the command-line (or DOS) requires that you have Python
   in your PATH environment variable. Python is not added to PATH by default. If
   the above command gives you a message like:

   "'python' is not recognized as an internal or external command, operable
   program or batch file."

   then you need to make sure that your computer knows where to find the
   Python interpreter. To do this you will have to modify a setting called
   PATH, which is a list of directories where Windows will look for programs.

   The `Python on Windows FAQ <http://docs.python.org/faq/windows.html>`_
   explains how to do this. Search for "PATH environment variable" on that page
   (Ctrl+F, type "PATH environment variable", hit Enter).

This should create a new folder called ``head\dist\``. Open it in Windows
Explorer. You should now see a whole bunch of files, including ``setlyze.exe``.

Go ahead and see if it runs. Double clicking ``setlyze.exe`` should open up
SETLyze's main window. You might notice something different though. For example,
the windows look really ugly. Remember that this Windows executable doesn't
need to have Python etc. installed. The executable is now actually using
it's own copy of Python (``python26.dll``), GTK (``libgtk-win32-2.0-0.dll``),
and all the other stuff it requires. Py2exe has automatically collected all the
files required to run SETLyze and put them in one folder. But the GTK2-Runtime
requires some extra files to make the windows look nice (py2exe doesn't
include these files automatically). So we need to manually copy these files to
the ``head\dist\`` folder.

Manually copy the following folders to the ``head\dist\`` folder:

* ``C:\Program Files\GTK2-Runtime\etc\``
* ``C:\Program Files\GTK2-Runtime\lib\``
* ``C:\Program Files\GTK2-Runtime\share\``

Again run ``setlyze.exe``. SETLyze should now look like a native
Windows application, no more ugly windows. But we are not there yet. Try to
use one of SETLyze Help buttons. You'll notice that it doesn't work. This is
because it's looking for the documentation files in the ``head\dist\docs\``
folder. This folder doesn't exist yet. The ``setup-win.py`` script doesn't
automatically copy the ``head\setlyze\docs\`` folder to the ``head\dist\``
folder. This is not yet built into the ``setup-win.py`` script, so you'll have
to copy it manually.

Copy the folder ``head\setlyze\docs\`` to the ``head\dist\`` folder. The contents
of ``head\setlyze\docs\`` were originally copied from ``setlyze-x.x-dev\sphinx-docs\build\html\``
(see the Sphinx documentation on how to build the HTML documentation).
The ``html`` folder contains the built HTML documentation for SETLyze. So in the
future, after you've updated the documentation, you rebuild the HTML
documentation and copy the folder ``setlyze-x.x-dev\sphinx-docs\build\html\``
to ``head\dist\`` and rename ``head\dist\html\`` to ``head\dist\docs\``. Again
try one of SETLyze's Help buttons. The help contents should now open in your
browser.

At this point, the ``head\dist\`` folder contains almost all files required to
run SETLyze. I say almost, because one still needs to have R installed to
run ``setlyze.exe``. But we'll get to that later. Check, and double check that
``setlyze.exe`` works the way it should. The contents of your ``setlyze-x.x-dev``
folder should now look similar to the tree below. Verify that your directory
structure matches. ::

    (For the sake of simplicity, this tree only shows the important files and folders)

    setlyze-x.x-dev/
    |-- dependencies
    |   `-- R-2.9.1-win32.exe
    |-- head
    |   |-- COPYING
    |   |-- dist
    |   |   |-- COPYING
    |   |   |-- etc
    |   |   |-- images
    |   |   |-- lib
    |   |   |-- README
    |   |   |-- setlyze.exe
    |   |   |-- share
    |   |   |-- test-data
    |   |   |-- docs
    |   |   `-- ...
    |   |-- icon.ico
    |   |-- INSTALL
    |   |-- MANIFEST.in
    |   |-- README
    |   |-- setlyze
    |   |-- setlyze.pyw
    |   |-- setup.py
    |   |-- setup-win.py
    |   |-- test-data
    |   `-- tests
    |-- setlyze_setup_modern.nsi
    `-- sphinx-docs


Building the Windows Installer
==============================

Now that you have prepared the ``setlyze-x.x-dev`` folder, you can start
building the Windows installer for SETLyze. The structure of the
``setlyze-x.x-dev`` folder is important, because the NSIS script
("setlyze_setup_modern.nsi") expects to find a number of files and folders in
the ``setlyze-x.x-dev`` folder, and packs these into a single installer. The
files and folders it uses are as follows: ::

    setlyze-x.x-dev/
    |-- dependencies
    |   `-- R-2.9.1-win32.exe
    `-- head
        |-- COPYING
        |-- README
        |-- icon.ico
        `-- dist

Open ``setlyze_setup_modern.nsi`` in a text editor (e.g. Notepad++) and see if
you can find the directives that load these files (hint: search for "File"). You
do not need to understand everything what's in the NSIS script right now.
You just need to be able to edit it. All directives need to be correct, or else
building the installer will fail.

Once all files are in place, it's time to compile the NSIS script. Compiling
means that we will build the actual installer from the NSIS script. You'll first
need to download and install `NSIS (Nullsoft Scriptable Install System) <http://nsis.sourceforge.net/>`_.

Once NSIS is installed, you can build the Windows installer by simply
right-clicking ``setlyze_setup_modern.nsi`` and choosing "Compile NSIS Script".
Give NSIS a moment to process the script and compile the installer. If the
script is correct, it should produce the Windows installer in the same folder,
called something similar to ``setlyze-0.1-bundle-win32.exe``.

Last, but not least you should to test the installer. You should do this on a
*clean* installation of Windows. Meaning you should test this on a Windows
machine with no extra software installed, because only then can you really say
that the installer and the resulting SETLyze executable works. An easy way to
get a clean installation, is to install Windows on a virtual machine
(e.g. VirtualBox) and test the installer before any other software is installed.


Building a Source Package
#########################

The source package is nothing more than an archive (.tar.gz on Linux, .zip on
Windows) containing the application's source code. Distributing the
application's source code is what defines open source software. This allows
everyone to see how SETLyze was created, but also to edit, use, and learn from
it. This package can also be used to install SETLyze on all supported
operating systems, including Windows and GNU/Linux. This can be done with the
included ``setup.py``. This part of the guide explains how to create the
source package.

From now on, well need to start using DOS. The standard DOS console in Windows
is very annoying to work with. So I highly recommend you to install `Console2
<http://sourceforge.net/projects/console/>`_ and use that instead. Open up a
DOS window and ``cd`` to the ``head`` folder. The DOS command for this looks
something like this: ::

    cd "C:\Documents and Settings\Serrano\My Documents\setlyze-0.1-dev\head"

Of course you need replace that path with the path to your ``head`` folder.
Now list all files in that folder by typing ``dir``. Remember that this is the
folder to which you copied SETLyze's source files. You should see a file called
``setup.py``. This script can do lots of great things, and creating a source
distribution is one of those (see `An Introduction to Distutils <http://docs.python.org/distutils/introduction.html>`_).
To create the source package, type the following command from the DOS window: ::

    python setup.py sdist

.. note::

   Running Python from the command-line (or DOS) requires that you have Python
   in your PATH environment variable. Python is not added to PATH by default. If
   the above command gives you a message like:

   "'python' is not recognized as an internal or external command, operable
   program or batch file."

   then you need to make sure that your computer knows where to find the
   Python interpreter. To do this you will have to modify a setting called
   PATH, which is a list of directories where Windows will look for programs.

   The `Python on Windows FAQ <http://docs.python.org/faq/windows.html>`_
   explains how to do this. Search for "PATH environment variable" on that page
   (Ctrl+F, type "PATH environment variable", hit Enter).

If all goes well, this should create a new folder called ``dist`` in the ``head``
folder. Open this folder in Windows Explorer. And voila, you should see a file
called ``setlyze-x.x.zip``. This is your new source package. Check out the
contents of the .zip and check if all files are present. The ``setup.py`` script
together with ``MANIFEST.in`` define which files are put in the source package
(see `Creating a Source Distribution <http://docs.python.org/distutils/sourcedist.html>`_).
Do note that the source package now has the extension .zip instead of .tar.gz.
This is because .zip is the default for Windows, and .tar.gz is the default for
Linux. It's usual to provide both a .tar.gz and a .zip file: ::

    python setup.py sdist --formats=gztar,zip

.. note::

   There's a catch though, you'll need GNU/Linux to create the .tar.gz file.

The resulting source packages are ready for distribution. Do make sure that
the packages aren't missing any files.
