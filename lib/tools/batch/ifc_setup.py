# -*- coding: utf-8 -*-
"""Load Revit IFC setups with Autodesk's own configuration converter.

The configuration's UpdateOptions applies settings that vary between IFC
exporter releases, including property set templates in Revit 2026.
Mapping JSON keys to IFCExportOptions by hand would lose those settings.
"""

import os

import clr
import System

from System import Activator, AppDomain, Array
from System.IO import File
from System.Diagnostics import Process
from System.Reflection import Assembly, BindingFlags


CONFIGURATION_NAMES = (
    "BIM.IFC.Export.UI.IFCExportConfiguration",
    "Revit.IFC.Export.Utility.IFCExportConfiguration",
)
COMMAND_APPLICATION_NAME = "BIM.IFC.Export.UI.IFCCommandOverrideApplication"
OPTIONS_UTIL_NAME = "Revit.IFC.Common.Utility.OptionsUtil"


class IfcSetupError(Exception):
    pass


def _loaded_type(type_name):
    fallback = None
    for assembly in AppDomain.CurrentDomain.GetAssemblies():
        try:
            if assembly.IsDynamic:
                continue
            found = assembly.GetType(type_name, False)
            if found is not None:
                if assembly.GetName().Name == "IFCExporterUIOverride":
                    return found
                fallback = found
        except Exception:
            continue
    return fallback


def _configuration_type_in(assembly):
    for name in CONFIGURATION_NAMES:
        found = assembly.GetType(name, False)
        if found is not None:
            return found
    return None


def find_configuration_type(version_number):
    for name in CONFIGURATION_NAMES:
        configuration_type = _loaded_type(name)
        if configuration_type is not None:
            return configuration_type

    version = str(version_number)
    candidates = []
    for variable in ("PROGRAMDATA", "APPDATA"):
        root = os.environ.get(variable)
        if root:
            candidates.append(os.path.join(
                root, "Autodesk", "ApplicationPlugins",
                "IFC {}.bundle".format(version), "Contents", version,
                "IFCExporterUIOverride.dll",
            ))
    process = Process.GetCurrentProcess()
    try:
        install_folder = os.path.dirname(process.MainModule.FileName)
    finally:
        process.Dispose()
    candidates.append(os.path.join(
        install_folder, "AddIns", "IFCExporterUI", "Autodesk.IFC.Export.UI.dll"
    ))
    candidates.append(os.path.join(install_folder, "Revit.IFC.Export.dll"))
    load_errors = []
    for path in candidates:
        if not File.Exists(path):
            continue
        try:
            assembly = Assembly.LoadFrom(path)
        except Exception as ex:
            load_errors.append("{}: {}".format(path, ex))
            continue
        configuration_type = _configuration_type_in(assembly)
        if configuration_type is not None:
            return configuration_type
        load_errors.append(
            "Autodesk IFC assembly has no IFCExportConfiguration: {}".format(path)
        )
        continue

    if load_errors:
        raise IfcSetupError(
            "Cannot load Autodesk IFC UI assembly for Revit {}: {}".format(
                version, "; ".join(load_errors)
            )
        )
    raise IfcSetupError(
        "Autodesk IFC export UI assembly was not found for Revit {}".format(version)
    )


def load_setup(path, version_number):
    try:
        text = File.ReadAllText(path)
        configuration_type = find_configuration_type(version_number)
        converter_type = configuration_type.Assembly.GetType(
            configuration_type.FullName + "Converter", False
        )
        if converter_type is None:
            raise IfcSetupError("Autodesk IFC configuration converter is unavailable")
        converter = Activator.CreateInstance(converter_type)
        base_type = converter_type.BaseType
        converters = Array.CreateInstance(base_type, 1)
        converters.SetValue(converter, 0)

        if base_type.FullName == "System.Web.Script.Serialization.JavaScriptConverter":
            clr.AddReference("System.Web.Extensions")
            serializer_type = base_type.Assembly.GetType(
                "System.Web.Script.Serialization.JavaScriptSerializer", True
            )
            serializer = Activator.CreateInstance(serializer_type)
            serializer_type.GetMethod("RegisterConverters").Invoke(
                serializer, Array[object]([converters])
            )
            for method in serializer_type.GetMethods():
                if method.Name == "Deserialize" and method.IsGenericMethodDefinition:
                    if len(method.GetParameters()) == 1:
                        configuration = method.MakeGenericMethod(
                            Array[System.Type]([configuration_type])
                        ).Invoke(serializer, Array[object]([text]))
                        break
            else:
                raise IfcSetupError("JavaScriptSerializer.Deserialize is unavailable")
        elif base_type.FullName == "Newtonsoft.Json.JsonConverter":
            serializer_type = base_type.Assembly.GetType(
                "Newtonsoft.Json.JsonConvert", True
            )
            for method in serializer_type.GetMethods():
                if method.Name != "DeserializeObject" or not method.IsGenericMethodDefinition:
                    continue
                parameters = method.GetParameters()
                if len(parameters) != 2 or parameters[0].ParameterType != System.String:
                    continue
                if parameters[1].ParameterType != converters.GetType():
                    continue
                configuration = method.MakeGenericMethod(
                    Array[System.Type]([configuration_type])
                ).Invoke(None, Array[object]([text, converters]))
                break
            else:
                raise IfcSetupError("JsonConvert.DeserializeObject is unavailable")
        else:
            raise IfcSetupError(
                "Unsupported Autodesk IFC converter: {}".format(base_type.FullName)
            )

        if configuration is None:
            raise IfcSetupError("IFC setup file contains no configuration: {}".format(path))
        return configuration
    except IfcSetupError:
        raise
    except Exception as ex:
        raise IfcSetupError("'{}': {}".format(path, ex))


def _new_parameter_mapping_enabled():
    options_util = _loaded_type(OPTIONS_UTIL_NAME)
    if options_util is None:
        options_util = Assembly.Load("Revit.IFC.Common").GetType(
            OPTIONS_UTIL_NAME, False
        )
    method = None
    if options_util is not None:
        method = options_util.GetMethod("UseLegacyParameterMapping")
    if method is None:
        raise IfcSetupError("Autodesk IFC OptionsUtil.UseLegacyParameterMapping is unavailable")
    return not method.Invoke(None, None)


def _takes_document(configuration):
    for method in configuration.GetType().GetMethods():
        if method.Name == "UpdateOptions" and len(method.GetParameters()) == 4:
            return True
    return False


def apply_setup(configuration, options, view_id, document):
    if _takes_document(configuration):
        configuration.UpdateOptions(
            document, options, view_id, _new_parameter_mapping_enabled()
        )
        return

    application_type = configuration.GetType().Assembly.GetType(
        COMMAND_APPLICATION_NAME, False
    )
    document_property = None
    if application_type is not None:
        document_property = application_type.GetProperty(
            "TheDocument", BindingFlags.Public | BindingFlags.Static
        )
    getter = document_property.GetGetMethod() if document_property is not None else None
    setter = document_property.GetSetMethod() if document_property is not None else None
    if getter is None or setter is None or not getter.IsStatic or not setter.IsStatic:
        raise IfcSetupError(
            "Autodesk IFC UI requires a public static read/write TheDocument property"
        )

    previous_document = document_property.GetValue(None, None)
    # Set before entering try: a failed setter must not be retried in finally.
    document_property.SetValue(None, document, None)
    try:
        # The exporter reads the document from the export dialog's static state.
        configuration.UpdateOptions(options, view_id)
    finally:
        document_property.SetValue(None, previous_document, None)
