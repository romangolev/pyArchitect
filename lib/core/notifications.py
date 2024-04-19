# -*- coding: utf-8 -*-
# by Roman Golev 

import clr
clr.AddReference('AdWindows')
clr.AddReference('System')
clr.AddReference('System.Windows')
clr.AddReference('System.Windows.Forms')
from Autodesk.Internal.InfoCenter import ResultItem
from Autodesk.Windows import ComponentManager
from System import Uri
from System.Windows.Forms import MessageBox


class BalloonNotifier(object):
     """
     Wraps Balloon notification maker
     Instance a class to create a pop-up
     Works without transaction
     See the story behind this class [here](https://jeremytammik.github.io/tbc/a/1114_balloon_tip.htm#3) and [there](https://through-the-interface.typepad.com/through_the_interface/2008/04/the-new-ribbonb.html):

     Basic usage:
     ``` python
          from core.notifications import BalloonNotifier

          notifier = BalloonNotifier()
          notifier.category = "Transaction went well"
          notifier.title = "Well done!"
          notifier.url = ""
          notifier.event = show_report #pass here any function without invoking it
          notifier.isfavourite = False
          notifier.isnew = False
          notifier.add_event()

          notifier.show()
     ```

     Simplified usage:
     ``` python

          BalloonNotifier(category="Operation completed",
                         title="Succesefully changed",
                         url='https://www.google.com/',
                         isnew=False).show()
     ```


     Tips:\n
     * category, title, tooltip are necessary parameters, everything else optional 
     * url opens a webpage while clicking on the balloon of title
     * only one - url or event can work at the same time

     """
     def __init__(self,
                  category='Category',
                  title='Well done!',
                  tooltip='Tooltip',
                  url='https://www.google.com/',
                  isfavourite=True,
                  isnew=True,
                  event=None):
          self.result_item = ResultItem()
          self.category = category
          self.title = title
          self.tooltip = tooltip
          self.isfavourite = isfavourite
          self.isnew = isnew
          self.url = url
          self.event = event
     
     @property
     def category(self):
          return self.result_item.Category
     
     @category.setter
     def category(self, value):
          self.result_item.Category = value

     @property
     def title(self):
          return self.result_item.Title
     
     @title.setter
     def title(self, value):
          self.result_item.Title = value
               
     @property
     def tooltiptext(self):
          return self.result_item.TooltipText
     
     @tooltiptext.setter
     def tooltiptext(self, value):
          self.result_item.TooltipText = value
     
     @property
     def url(self):
          return self.result_item.Uri
     
     @url.setter
     def url(self, value):
          self.result_item.Uri = Uri(value)

     @property
     def is_favourite(self):
          """bool"""
          return self.result_item.IsFavorite
     
     @is_favourite.setter
     def is_favourite(self, value):
          """bool"""
          self.result_item.IsFavorite = value

     @property
     def is_new(self):
          """bool"""
          return self.result_item.IsNew
     
     @is_new.setter
     def is_new(self, value):
          """bool"""
          self.result_item.IsNew = value

     @property
     def event(self):
          """function"""
          return self.result_item.ResultClicked
     
     @event.setter
     def event(self, value):
          """function"""
          if value != None:
               self.result_item.ResultClicked += value

     def show(self):
          """show balloon notification"""
          ComponentManager.InfoCenterPaletteManager.ShowBalloon(self.result_item)

     def test_event(self):
        self.result_item.ResultClicked += self.fire_event

     @staticmethod
     def fire_event(*args):
          MessageBox.Show('Test event has fired up','Event window')