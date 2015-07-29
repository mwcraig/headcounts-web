headcounts
**********

headcounts is a simple web app for displaying (reasonably) up-to-date
enrollments in courses at `Minnesota State University Moorhead`_ for the
current semester. You can check it out here:
`http://headcounts.herokuapp.com <http://headcounts.herokuapp.com>`_.
It is `deployed on heroku`_ but is based on the `anaconda
python distribution`_  and `conda`, which doesn't use ``virtualenv``. The
magic to make this work is the `conda buildpack for heroku by Kenneth Reitz`_ (thanks
@kennethreitz).


.. _Minnesota State University Moorhead: http://www.mnstate.edu
.. _deployed on heroku: http://headcounts.herokuapp.com
.. _anaconda python distribution: https://store.continuum.io/cshop/anaconda/
.. _conda buildpack for heroku by Kenneth Reitz: https://github.com/kennethreitz/conda-buildpack
