=========================================
Welcome to SETLyze's documentation!
=========================================

About SETLyze
=========================================

The purpose of SETLyze is to provide the people involved with the SETL project
an easy and fast way of getting useful information from the data stored in the
SETL database. The SETL database at `GiMaRIS <http://www.gimaris.com/>`_
contains data about the settlement of species in Dutch waters. SETLyze helps
provide more insight in a set of biological questions by analyzing this data.
SETLyze can perform the following set of analyses:

*Spot Preference*
    Determine a species' preference for a specific location on a SETL plate.
    Species can be combined so that they are treated as a single species.

*Attraction within Species*
    Determine if a species attracts or repels individuals of its own kind.
    Species can be combined so that they are treated as a single species.

*Attraction between Species*
    Determine if two different species attract or repel each other. Species
    can be combined so that they are treated as a single species.

Additionally, any of the above analyses can be performed in batch mode, meaning
that the analysis is repeated for each species of a species selection. Thus
an analysis can be easily performed on an entire data set without intervention.
Batch mode for analyses are parallelized such that the computing power of a
computer is optimally used.

The following analysis will be implemented in the next version:

*Relation between Species*
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

