# SETLyze 0.3

The purpose of SETLyze is to provide the people involved with the SETL project
an easy and fast way of getting useful information from the data stored in the
SETL database. The SETL database at GiMaRIS contains data about the settlement
of species in Dutch waters. SETLyze helps provide more insight in a set of
biological questions by analyzing this data. SETLyze can perform the following
set of analyses:

**Spot Preference**
  Determine a species' preference for a specific location on a SETL plate.
  Species can be combined so that they are treated as a single species.

**Attraction within Species**
  Determine if a species attracts or repels individuals of its own kind.
  Species can be combined so that they are treated as a single species.

**Attraction between Species**
  Determine if two different species attract or repel each other. Species
  can be combined so that they are treated as a single species.

Additionally, any of the above analyses can be performed in batch mode, meaning
that the analysis is repeated for each species of a species selection. Thus
an analysis can be easily performed on an entire data set without intervention.
Batch mode for analyses are parallelized so that the computing power of a
computer is optimally used.


## Documentation

SETLyze's documentation can be found in SETLyze's package folder. Open
`src/setlyze/docs/html/index.html` in your web browser.

## Installation

See the INSTALL file for installation instructions.

## License

The source code for SETLyze is licensed under the GNU General Public License
Version 3, which you can find in the COPYING file.

All graphical assets are licensed under the
[Creative Commons Attribution 3.0 Unported License](http://creativecommons.org/licenses/by/3.0/).
