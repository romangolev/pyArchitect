# -*- coding: utf-8 -*-
__helpurl__ = ""

import clr
clr.AddReference('System.Windows.Forms')
from pyrevit.forms import WPFWindow
import os.path as op
from System.Windows import MessageBox
from Autodesk.Revit.UI.Selection import ObjectType
from Autodesk.Revit.DB import Transaction, StorageType
import collections
import sys
from core.selectionhelpers import CustomISelectionFilterByIdExclude, ID_MODEL_ELEMENTS
from core.unitsconverter import UnitConverter

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
uiapp = __revit__
app = uiapp.Application
t = Transaction(doc)

try:
    shift_click = __shiftclick__
except NameError:
    shift_click = False



def get_selection():
    selobject = uidoc.Selection.GetElementIds()
    if selobject.Count == 0:
        try:
            selection = uidoc.Selection.PickObjects(ObjectType.Element, CustomISelectionFilterByIdExclude(ID_MODEL_ELEMENTS), "Selection Objects")
        except Exception:
            sys.exit()
    elif selobject.Count != 0:
        selection = selobject
    return selection


class ManageParameters:
    def __init__(self, selection):
        self.selection = selection
        self.inst_params = list()
        self.type_params = list()
        self.collect_parameters()
        self.inst_dict_raw = dict(zip(self.inst_params, range(0, len(self.inst_params), 1)))
        self.type_dict_raw = dict(zip(self.type_params, range(0, len(self.type_params), 1)))
        self.compile_from_params()
        self.compile_to_dictionary()

    def collect_parameters(self):
        for element in self.selection:
            el = doc.GetElement(element)
            eltype = doc.GetElement(el.GetTypeId())
            try:
                params = el.GetOrderedParameters()
                for param in params:
                    self.inst_params.append(param)
            except Exception:
                pass
            try:
                tparams = eltype.GetOrderedParameters()
                for tparam in tparams:
                    self.type_params.append(tparam)
            except Exception:
                pass

    @property
    def select_from_dictionary(self):
        return self.from_dict

    def compile_from_params(self):
        inst_dict = dict()
        for elem in self.inst_dict_raw.items():
            if elem[0].IsShared:
                inst_dict[str(elem[0].Definition.Name) + ' [' + str(elem[0].Definition.Id) + ']'] = elem[1]
            else:
                inst_dict[elem[0].Definition.Name] = elem[1]
        self._inst_dict_names = collections.OrderedDict(inst_dict)

        type_dict = dict()
        for elem in self.type_dict_raw.items():
            if elem[0].IsShared:
                type_dict[str(elem[0].Definition.Name) + ' [' + str(elem[0].Definition.Id) + ']'] = elem[1]
            else:
                type_dict[elem[0].Definition.Name] = elem[1]
        self._type_dict_names = collections.OrderedDict(type_dict)

        from_dict_raw = dict(self._inst_dict_names, **self._type_dict_names)
        self.from_dict = collections.OrderedDict(sorted(from_dict_raw.items()))

    @property
    def select_to_dictionary(self):
        return self.to_dict

    def compile_to_dictionary(self):
        inst_dict = dict()
        for elem in self.inst_dict_raw.items():
            if elem[0].IsReadOnly:
                continue
            if elem[0].IsShared:
                inst_dict[str(elem[0].Definition.Name) + ' [' + str(elem[0].Definition.Id) + ']'] = elem[1]
            else:
                inst_dict[elem[0].Definition.Name] = elem[1]
        to_inst_dict_names = collections.OrderedDict(inst_dict)

        type_dict = dict()
        for elem in self.type_dict_raw.items():
            if elem[0].IsReadOnly:
                continue
            if elem[0].IsShared:
                type_dict[str(elem[0].Definition.Name) + ' [' + str(elem[0].Definition.Id) + ']'] = elem[1]
            else:
                type_dict[elem[0].Definition.Name] = elem[1]
        to_type_dict_names = collections.OrderedDict(type_dict)

        to_dict_raw = dict(to_inst_dict_names, **to_type_dict_names)
        self.to_dict = collections.OrderedDict(sorted(to_dict_raw.items()))

    @property
    def inst_dict_names(self):
        return self._inst_dict_names

    @property
    def type_dict_names(self):
        return self._type_dict_names


class CopyValues:
    def __init__(self, parameter_from, parameter_to, element_from, element_to):
        self.param_from = parameter_from
        self.param_to = parameter_to
        self.element_from = element_from
        self.element_to = element_to
        self.from_value = None

    def getValueFrom(self):
        try:
            if self.param_from.IsShared:
                val = self.element_from.get_Parameter(self.param_from.GUID)
            else:
                val = self.element_from.GetParameters(self.param_from.Definition.Name)[0]
        except Exception:
            return False, False, False

        if val is None:
            return False, False, False

        if self.param_from.StorageType == StorageType.Integer:
            return val.AsInteger(), StorageType.Integer, None
        elif self.param_from.StorageType == StorageType.Double:
            try:
                return val.AsDouble(), StorageType.Double, self.param_from.DisplayUnitType
            except Exception:
                return val.AsDouble(), StorageType.Double, self.param_from.GetUnitTypeId()
        elif self.param_from.StorageType == StorageType.String:
            return val.AsString(), StorageType.String, None
        elif self.param_from.StorageType == StorageType.ElementId:
            return val.AsElementId(), StorageType.ElementId, None
        return False, False, False

    def setValueTo(self, value):
        if self.param_to.IsShared:
            self.element_to.get_Parameter(self.param_to.GUID).Set(value)
        else:
            self.element_to.GetParameters(self.param_to.Definition.Name)[0].Set(value)

    def runLogic(self):
        value, storageTypeFrom, units = self.getValueFrom()
        self.from_value = value
        if storageTypeFrom == StorageType.Integer:
            if self.param_to.StorageType == StorageType.Integer:
                try:
                    self.setValueTo(value)
                    return "Success"
                except Exception:
                    return "Skipped"
            elif self.param_to.StorageType == StorageType.Double:
                try:
                    self.setValueTo(value)
                    return "Success"
                except Exception:
                    return "Skipped"
            elif self.param_to.StorageType == StorageType.String:
                try:
                    self.setValueTo(str(value))
                    return "Success"
                except Exception:
                    return "Skipped"
            elif self.param_to.StorageType == StorageType.ElementId:
                return "Not supported"
        elif storageTypeFrom == StorageType.Double:
            if self.param_to.StorageType == StorageType.Integer:
                try:
                    value_converted = UnitConverter.convertDouble(uiapp, value, units)
                    self.setValueTo(round(value_converted))
                    return "Success"
                except Exception:
                    return "Skipped"
            elif self.param_to.StorageType == StorageType.Double:
                try:
                    value_converted = UnitConverter.convertDouble(uiapp, value, units)
                    self.setValueTo(round(value_converted))
                    return "Success"
                except Exception:
                    return "Skipped"
            elif self.param_to.StorageType == StorageType.String:
                try:
                    value_converted = UnitConverter.convertDouble(uiapp, value, units)
                    self.setValueTo(str(value_converted))
                    return "Success"
                except Exception:
                    return "Skipped"
            elif self.param_to.StorageType == StorageType.ElementId:
                return "Not supported"
        elif storageTypeFrom == StorageType.String:
            if self.param_to.StorageType == StorageType.Integer:
                try:
                    self.setValueTo(int(value))
                    return "Success"
                except Exception:
                    return "Skipped"
            elif self.param_to.StorageType == StorageType.Double:
                try:
                    self.setValueTo(float(value))
                    return "Success"
                except Exception:
                    return "Skipped"
            elif self.param_to.StorageType == StorageType.String:
                try:
                    self.setValueTo(value)
                    return "Success"
                except Exception:
                    return "Skipped"
            elif self.param_to.StorageType == StorageType.ElementId:
                return "Not supported"
        elif storageTypeFrom == StorageType.ElementId:
            if self.param_to.StorageType == StorageType.Integer:
                return "Not supported"
            elif self.param_to.StorageType == StorageType.Double:
                return "Not supported"
            elif self.param_to.StorageType == StorageType.String:
                return "Not supported"
            elif self.param_to.StorageType == StorageType.ElementId:
                try:
                    self.setValueTo(value)
                    return "Success"
                except Exception:
                    return "Skipped"
        return "Skipped"


class MyWindow(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.set_icon(op.join(op.dirname(op.realpath(__file__)), 'icon16.png'))
        self.drop1 = self.FindName('drop1')
        self.drop2 = self.FindName('drop2')
        self.drop1.ItemsSource = paraMan.select_from_dictionary
        self.drop2.ItemsSource = paraMan.select_to_dictionary
        self.resultlist = []
        self.transfer_log = []

    def generate_report(self):
        s = self.resultlist.count("Success")
        sk = self.resultlist.count("Skipped")
        e = self.resultlist.count("Error")
        n = self.resultlist.count("Not supported")
        text1 = "Successfully copied parameter values: " + str(s) + " elements"
        text2 = "\nSkipped copying for: " + str(sk) + " elements"
        text3 = "\nError encounter during copying: " + str(e) + " elements"
        text4 = "\nCopying not supported for: " + str(n) + " elements"
        return text1 + text2 + text3 + text4

    def print_report(self, from_name, to_name):
        print("=== Copy Parameter Values ===")
        print("From: {}  ->  To: {}".format(from_name, to_name))
        print("-" * 60)
        for entry in self.transfer_log:
            el_id, from_param, from_val, to_param, result = entry
            print("  Element {}: {} = {}  ->  {}  [{}]".format(el_id, from_param, from_val, to_param, result))
        print("-" * 60)
        print(self.generate_report())

    def _copy_loop(self, from_parameter, to_parameter, get_from, get_to):
        for elem in selection:
            el_from = get_from(elem)
            el_to = get_to(elem)
            cv = CopyValues(from_parameter, to_parameter, el_from, el_to)
            result = cv.runLogic()
            self.resultlist.append(result)
            self.transfer_log.append((el_to.Id, from_parameter.Definition.Name, cv.from_value, to_parameter.Definition.Name, result))

    def _show_result(self, from_parameter, to_parameter, shift_pressed):
        self.hide()
        if shift_pressed:
            self.print_report(from_parameter.Definition.Name, to_parameter.Definition.Name)
        else:
            MessageBox.Show(self.generate_report(), "Executed")

    def rewrite(self, sender, args):
        selected1 = self.drop1.SelectedItem
        selected2 = self.drop2.SelectedItem
        shift_pressed = shift_click

        t.Start("Copy parameters")
        committed = False
        try:
            if paraMan.type_dict_names.get(selected1) is not None:
                from_parameter = paraMan.type_params[paraMan.type_dict_names.get(selected1)]
                if paraMan.type_dict_names.get(selected2) is not None:
                    to_parameter = paraMan.type_params[paraMan.type_dict_names.get(selected2)]
                    self._copy_loop(from_parameter, to_parameter,
                                    lambda e: doc.GetElement(doc.GetElement(e).GetTypeId()),
                                    lambda e: doc.GetElement(doc.GetElement(e).GetTypeId()))
                    t.Commit()
                    committed = True
                    self._show_result(from_parameter, to_parameter, shift_pressed)
                elif paraMan.inst_dict_names.get(selected2) is not None:
                    to_parameter = paraMan.inst_params[paraMan.inst_dict_names.get(selected2)]
                    self._copy_loop(from_parameter, to_parameter,
                                    lambda e: doc.GetElement(doc.GetElement(e).GetTypeId()),
                                    lambda e: doc.GetElement(e))
                    t.Commit()
                    committed = True
                    self._show_result(from_parameter, to_parameter, shift_pressed)
            elif paraMan.inst_dict_names.get(selected1) is not None:
                from_parameter = paraMan.inst_params[paraMan.inst_dict_names.get(selected1)]
                if paraMan.type_dict_names.get(selected2) is not None:
                    t.RollBack()
                    committed = True
                    self.hide()
                    MessageBox.Show('Cannot write values from Instance parameter to Type parameters of the element', 'Error')
                elif paraMan.inst_dict_names.get(selected2) is not None:
                    to_parameter = paraMan.inst_params[paraMan.inst_dict_names.get(selected2)]
                    self._copy_loop(from_parameter, to_parameter,
                                    lambda e: doc.GetElement(e),
                                    lambda e: doc.GetElement(e))
                    t.Commit()
                    committed = True
                    self._show_result(from_parameter, to_parameter, shift_pressed)
        finally:
            if not committed:
                t.RollBack()


if __name__ == '__main__':
    selection = get_selection()
    paraMan = ManageParameters(selection)
    MyWindow('ui.xaml').ShowDialog()
