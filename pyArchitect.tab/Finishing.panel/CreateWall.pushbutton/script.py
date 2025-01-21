# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

import traceback
from tools.finishing import FinishingTool

if __name__ == '__main__':
    try:
        tool_instance = FinishingTool(__revit__)
        tool_instance.create_walls()
    except Exception as e:
        print(traceback.format_exc())