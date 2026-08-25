# -*- coding: utf-8 -*-
"""Entry point reserved for the batch Navisworks exporter.

The exporter will use the shared batch Navis service once the existing view
creation library has been extracted. Keeping this command separate makes the
two workflows discoverable without creating a second copy of that logic.
"""

from Autodesk.Revit.UI import TaskDialog


TaskDialog.Show(
    "Export Navisworks",
    "Batch Navisworks export is being wired to the shared batch library.\n\n"
    "Use Navisworks Views to prepare model views in the meantime."
)
