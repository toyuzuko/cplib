"""Geometry package.

``integer`` (integer coordinates), ``rational`` (rational coordinates), and
``floating`` (floating-point coordinates) are intentionally separate modules
and must be imported explicitly, e.g.::

    from cplib.geometry.integer import Point

This package does not re-export their contents because these modules
provide same-named classes with different representations.
"""
