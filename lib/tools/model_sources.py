# -*- coding: utf-8 -*-

from tools.local_models import LocalModelFinder
from tools.rsn import RsnModelListReader


class ModelSourceResolver(object):
    """Selects the appropriate model source for a batch request."""

    def resolve(self, settings):
        source = settings.get("source", "LOCAL").upper()

        if source == "LOCAL":
            return LocalModelFinder().find(settings)

        if source == "RSN":
            return RsnModelListReader().parse(settings.get("server_models", ""))

        return []
