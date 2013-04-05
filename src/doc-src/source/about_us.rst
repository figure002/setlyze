========
About Us
========

The following people have been involved in the SETLyze project.

Arjan Gittenberger
------------------

Project leader and contact (info@gimaris.com) at GiMaRIS.

Jonathan den Boer
-----------------

Internship bioinformatics (Leiden University of Applied Science) student at
GiMaRIS. Responsible for the intial development of the application (then
called "Sesprere").

* Implemented analysis "Spot preference".
* Documentation (user manual, programmer's manual and technical design).

Serrano Pereira
---------------

Internship bioinformatics (Leiden University of Applied Science) student at
GiMaRIS (September to November 2010).

* Optimization of the overall application (renamed "SETLyze").
* Moved from Tkinter to GTK+ for creating the graphical user interfaces.
* Optimization of analysis "Spot preference"
* Implementation of analysis "Attraction within species" and
  analysis "Attraction between species".
* Sphinx documentation (user manual, developer guide).
* Technical design.
* Distribution packages (source package, Windows installer).

Continued work on SETLyze in January 2013:

* Code repository moved from Bazaar to Git.
* Implementation of batch mode for analyses "Spot preference", "Attraction
  within species" and "Attraction between species". This has been parallelized
  with the multiprocessing module from Python's standard library.
* Overall optimization of the code.
* Dropped the XML report exporter in favor of an improved reStructuredText
  report exporter.
* Use a configuration file to save user preferences.
* Release of version 1.0 in April 2013.

Adam van Adrichem and Fedde Schaeffer
-------------------------------------

Minor project / internship bioinformatics (Leiden University of Applied
Science) students at GiMaRIS.

* Reorganised the Bazaar repositories to be easier to copy, develop and track.
* Implemented the cancel button in the progress bar of the analyses.
* Implemented the possibility of reading Microsoft Office Excel 97–2004
  workbooks.
* Tried to make a start making the technical design match the actual
  implementation.
* Looked into how the repetitions of Wilcoxon tests could be parallelised
  using the multiprocessing module from Python’s standard library.
* Looked into how an analysis could be executed serially for all species in
  the database, to find out which species should be investigated more.
* Release of version 0.2.
