# -*- coding: UTF-8 -*-
"""
Swap Family Type route
POST /swap_family_type/  - change type of one or more elements to a target family type
"""

from pyrevit import routes
import Autodesk.Revit.DB as DB
from . import logger
import json
import System


def register_swap_family_type_routes(api):

    @api.route('/swap_family_type/', methods=["POST"])
    def swap_family_type(doc, request):
        """
        Change the type of one or more elements to a specified family type.

        Expected request data:
        {
            "element_ids": [123, 456],
            "family_name": "BEEL_DR_Deur",
            "type_name": "900x2100"
        }
        """
        try:
            if not doc:
                return routes.make_response(data={"error": "No active Revit document"}, status=503)

            data = None
            if isinstance(request.data, str):
                try:
                    data = json.loads(request.data)
                except Exception as e:
                    return routes.make_response(
                        data={"error": "Invalid JSON: {}".format(str(e))}, status=400
                    )
            else:
                data = request.data

            if not data or not isinstance(data, dict):
                return routes.make_response(data={"error": "Expected JSON object"}, status=400)

            element_ids = data.get("element_ids", [])
            family_name = data.get("family_name", "").strip()
            type_name = data.get("type_name", "").strip()

            if not element_ids:
                return routes.make_response(data={"error": "element_ids is required"}, status=400)
            if not family_name:
                return routes.make_response(data={"error": "family_name is required"}, status=400)
            if not type_name:
                return routes.make_response(data={"error": "type_name is required"}, status=400)

            # Find the target FamilySymbol
            target_symbol = None
            symbols = DB.FilteredElementCollector(doc).OfClass(DB.FamilySymbol).ToElements()
            for sym in symbols:
                try:
                    fam = getattr(sym, 'Family', None)
                    fam_name = fam.Name if fam else ""
                    tp = sym.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
                    sym_type_name = tp.AsString() if (tp and tp.HasValue) else ""
                    if fam_name.lower() == family_name.lower() and sym_type_name.lower() == type_name.lower():
                        target_symbol = sym
                        break
                except Exception:
                    continue

            if not target_symbol:
                return routes.make_response(
                    data={"error": "Family type not found: {} - {}".format(family_name, type_name)},
                    status=404
                )

            # Activate the symbol if needed
            if not target_symbol.IsActive:
                with DB.Transaction(doc, "Activate Symbol") as t:
                    t.Start()
                    target_symbol.Activate()
                    doc.Regenerate()
                    t.Commit()

            changed = []
            errors = []

            with DB.Transaction(doc, "Swap Family Type") as t:
                t.Start()
                for raw_id in element_ids:
                    try:
                        try:
                            eid = DB.ElementId(System.Int64(int(raw_id)))
                        except TypeError:
                            eid = DB.ElementId(System.Int32(int(raw_id)))

                        elem = doc.GetElement(eid)
                        if not elem:
                            errors.append({"id": raw_id, "error": "Element not found"})
                            continue

                        elem.ChangeTypeId(target_symbol.Id)
                        changed.append(int(raw_id))
                    except Exception as e:
                        errors.append({"id": raw_id, "error": str(e)})
                t.Commit()

            return routes.make_response(data={
                "changed": len(changed),
                "changed_ids": changed,
                "errors": errors,
                "target_family": family_name,
                "target_type": type_name,
            })

        except Exception as e:
            logger.error("Error in swap_family_type: {}".format(str(e)))
            return routes.make_response(data={"error": str(e)}, status=500)

    logger.info("Swap family type routes registered successfully")
