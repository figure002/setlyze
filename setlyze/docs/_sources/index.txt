=========================================
Welcome to SETLyze's documentation!
=========================================

About SETLyze
=========================================

The purpose of SETLyze is to provide the people involved with the SETL-project
an easy and fast way of getting useful information from the data stored in the
SETL database. The SETL database at `GiMaRIS <http://www.gimaris.com/>`_ contains data about the settlement
of species in Dutch waters. SETLyze helps provide more insight in a set of
biological questions by analyzing this data. SETLyze is capable of performing
the following set of analyses:

*Analysis 1 "Spot Preference"*
    Determine a species’ preference for a specific location on a SETL plate.
    Species can be combined so that they are treated as a single species.

*Analysis 2 "Attraction of Species (intra-specific)"*
    Determine if a species attracts or repels individuals of its own kind.
    Species can be combined so that they are treated as a single species.

*Analysis 3 "Attraction of Species (inter-specific)"*
    Determine if two different species attract or repel each other. Species
    can be combined so that they are treated as a single species.

The following analysis will be implemented in the next version:

*Analysis 4 "Relation between Species"*
    Determine if there is a relation between the presence/absence of two
    species in a specific location. Plates per location are compared. Also
    instead of looking at different plate surfaces, only the presence or
    absence of a species on a plate is taken into account.

Documentations
=========================================

.. toctree::
   :maxdepth: 2

   user_manual
   developer_guide
   references
   legal
   about_us

Indices and tables
=========================================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

