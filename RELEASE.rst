Release Steps
=============

#. Create a signed tag::

  git tag -s VERSION

#. Create a Wheel::

  python setup.py bdist_wheel

#. Create a detached signature of the wheel::

  gpg -b dist/*

#. Upload both to pypi Test::

  twine upload --repository-url https://test.pypi.org/legacy/ dist/*

#. Verify the install works from pypi test::

   pip install --index-url https://test.pypi.org/simple/ newsreader

#. Upload the package and signature to pypi prod::

  twine upload dist/*
