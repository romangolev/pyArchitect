# -*- coding: utf-8 -*-
"""Locale-aware strings for pyArchitect, driven by pyRevit's own language.

pyRevit already resolves a language for every user: ``user_locale`` in the
pyRevit settings, which is what picks the ``en_us`` / ``ru`` / ``es_es`` entry
of a bundle's ``title`` and ``tooltip``, and what picks the
``*.ResourceDictionary.<locale>.xaml`` a form is merged with.  This module
reads the same setting through :func:`pyrevit.coreutils.applocales.get_locale_string`
so a command's Python strings can never disagree with the ribbon button that
started it or with the XAML of the window it opens.

Strings live in catalogs next to the feature that shows them: a dict of keys,
each holding one dict of locale code to text.  Wrap the catalog in a
:class:`StringTable` and call it::

    S = StringTable({"run.done": {"en_us": "Done", "ru": u"Готово"}})
    S("run.done")

English is the default and the only required locale: a key with no entry for
the active language falls back to ``en_us``, and an unknown key returns itself
rather than raising, so a missing translation can never break a batch run.
"""

from pyrevit.coreutils import applocales


DEFAULT_LOCALE = "en_us"

SUPPORTED_LOCALES = ("en_us", "ru", "es_es")


def localize(variants):
    """Return the variant for pyRevit's language, or the English one.

    Args:
        variants (dict[str, str]): locale code to text.

    Returns:
        (str): text in the active locale.
    """
    try:
        text = applocales.get_locale_string(variants)
    except Exception:
        text = None
    if text is None:
        text = variants.get(DEFAULT_LOCALE, "")
    return text


class StringTable(object):
    """A catalog of localized strings, resolved once per session.

    Args:
        catalog (dict[str, dict[str, str]]): message key to locale variants.
    """

    def __init__(self, catalog):
        self._catalog = catalog
        self._resolved = {}

    def __call__(self, key, *args, **kwargs):
        """Return the localized string for `key`, formatted with any arguments."""
        text = self._resolved.get(key)
        if text is None:
            variants = self._catalog.get(key)
            text = key if variants is None else localize(variants)
            self._resolved[key] = text
        if args or kwargs:
            return text.format(*args, **kwargs)
        return text

    def keys(self):
        """Return every message key in the catalog."""
        return self._catalog.keys()
