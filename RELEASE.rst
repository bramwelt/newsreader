Release Steps
=============

#. Create a signed tag::

  git tag -s VERSION

#. Create a Source Distribution::

  python setup.py sdist

#. Create a Wheel::

  python setup.py bdist_wheel

#. Create a detached signature of the wheel and sdist::

  for relfile in dist/*; do gpg -a --detach-sign $relfile; done

#. Upload both to pypi Test::

  twine upload --repository-url https://test.pypi.org/legacy/ dist/*

#. Verify the install works on both from pypi test::

  pip install --extra-index-url https://test.pypi.org/simple/ --only-binary wheel --no-cache-dir newsreader
  pip install --extra-index-url https://test.pypi.org/simple/ --no-cache-dir --no-binary newsreader newsreader

#. Upload the package and signature to pypi prod::

  twine upload dist/*
