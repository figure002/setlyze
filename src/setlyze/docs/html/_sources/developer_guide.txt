.. _developer-guide:

=========================================
SETLyze Developer Guide
=========================================

Welcome to the Developer Guide for SETLyze. This document describes the
SETLyze internals. It’s meant for people who are involved in the
development process of SETLyze. It should be easy for a new developer
to pick up where the last SETLyze developer left off. The purpose of
this guide is to give the new developer full understanding of SETLyze's
internals, its programming style, what's unfinished, et cetera.

Getting Started
###############

Navigating the SETLyze folder
=============================

The key files in SETLyze's root folder are:

src/setlyze/
    This is SETLyze's main code base. This package folder contains
    all of SETLyze's modules. This is the folder where you'll be
    editing most Python source files for SETLyze.

src/setlyze.pyw
    This is SETLyze's executable. This is what you'll run to start SETLyze.

src/setlyze/docs/html/
    This folder contains the documentation for SETLyze. This includes
    the User Manual and the Developer Guide. You can view the manual
    by (double) clicking index.html. This should open the documentation
    in your web browser.

src/doc-src/
    This folder contains the files used to build the documentation. This is
    done using Sphinx. Some parts of the documentation are from
    ``.rst``-files within this folder, others are extracted from the
    documentation strings within the program source code.

README
    This text file contains a short description of the program and directs
    you to other documentation.

COPYING
    This text file contains the license for SETLyze. SETLyze is released
    under the GNU General Public License version 3.

INSTALL
    Text file with installation instructions for SETLyze.


Technical Design
================

SETLyze comes with a :download:`Technical Design <./technical_design_setlyze-0.1.pdf>`;
a visual representation of SETLyze's design parts (functions/classes/GUI's)
interconnected by arrows representing the application's functions and work
flow. All design parts are numbered. The same numbers can be found in the
SETLyze's source code. This means that the different design parts of the
Technical Design can be easily linked to the corresponding source code.

The Technical Design provides an easy to understand overview of the
application for users, but is also of great value to developers. It makes it
easier to get a basic understanding of how the application works by looking
at the Technical Design. If the developer is interested in a specific part of
the application, he or she can easily navigate to the corresponding description
and source code by the reference numbers used in the Technical Design.

Both the descriptions and source codes for the design parts in the Technical
Design are browsable using this documentation. Read the "Design Parts" section
below.

Design Parts
------------

The links below will guide you to the different design parts present in the
Technical Design. You just have to click in the the number for that design
part. Clicking on a design part will show you its description. Next to the
description is a link "[source]" which links to the corresponding source code.

.. toctree::
   :maxdepth: 2

   design_parts_index

Navigating the SETLyze Code Base
================================

SETLyze's many functions and classes are stored in different modules.
Classes and functions with similar functions are placed in the same module.

Below is an overview of all modules for SETLyze. You can click on a
module to get a description of that module and all its elements. You can
even view the source-code for a specific function or class by clicking
the *[source]* link on the right side of the description.

SETLyze modules
---------------

.. toctree::
   :maxdepth: 4

   setlyze_modules

Coding Style Guidelines
#######################

Code layout
===========

Please write `PEP-8 <http://www.python.org/peps/pep-0008.html>`_
compliant code.

One often-missed requirement is that the first line of docstrings
should be a self-contained one-sentence summary.

We use 4 space indents for blocks, and never use tab characters.

Trailing white space should be avoided, but is allowed. If possible,
configure your text editor to automatically remove trailing spaces and
tabs upon saving.

Unix style newlines (LF) are used.

Each file must have a newline at the end of it.

Lines should be no more than 79 characters if at all possible. Use a
text editor that has some kind of long line marker indicating the 79
characters boundary.
Lines that continue a long statement may be indented in either of
two ways:

within the parenthesis or other character that opens the block, e.g.::

    my_long_method(arg1,
                   arg2,
                   arg3)

or indented by four spaces::

    my_long_method(arg1,
        arg2,
        arg3)

The first is considered clearer by some people; however it can be a bit
harder to maintain (e.g. when the method name changes), and it does not
work well if the relevant parenthesis is already far to the right. Avoid
this::

     self.legbone.kneebone.shinbone.toebone.shake_it(one,
                                                     two,
                                                     three)

but rather ::

     self.legbone.kneebone.shinbone.toebone.shake_it(one,
         two,
         three)

or ::

     self.legbone.kneebone.shinbone.toebone.shake_it(
         one, two, three)

For long lists, we like to add a trailing comma and put the closing
character on the following line. This makes it easier to add new items in
the future::

    from setlyze.std import (
        uniqify,
        median,
        distance,
        )

There should be spaces between function parameters, but not between the
keyword name and the value::

    call(1, 3, cheese=quark)

Module Imports
==============

* Imports should be done at the top-level of the file, unless there is
  a strong reason to have them lazily loaded when a particular
  function runs. Import statements have a cost, so try to make sure
  they don't run inside hot functions.

* Preserved namespaces when importing modules, e.g.:

  Correct: ::

    import setlyze.config

  But avoid this: ::

    import setlyze.config as config

  Preserving the namespaces makes it easier for the developers to understand
  where a specific class, method, function or variable originates from.

  We do make one exception: ::

    from sqlite3 import dbapi2 as sqlite

  This is because we want to avoid the use of version numbers in namespaces.

Naming
======

Functions, methods or members that are relatively private are given
a leading underscore prefix.

We prefer class names to be concatenated capital words (``TestCase``)
and variables, methods and functions to be lowercase words joined by
underscores (``revision_id``, ``get_revision``).

For the purposes of naming some names are treated as single compound
words: "filename", "revno".

Consider naming classes as nouns and functions/methods as verbs.

Try to avoid using abbreviations in names, because there can be
inconsistency if other people use the full name.


Standard Names
==============

``revision_id`` not ``rev_id`` or ``revid``

Functions that transform one thing to another should be named ``x_to_y``
(not ``x2y`` as occurs in some old code.)


Event and Signal Handling
=========================

A large part of SETLyze is controlled with signals and signal handlers. To emit
custom application signals we use :meth:`setlyze.std.sender.emit`. And to
connect a signal to a signal handler, we use :meth:`setlyze.std.sender.connect`.
When signal handlers are no longer needed, use
:meth:`setlyze.std.sender.disconnect` to disconnect the handler from the signal.
Calling :meth:`setlyze.std.sender.disconnect` should generally be done when
the instance that called :meth:`setlyze.std.sender.connect` is destroyed.


License Statement
=================

SETLyze is released under the GNU General Public License version 3.
Each file that's part of SETLyze must have the copyright notice and
copying permission statement included at the top of the file after
the encoding declaration. So the top of each file should look like this: ::

    #!/usr/bin/env python
    # -*- coding: utf-8 -*-
    #
    #  Copyright 2010, GiMaRIS <info@gimaris.com>
    #
    #  This file is part of SETLyze - A tool for analyzing the settlement
    #  of species on SETL plates.
    #
    #  SETLyze is free software: you can redistribute it and/or modify
    #  it under the terms of the GNU General Public License as published by
    #  the Free Software Foundation, either version 3 of the License, or
    #  (at your option) any later version.
    #
    #  SETLyze is distributed in the hope that it will be useful,
    #  but WITHOUT ANY WARRANTY; without even the implied warranty of
    #  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    #  GNU General Public License for more details.
    #
    #  You should have received a copy of the GNU General Public License
    #  along with this program.  If not, see <http://www.gnu.org/licenses/>.


Testing and Optimization
########################

The following document describes the steps taken to test and optimize SETLyze.

.. toctree::
   :maxdepth: 2

   testing_optimization


Distribution
############

The following document describes how to create the distribution packages and
installers for SETLyze.

.. toctree::
   :maxdepth: 2

   distribution
