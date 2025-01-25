import Autodesk.Revit.DB as DB

class WarningSuppressor(DB.IFailuresPreprocessor):
     def PreprocessFailures(self, failuresAccessor):
          for failure in failuresAccessor.GetFailureMessages():
               failure_severity = failure.GetSeverity()
               # Check the severity of a warning and delete it
               if failure_severity == DB.FailureSeverity.Warning:
                    failuresAccessor.DeleteWarning(failure)
          return DB.FailureProcessingResult.Continue