=========================================
SETLyze User Manual
=========================================

Welcome to the user manual for SETLyze. This manual is intended for the
end user and explains how to use SETLyze.

Introduction to SETLyze
#######################

SETLyze is a part of the SETL-project, a fouling community study focussing on
marine invasive species. The website describes the SETL-project as follows:

    "Over the last ten years, marine invaders have had a dramatically
    increasing impact on temperate water ecosystems around the world.
    Substantial ecological and economical damage has been caused by the
    introduction of diseases, parasites, predators, invaders outcompeting
    native species, and species that are a nuisance for public health,
    tourism, aquaculture or in any other way. In the SETL-project
    standardized PVC-plates are used to detect these invasive species
    and other fouling community organisms. The material and methods of
    the SETL-project were developed by the ANEMOON foundation in
    cooperation with the Smithsonian Marine Invasions Laboratory of
    Smithsonian Environmental Research Centre. In this project 14x14
    cm PVC-plates are hung 1 meter below the water surface, and refreshed
    and checked for species at least every three months." ---
    `ANEMOON foundation <http://www.anemoon.org/>`_

Data collected from these SETL plates are being collected in
the SETL database. This database contains over 25000 records containing
information of over 200 species in different localities throughout the
Netherlands. SETLyze is an application which is capable of performing
a set of analysis on the data from the SETL database. SETLyze is
capable of performing the following analyses:

*Analysis 1 "Spot Preference"*
    Determine a species’ preference for a specific location on a SETL
    plate.

*Analysis 2 "Attraction of Species (intra-specific)"*
    Determine if a specie attracts or repels individuals of its own kind.

*Analysis 3 "Attraction of Species (inter-specific)"*
    Determine if two different species attract or repel each other.

The following analysis will be implemented in the next version:

*Analysis 4 "Relation between Species"*
    Determine if there is a relation between two (groups of) species on
    SETL plates in a location. Plates per location are compared. Also
    instead of looking at different plate spots, only the presence or
    absence of a specie on a plate is taken into account.

Data Collection
===============

First let's have a look at how the data for the SETL-project is being
collected. When the SETL plates are checked, each plate is first
carefully pulled out of the water and then photographed. This is
done by a standard procedure described on the ANEMOON
foundation's website. First an overview photograph is taken of each
plate. Then some more detailed photographs are taken of the species
that grow on each plate. Indivdual plates are recognized by their tags.
The pictures are then carefully analyzed. For each plate the
SETL-monitoring form is filled in. For each species the absence or
presence, abundance and area cover are filled in. For this, a 5x5 grid
is digitally applied over the photograph. For each specie the presence
or absence on each of the 25 plate surfaces are filled in and saved
to the database.

.. _fig_plate_with_grid:

.. figure:: setl_plate_with_grid.png
   :scale: 100 %
   :alt: SETL plate with a grid
   :align: center

   Figure 1. SETL-plate with digitally applied grid

Each record in the database contains a specie ID, a plate ID, and
the 25 plate surfaces. The specie ID links to the specie that was found
on the plate. The plate ID links to the plate on which that specie was
found. The plate ID is also linked to the location where this plate
was deployed. The 25 plate surfaces ("spots") are stored in each record
as booleans (meaning they can have a value of True or False). The value
1 (True) for a spot means that the specie in question was present on
that spot of the plate. The value 0 (False) means that the specie
was absent from that spot.

With 25 spots x 2500 records = 625000+ booleans for the presence/absence of species,
automatic methods of analyzing this data are required. Hence SETLyze
was developed, a tool for analyzing the settlement of species
on SETL plates.

Requirements
############

To use SETLyze you will need:

Hardware
    * Disk space: 2 MB (source) / 70+ MB (Windows® setup)
    * 512 MB RAM

Software
    * Microsoft® Windows® or GNU/Linux*

\* Linux users will need to manually install the software dependencies. See
the "Installation" section below.


Installation
############

Microsoft® Windows®
===================

For Windows® users, an installer is available that includes the SETLyze
core package together with the necessary pre-requisites.

GNU/Linux
=========

For GNU/Linux users, a source package is available. The source package
doesn't contain the software dependencies. GNU/Linux user can use their
package manager to install the dependencies.

On Ubuntu or other Debian derivatives, installing the dependencies
can be done with the following command: ::

    sudo apt-get install python python-gtk2 python-rpy python-setuptools

Once all dependencies are installed, extract the source package and start
SETLyze by running "setlyze.pyw".

If you want to install SETLyze system wide, you can do so with the
provided setup script. The following command will install
SETLyze's modules to an existing Python installation and copies
SETLyze's executable "setlyze.pyw" to the system's "bin" folder. ::

    sudo python setup.py install

Once installed, SETLyze can be started from the command-line with, ::

    setlyze.pyw


Using SETLyze
#############

SETLyze comes with a graphical user interface (GUI). The GUI consists
of dialogs which all have a specific task. These dialogs will guide
you in performing the set of analyses it provides. Most of SETLyze's
dialogs have a Help button. Clicking this Help button should point you
to the corresponding dialog description on this page. All dialog
descriptions can be found in the :ref:`SETLyze dialogs <setlyze-dialogs>`
section of this manual.

Before SETLyze can perform an analysis, it needs access to a data
source containing SETL data. Currently just one data source is
supported: manually exported CSV files from the Microsoft Access SETL
database. This means that the user must first export the tables of the
SETL database from Microsoft Access to CSV files. This would result in
four CSV files, one for each table. The user is then required to load
these files into SETLyze. First follow :ref:`the steps to export the
SETL data to CSV files <export-csv-msaccess>`.

You can perform an analysis once you have the four CSV files containing
the SETL data. First run SETLyze by (double) clicking the file named
``setlyze.pyw``. You should be presented with the
:ref:`analysis selection dialog <dialog-analysis-selection>`. Select
the analysis you want to perform and press OK to begin. A new dialog
will be displayed, most likely the
:ref:`locations selection dialog <dialog-loc-selection>`.

If this is your first time running SETLyze, the locations selection
dialog will show an empty locations list. The list is empty because the
data source has not been set yet. To set the data source and load the
SETL data, click on the `Change Data Source` button to open the
:ref:`change data source dialog <dialog-change-data-source>`. This
dialog allows you to load the data from the CSV files you've just
created.

Once the data has been loaded, the locations selection dialog will
automatically update the list of locations. From here on it's just a
matter of following the instruction one the dialogs. Should you need
more help, scroll down to the :ref:`SETLyze dialogs <setlyze-dialogs>`
section for a more extensive description of each dialog. The dialog
descriptions are also accessible from SETLyze's dialogs itself by
clicking the Help button on a dialog.

Definition List
===============

This part of the user manual describes some terminology often used
throughout the application and this manual.

Intra-specific
    Within a single species.

Inter-specific
    Between two different species.

Plate area
    The defined area on a SETL-plate. By default the SETL-plate is divided in
    four plate areas (A, B, C and D). See :ref:`figure 7 <fig_plate_areas_default>`.
    Plate areas can be combined, see :ref:`Define Plate Areas dialog <dialog-define-plate-areas>`.

Positive spot
    Each record in the SETL database contains data for each of the 25
    spots on a SETL plate. The spots are stored as booleans, meaning
    they can have two values; 1 (True) means that the specie was present
    on that spot, 0 (False) means that the species was absent on
    that spot. A spot is "positive" if the spot value is 1 or True. Each
    record can thus have up to 25 positive spots.

SETL-plate
    In the SETL-project standardized PVC-plates are used to detect invasive
    species and other fouling community organisms. In this project 14x14
    cm PVC-plates are hung 1 meter below the water surface, and refreshed
    and checked for species at least every three months.

Spot
    To analyze SETL plates, photographs of the plates are taken. The
    photographs are then analyzed on the computer by applying a 5x5
    grid to the photographs. This divides the SETL plate into 25 equal
    surface areas (see :ref:`figure 1 <fig_plate_with_grid>`). Each
    of the 25 surface areas are called "spots". Species are scored for
    presence/absence for each of the 25 spots on each SETL plate, and the
    data is stored in the SETL database in the form of records. So each
    SETL record in the database contains presence/absence data of one
    specie for all 25 spots on a SETL plate.

.. _setlyze-dialogs:

SETLyze dialogs
###############

SETLyze comes with a graphical user interface consisting of separate
dialogs. The dialogs are described in this section.

.. _dialog-analysis-selection:

Analysis Selection dialog
=========================

.. figure:: dialog_select_analysis.png
   :scale: 100 %
   :alt: Analysis Selection dialog
   :align: center

   Figure 2. Analysis Selection dialog

The analysis selection dialog is the first dialog you see when SETLyze
is started. It allows the user to select an analysis to perform on SETL
data. The user can select one of the analyses in the list and click on
the OK button to start the analysis. Clicking the Quit button closes
the application.

After pressing the OK button, two things can happen. If no SETL data was
found on the user's computer, SETLyze automatically tries to load SETL
localities and species data from the remote SETL database. This requires
a direct connection with the SETL database server. A progress dialog is
shown while the data is being loaded. If connecting to the remote
database fails, SETLyze continues without data.

If SETL data is found on the user's computer, a message dialog is shown
presenting the user with two options. Option one is to use the SETL data
that was previously saved to the user's computer. Option two is to
discard the saved data and load data from the remote SETL database.

Clicking the About button shows SETLyze's About dialog. The About dialog
shows basic information about SETLyze; its version number, license
information, a link to the GiMaRIS website, the application developers,
and contact information.

.. _dialog-loc-selection:

Locations Selection dialog
==========================

.. figure:: dialog_locations_selection.png
   :scale: 100 %
   :alt: Locations Selection dialog
   :align: center

   Figure 3. Locations Selection dialog

The locations selection dialog shows a list of all SETL localities. This
dialog allows you to select locations from which you want to select
species. The :ref:`species selection dialog <dialog-spe-selection>`
(displayed after clicking the Continue button) will only display the
species that were recorded in the selected locations. Subsequently this
means that only the SETL records that match both the locations and
species selection will be used for the analysis, as each SETL record
is bound to a specie and a SETL plate from a specific location.

The `Change Data Source` button opens the
:ref:`change data source dialog <dialog-change-data-source>`. This
dialog allows you to switch to a different data source. After doing so,
the locations selection dialog is automatically updated with the new
data.

The Back button allows you to go back to the previous dialog. This can
be useful when you want to correct a choice you made in a previous
dialog.

The Continue button saves the choices you made in that dialog, closes
the dialog, and shows the next dialog.

Making a selection
------------------
Just click on one of the locations to select it. To select multiple
locations, hold Ctrl or Shift while selecting. To select all locations
at once, click on a location and press Ctrl+A.

.. _dialog-spe-selection:

Species Selection dialog
========================

.. figure:: dialog_species_selection.png
   :scale: 100 %
   :alt: Species Selection dialog
   :align: center

   Figure 4. Species Selection dialog

The species selection dialog shows a list of all SETL species that were
found in the selected SETL localities. This dialog allows you to select
the species to be included in the analysis. Only the SETL records that
match both the the locations and species selection will be used for the
analysis.

It is possible to select more than one specie (see `Making a selection`).
Selecting more than one specie in a single species selection dialog
means that the selected species are threated as one specie for the
analysis. However, if the selected analysis requires two or more
separate specie selections (i.e. two species are compared), it will
display the selection dialog multiple times. In this case, the
header of the selection dialog will say "First Species Selection",
"Second Species Selection", etc.

The Back button allows you to go back to the previous dialog. This can
be useful when you want to correct a choice you made in a previous
dialog.

The Continue button saves the choices you made in that dialog, closes
the dialog, and shows the next dialog.

Making a selection
------------------
Just click on one of the species to select it. To select multiple
species, hold Ctrl or Shift while selecting. To select all species
at once, click on a specie and press Ctrl+A.

.. _dialog-change-data-source:

Change Data Source dialog
=========================

.. figure:: dialog_change_data_source.png
   :scale: 100 %
   :alt: Change Data Source dialog
   :align: center

   Figure 5. Change Data Source dialog

The change data source dialog allows you to switch to a different data
source. Two data sources are possible:

* CSV files exported from the Microsoft Access SETL database. The CSV
  files need to be exported by Microsoft Access, one file for each of
  the four tables: SETL_localities, SETL_plates, SETL_records, and
  SETL_species. The section
  :ref:`Exporting CSV Files from the MS Access database <export-csv-msaccess>`
  describes how to export these files.

  After selecting all four CSV files, press the OK button to load all
  SETL data from these files. A progress dialog is shown while the data
  is being loaded. Once the data has been loaded, the
  :ref:`locations selection dialog <dialog-loc-selection>` will be
  updated with the new data.

* The remote SETL database. The remote SETL database has not been
  created yet, so this functionality is not implemented yet. The idea is
  to move the data from the Microsoft Access database to a PostgreSQL
  database.

  This dialog should allow you to enter the information needed to
  connect to the remote database (i.e. the server address and a port number),
  Pressing the OK button should load the localities and species data.
  A progress dialog is shown while the data is being loaded. Once the
  data has been loaded, the
  :ref:`locations selection dialog <dialog-loc-selection>` will be
  updated with the new data.

  The plates and records data will not be loaded directly (in contrast
  to loading data from CSV files). The plates and record data will be
  loaded when required by the analysis.

.. _dialog-define-plate-areas:

Define Plate Areas dialog
=========================

.. figure:: dialog_define_plate_areas.png
   :scale: 100 %
   :alt: Define Plate Areas dialog
   :align: center

   Figure 6. Define Plate Areas dialog

This dialog allows you to define the plate areas for analysis 1
"spot preference". By default, the SETL plate is devided in four plate
areas: A, B, C and D. This dialog allows you to combine specific areas by
changing the areas selection in the dialog. Combining areas means that
the combined areas are treated as a single plate area.

Below is a schematic SETL-plate with a grid. By default the plate is
divided in four plate areas (A, B, C and D),

.. _fig_plate_areas_default:

.. figure:: plate_areas_default.png
   :scale: 100 %
   :alt: Figure 7. Default plate areas
   :align: center

   Figure 7. Default plate areas

But sometimes it's useful to combine plate areas. So if the user decides
to combine area A and B, the areas selection would be set like this,

.. figure:: plate_areas_selection_combined1.png
   :scale: 100 %
   :alt: Figure 8. Combined plate areas selection
   :align: center

   Figure 8. Combined plate areas selection

And the resulting plate areas definition would look something like this,

.. figure:: plate_areas_combined1.png
   :scale: 100 %
   :alt: Figure 9. Plate areas A and B combined.
   :align: center

   Figure 9. Plate areas A and B combined.

This would result in three plate areas. Analysis 1 would then determine
if the selected specie has a preference for either of the three plate
areas.

The names of the plate areas (area 1, area 2, ...) do not have a
special meaning. It is simply used internally by the application to
distinguish between plate areas. These area names are also used in the
analysis report to distinguish between the plate areas.

The Back button allows you to go back to the previous dialog. This can
be useful when you want to correct a choice you made in a previous
dialog.

The Continue button saves the choices you made in the dialog, closes
the dialog, and shows the next dialog.

.. _dialog-analysis-report:

Analysis Report dialog
======================

.. figure:: dialog_analysis_report.png
   :scale: 100 %
   :alt: Analysis Report dialog
   :align: center

   Figure 10. Analysis Report dialog

The analysis report dialog shows the results for the anaylysis. The
report is divided into sub sections. Each sub section is described
below.

The analysis report dialog's toolbar holds three buttons. The Home button
brings you back to the :ref:`select analysis dialog <dialog-analysis-selection>`.

The Save Report button allows you to save the report to a file. Clicking
this button first shows a File Save dialog which allows you to select the
format in which to export the report and the filename. Two formats are
currently supported:

* Plain Text Document - This exports the analysis report to a plain text file.
  This file can be openend with any text editor.

* XML Document - This exports the analysis report along with all analysis data
  to a XML document. The purpose of the XML document is to store all data of
  an analysis. It contains extra data as the arguments used for the statistical
  tests (alpha level, confidence level, etc.) and spot distances.

After pressing the Save button in the File Save dialog, another dialog is shown
which allows you to select the report elements to export. This dialog is not
shown when exporting to a XML document.

The Help button shows the description for the Analysis Report dialog.

Locations and Species Selections
--------------------------------

Displays the locations and species selections. If multiple selections
were made, each element is suffixed by a number. For example "Species
selection (2)" stands for the second species selection.

Spot Distances
--------------

Displays the observed and expected spot distances. How these distances
are calculated is described below.

Observed spot distances (intra)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All possible distances between the spots on each plate are calculated
using the Pythagorean theorem. Consider the case of specie A and the
following plate:

.. figure:: setl_plate_intra_distances.png
   :scale: 100 %
   :alt: Figure 11. Spot distances on SETL plate (intra)
   :align: center

   Figure 11. Spot distances on SETL plate (intra)

As you can see from the figure, three positive spots results in three
spot distances (*a*, *b* and *c*). The distance from one spot to the next
by moving horizontally or vertically is defined as 1. The distances from
the figure are calculated as follows:

| :math:`spot\_distance(a) = \sqrt{3^2 + 2^2} = 3.61`
| :math:`spot\_distance(b) = \sqrt{3^2 + 1^2} = 3.16`
| :math:`spot\_distance(c) = \sqrt{0^2 + 3^2} = 3`

This is done for all possible spot distances on each plate. Note that
there can be no distance 0 (in contrast to inter-specific spot
distances).

Observed spot distances (inter)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First the plate records are collected that contain both of the selected
species. Then all possible spot distances are calculated between the
two species. The following figure shows an example with positive spots
for two species (A and B) and all possible spot distnaces.

.. _fig_spot-distances-inter:

.. figure:: setl_plate_inter_distances.png
   :scale: 100 %
   :alt: Figure 12. Spot distances on SETL plate (inter)
   :align: center

   Figure 12a. Spot distances on SETL plate (inter)

In the above figure, the distances are calculated the same way as for
analysis 2. Note however that only inter-specific distances are
calculated (distances between two different species). This also makes it
possible to have a distance of 0 as visualized in the next figure.

.. _fig_spot-distances-inter2:

.. figure:: setl_plate_inter_distances2.png
   :scale: 100 %
   :alt: Figure 12. Spot distances on SETL plate (inter)
   :align: center

   Figure 12b. Spot distances on SETL plate (inter)

The distances for this figure are calculated as follows:

| :math:`spot\_distance(a) = \sqrt{0^2 + 0^2} = 0`
| :math:`spot\_distance(b) = \sqrt{3^2 + 1^2} = 3.16`
| :math:`spot\_distance(c) = \sqrt{0^2 + 2^2} = 2`

Expected spot distances
^^^^^^^^^^^^^^^^^^^^^^^

The expected spot distances are calculated by generating a copy of
each plate record matching the species selection. Each copy has the
same number of positive spots as its original, except the positive
spots are placed randomly at the plates. Then the spot distances
are calculated the same way as for the observed spot distances. This
means that the resulting list of expected spot distances has the same
length as the observed spot distances.

.. _wilcoxon-test:

Results for Wilcoxon signed-rank test
-------------------------------------

Shows the results for the Wilcoxon signed-rank test.

    "The Wilcoxon signed-rank test is a non-parametric statistical
    hypothesis test for the case of two related samples or repeated
    measurements on a single sample. It can be used as an alternative
    to the paired Student's t-test when the population cannot be assumed
    to be normally distributed." ---
    `Wikipedia - Wilcoxon signed-rank test (obt. 2010/12/22) <http://en.wikipedia.org/wiki/Wilcoxon_test>`_

Tests showed that spot distances on a SETL plate are not normally
distributed (see :ref:`figure 13 <fig_distance_distribution_intra>`
and :ref:`14 <fig_distance_distribution_inter>`), hence the Wilcoxon
test was chosen to test if the observed and expected spot distances
differ significantly.

.. _fig_distance_distribution_intra:

.. figure:: distance_distribution_intra.png
   :scale: 100 %
   :alt: Distribution for intra-specific spot distances
   :align: center

   Figure 13. Distribution for intra-specific spot distances. The
   frequencies were obtained by calculating all possible distances
   between two spots if all 25 spots are covered.
   The same test was done with different numbers of positive spots
   randomly placed on a plate with 100.000 repeats. All
   resulting distributions are very similar to this figure.


.. _fig_distance_distribution_inter:

.. figure:: distance_distribution_inter.png
   :scale: 100 %
   :alt: Distribution for inter-specific spot distances
   :align: center

   Figure 14. Distribution for inter-specific spot distances. The
   frequencies were obtained by calculating all possible distances
   between two spots with ratio 25:25 (specie A and B have all 25 spots
   covered). The same test was done with different positive spots
   ratios (spots randomly placed on a plate, 100.000 repeats). All
   resulting distributions are very similar to this figure.

Depending on the analysis, the records matching the species selection
are first grouped by positive spots number (analysis 2) or by ratios
group (analysis 3). See section :ref:`record grouping <record-grouping>`.

Each row for the results of the Wicoxon test contains the results
of a single test on a spots/ratios group. Each row can have the
following elements:

Positive Spots
    A number representing the number of positive spots. For this test
    only records matching that number of positive spots were used.

Ratios Group
    A number representing the ratios group. For this test
    only records grouped in that ratios group were used.

n (plates)
    The number of plates that match the number of positive spots.

n (distances)
    The number of spot distances derived from the records matching the
    positive spots number.

P-value
    The P-value for the test.

Mean Observed
    The mean of the observed spot distances.

Mean Expected
    The mean of the expected spot distances.

Conf. interval start
    The start of the confidence interval for the test.

Conf. interval end
    The end of the confidence interval for the test.

Remarks
    A summary of the results. Shows whether the p-value is significant,
    and if so, how significant and decides based on the means if the
    species attract (observed mean < expected mean) or repel
    (observed mean > expected mean).

Some spots/ratios groups might me missing from the list of results. This is
because spots/ratios groups that don't have matching records are skipped,
so they are not displayed in the list of results.

Results for Pearson's Chi-squared Test for Count Data
-----------------------------------------------------

Shows the results for Pearson's Chi-squared Test for Count Data.

    "Pearson's chi-square (χ2) test is the
    best-known of several chi-square tests. It tests a null hypothesis
    stating that the frequency distribution of certain events observed
    in a sample is consistent with a particular theoretical distribution."
    --- `Wikipedia - Pearson's Chi-squared Test (obt. 2010/12/22) <http://en.wikipedia.org/wiki/Pearson's_chi-square_test>`_

The observed values are the frequencies of the observed spot distances. The
expected values are calculated with the formula :math:`e(d) = N * p(d)`
where *N* is the total number of observed distances and *p* is the
probability for spot distance *d*. The probability *p* has been
pre-calculated for each spot distance. The probabilities for intra-specific
spot distances are from the model of :ref:`figure 13 <fig_distance_distribution_intra>`
and the probabilities for inter-specific distances are from the model of
:ref:`figure 14 <fig_distance_distribution_inter>`. The probabilities
have been hard coded into the application: ::

    # The probability for each spot distance on a 5x5 SETL plate
    # (intra-specific).
    # Format of the dictionary: {distance: probability, ...}
    SPOT_DIST_TO_PROB_INTRA = {
        1: 40/300.0,
        1.41: 32/300.0,
        2: 30/300.0,
        2.24: 48/300.0,
        2.83: 18/300.0,
        3: 20/300.0,
        3.16: 32/300.0,
        3.61: 24/300.0,
        4: 10/300.0,
        4.12: 16/300.0,
        4.24: 8/300.0,
        4.47: 12/300.0,
        5: 8/300.0,
        5.66: 2/300.0,
        }

    # The probability for each spot distance on a 5x5 SETL plate
    # (inter-specific).
    # Format of the dictionary: {distance: probability, ...}
    SPOT_DIST_TO_PROB_INTER = {
        0: 25/625.0,
        1: 80/625.0,
        1.41: 64/625.0,
        2: 60/625.0,
        2.24: 96/625.0,
        2.83: 36/625.0,
        3: 40/625.0,
        3.16: 64/625.0,
        3.61: 48/625.0,
        4: 20/625.0,
        4.12: 32/625.0,
        4.24: 16/625.0,
        4.47: 24/625.0,
        5: 16/625.0,
        5.66: 4/625.0,
        }

Depending on the analysis, the records matching the species selection
are first grouped by positive spots number (analysis 2) or by ratios
group (analysis 3). See section :ref:`record grouping <record-grouping>`.

Each row for the results of the Chi-squared tests contains the results
of a single test on a spots/ratios group. Each row can have the
following elements:

Positive Spots
    A number representing the number of positive spots. For this test
    only records matching that number of positive spots were used.

Ratios Group
    A number representing the ratios group. For this test
    only records grouped in that ratios group were used.

n (plates)
    The number of plates that match the number of positive spots.

n (distances)
    The number of spot distances derived from the records matching the
    positive spots number.

P-value
    The P-value for the test.

Chi squared
    The value the chi-squared test statistic.

df
    The degrees of freedom of the approximate chi-squared distribution
    of the test statistic.

Mean Observed
    The mean of the observed spot distances.

Mean Expected
    The mean of the expected spot distances.

Remarks
    A summary of the results. Shows whether the p-value is significant,
    and if so, how significant and decides based on the means if the
    species attract (observed mean < expected mean) or repel
    (observed mean > expected mean).

Some spots/ratios groups might me missing from the list of results. This is
because spots/ratios groups that don't have matching records are skipped,
so they are not displayed in the list of results.

Plate Areas Definition
----------------------

Describes the definition of the plate areas set with the
:ref:`define plate areas dialog <dialog-define-plate-areas>`. Read the
description for that dialog to get the meaning of the letters A, B, C
and D.

Species Total per Plate Area
----------------------------

Observed Totals
    How many times the selected specie was found present in each of
    the plate areas.

Expected Totals
    The expected totals for the selected specie.


.. _record-grouping:

Record Grouping
===============

SETLyze performs statistical tests to determine the significance of
results. The key statistical tests used to determine significance are
the Wilcoxon signed-rank test and Pearson's Chi-squared test. The tests
are performed on records data that match the locations and species
selection. It is however not a good idea to just perform the test
on all matching records. For this reason the matching records are first
grouped by a specific property. The tests are then performed on each
group.

Two methods for grouping records have been implemented. One is by positive
spots number, and the other is by positive spots ratio. We'll describe
each grouping method below.


Record grouping by number of positive spots
-------------------------------------------

This type of grouping is done in the case of calculated spot distances
for a single specie (or multiple species grouped together) on SETL
plates (analysis 2).

A record has a maximum of 25 positive spots, so this results in a
maximum of 25 record groups. Group 1 contains records with just one
positive spot, group 2 contains records with two positive spots, et
cetera. Records of group 1 and 25 are left out however. Group 1 is
skipped because it is not possible to calculate spot distances for
records with just one positive spot. And group 25 is excluded because
a significance test on records of this group will always result in a
p-value of 1. This makes sense, because both the observed and expected
distances are based on records with 25 positive spots, which is a full
SETL-plate. As a result, the observed and expected spot distances will
be exactly the same.

The test is also performed on a group with number -24. Of course there
is no such thing as records with minus 24 positive spots. Actually, the
minus sign should be read as "up to". So this test is also performed on
records with up to 24 positive spots. This means that the significance
test will also be performed on records of all groups together. Note
that records of group 1 will still be ignored.

The results of the significance tests are presented in rows. Each row
contains the result of the test for one group. The "Positive Spots"
column tells you to which group each result belongs.

Record grouping by ratios groups
--------------------------------

This type of grouping is done in the case of calculated spot distances
between two different (groups of) species (analysis 3).

When dealing with two species, plate records are matched that contain
both species. This means we can get a ratio for the positive spots for
each matching SETL plate record. Consider :ref:`figure 12 <fig_spot-distances-inter>`
which visualizes a SETL plate with positive spots of species A and B.
There are two positive spots of one specie, and three positive spots of
the other. That makes the ratio for this plate 2:3. The order of the
species doesn't matter here, so a ratio A:B is considered the same as
ratio B:A. All records are grouped based on this ratio. We've defined
five ratios groups:

.. note::

  :math:`c = comb(s)`
    A function for generating a list of two-item combinations with
    replacement *c* from a sequence of numbers *s*. The two-item
    combinations are ratios (e.g. (2,3) = ratio 2:3).

  :math:`s = seq(start,end)`
    A function for creating a sequence of numbers *s* from a number
    range starting with *start* and ending at *end*. For example
    :math:`seq(1,6) = 1,2,3,4,5`

Ratios group 1:
    :math:`comb(seq(1,6))` =
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (2, 2), (2, 3), (2, 4),
    (2, 5), (3, 3), (3, 4), (3, 5), (4, 4), (4, 5), (5, 5)

Ratios group 2:
    :math:`comb(seq(1,11)) - comb(seq(1,6))` =
    (1, 6), (1, 7), (1, 8), (1, 9), (1, 10), (2, 6), (2, 7), (2, 8),
    (2, 9), (2, 10), (3, 6), (3, 7), (3, 8), (3, 9), (3, 10), (4, 6),
    (4, 7), (4, 8), (4, 9), (4, 10), (5, 6), (5, 7), (5, 8), (5, 9),
    (5, 10), (6, 6), (6, 7), (6, 8), (6, 9), (6, 10), (7, 7), (7, 8),
    (7, 9), (7, 10), (8, 8), (8, 9), (8, 10), (9, 9), (9, 10), (10, 10)

Ratios group 3:
    :math:`comb(seq(1,16)) - comb(seq(1,11))` =
    (1, 11), (1, 12), (1, 13), (1, 14), (1, 15), (2, 11), (2, 12),
    (2, 13), (2, 14), (2, 15), (3, 11), (3, 12), (3, 13), (3, 14),
    (3, 15), (4, 11), (4, 12), (4, 13), (4, 14), (4, 15), (5, 11),
    (5, 12), (5, 13), (5, 14), (5, 15), (6, 11), (6, 12), (6, 13),
    (6, 14), (6, 15), (7, 11), (7, 12), (7, 13), (7, 14), (7, 15),
    (8, 11), (8, 12), (8, 13), (8, 14), (8, 15), (9, 11), (9, 12),
    (9, 13), (9, 14), (9, 15), (10, 11), (10, 12), (10, 13), (10, 14),
    (10, 15), (11, 11), (11, 12), (11, 13), (11, 14), (11, 15),
    (12, 12), (12, 13), (12, 14), (12, 15), (13, 13), (13, 14),
    (13, 15), (14, 14), (14, 15), (15, 15)

Ratios group 4:
    :math:`comb(seq(1,21)) - comb(seq(1,16))` =
    (1, 16), (1, 17), (1, 18), (1, 19), (1, 20), (2, 16), (2, 17),
    (2, 18), (2, 19), (2, 20), (3, 16), (3, 17), (3, 18), (3, 19),
    (3, 20), (4, 16), (4, 17), (4, 18), (4, 19), (4, 20), (5, 16),
    (5, 17), (5, 18), (5, 19), (5, 20), (6, 16), (6, 17), (6, 18),
    (6, 19), (6, 20), (7, 16), (7, 17), (7, 18), (7, 19), (7, 20),
    (8, 16), (8, 17), (8, 18), (8, 19), (8, 20), (9, 16), (9, 17),
    (9, 18), (9, 19), (9, 20), (10, 16), (10, 17), (10, 18), (10, 19),
    (10, 20), (11, 16), (11, 17), (11, 18), (11, 19), (11, 20),
    (12, 16), (12, 17), (12, 18), (12, 19), (12, 20), (13, 16),
    (13, 17), (13, 18), (13, 19), (13, 20), (14, 16), (14, 17),
    (14, 18), (14, 19), (14, 20), (15, 16), (15, 17), (15, 18),
    (15, 19), (15, 20), (16, 16), (16, 17), (16, 18), (16, 19),
    (16, 20), (17, 17), (17, 18), (17, 19), (17, 20), (18, 18),
    (18, 19), (18, 20), (19, 19), (19, 20), (20, 20)

Ratios group 5:
    :math:`comb(seq(1,26)) - comb(seq(1,21)) - comb(25)` =
    (1, 21), (1, 22), (1, 23), (1, 24), (1, 25), (2, 21), (2, 22),
    (2, 23), (2, 24), (2, 25), (3, 21), (3, 22), (3, 23), (3, 24),
    (3, 25), (4, 21), (4, 22), (4, 23), (4, 24), (4, 25), (5, 21),
    (5, 22), (5, 23), (5, 24), (5, 25), (6, 21), (6, 22), (6, 23),
    (6, 24), (6, 25), (7, 21), (7, 22), (7, 23), (7, 24), (7, 25),
    (8, 21), (8, 22), (8, 23), (8, 24), (8, 25), (9, 21), (9, 22),
    (9, 23), (9, 24), (9, 25), (10, 21), (10, 22), (10, 23), (10, 24),
    (10, 25), (11, 21), (11, 22), (11, 23), (11, 24), (11, 25),
    (12, 21), (12, 22), (12, 23), (12, 24), (12, 25), (13, 21),
    (13, 22), (13, 23), (13, 24), (13, 25), (14, 21), (14, 22),
    (14, 23), (14, 24), (14, 25), (15, 21), (15, 22), (15, 23),
    (15, 24), (15, 25), (16, 21), (16, 22), (16, 23), (16, 24),
    (16, 25), (17, 21), (17, 22), (17, 23), (17, 24), (17, 25),
    (18, 21), (18, 22), (18, 23), (18, 24), (18, 25), (19, 21),
    (19, 22), (19, 23), (19, 24), (19, 25), (20, 21), (20, 22),
    (20, 23), (20, 24), (20, 25), (21, 21), (21, 22), (21, 23),
    (21, 24), (21, 25), (22, 22), (22, 23), (22, 24), (22, 25),
    (23, 23), (23, 24), (23, 25), (24, 24), (24, 25)

    Ratio 25:25 is removed from this group because the p-value for
    records with that ratio would always be 1.

You can imagine that the results of the statistical test performed on
records from ratios group 1 has a higher reliability than the results
for ratios group 5. Records from ratios group 1 have fewer positive
spots. Finding that specie A is often close to specie B on records of
group 5 doesn't say much. The high number of positive spots naturally
results in spots sitting close to each other. This is however
not the case for records of group 1, where there is enough space for
the species to sit. Finding them next to each other in group 1
probably means something.

The significance test is also performed on ratios group with number -5.
This group includes ratios from all 5 groups (still excluding ratio
25:25).

The results of the significance tests are presented in rows. Each row
contains the result of the test for one group. The "Ratios Group"
column tells you to which group each result belongs.

.. _export-csv-msaccess:

Exporting SETL data to CSV files
################################

This section describes how to export the SETL data from the Microsoft
Access database to CSV files.

1. Open the SETL database file (\*.mdb) in Microsoft Access. You'll
   see four tables in the left column: SETL_localities, SETL_plates,
   SETL_records and SETL_species.

2. To export a table, right-click on it to open the drop menu. From the
   menu select Export > Text file. Then give the filename of the output
   file. Make sure to include the table name in the filename (e.g.
   setl_localities.csv for the "SETL_localities" table). Uncheck all
   other options and press OK.

3. In the next dialog that appears select the option that separates
   fields with a character. The separator character must be a semicolon
   (";"). If it's not, change it by clicking the Advanced button. Then
   click Finish to export the data to a CSV file.

4. Repeat steps 2 and 3 for all tables.

5. You should end up with four files, one CSV file for each table. Put
   these files in one folder.
