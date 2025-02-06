# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

import traceback
from tools.finishing import FinishingTool

if __name__ == '__main__':
    try:
        tool_instance = FinishingTool(__revit__) # type: ignore
        tool_instance.create_floors()
    except Exception as e:
        print(traceback.format_exc()) 