# -*- coding: UTF-8 -*-
from pyrevit import routes, DB
import logging
logger = logging.getLogger(__name__)

def register_door_routes(api):
    @api.route('/doors/allparams/', methods=["GET"])
    def door_all_params(doc, request=None):
        """
        Haalt ALLE parameters op van alle deuren in het model.
        """
        try:
            doors_data = []
            collector = DB.FilteredElementCollector(doc)\
                          .OfCategory(DB.BuiltInCategory.OST_Doors)\
                          .WhereElementIsNotElementType()

            for door in collector:
                # Type name
                type_elem = doc.GetElement(door.GetTypeId())
                type_name_param = type_elem.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
                type_name = type_name_param.AsString() if type_name_param else ""

                # Alle parameters uitlezen
                param_dict = {}
                for p in door.Parameters:
                    try:
                        name = p.Definition.Name
                        if p.StorageType == DB.StorageType.String:
                            value = p.AsString()
                        elif p.StorageType == DB.StorageType.Double:
                            value = p.AsDouble()  # raw feet, kan ook naar meters
                        elif p.StorageType == DB.StorageType.Integer:
                            value = p.AsInteger()
                        elif p.StorageType == DB.StorageType.ElementId:
                            eid = p.AsElementId()
                            value = str(eid.IntegerValue)
                        else:
                            value = p.AsValueString()
                        param_dict[name] = value
                    except Exception as e:
                        param_dict[name] = "Error: {}".format(e)

                doors_data.append({
                    "DoorTypeName": type_name,
                    "parameters": param_dict
                })

            return routes.make_response(data=doors_data)

        except Exception as e:
            logger.error("door_all_params failed: %s", e)
            return routes.make_response(data={"error": str(e)}, status=500)
