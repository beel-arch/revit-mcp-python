from Autodesk.Revit.DB import *

level_parameter_mapping = {
    "Rooms": "Level",
    "Walls": "Base Constraint",
    "Doors": "Level",
    "Windows": "Level",
    "Floors": "Level",
    "Ceilings": "Level",
    "Roofs": "Level",
    "Curtain Panels": "Level",
    "Curtain Wall Mullions": "Level",
    "Railings": "Host Level",
    "Stairs": "Base Level",
    "Structural Columns": "Base Level",
    "Structural Framing": "Reference Level",
    "Structural Foundations": "Level",
    "Generic Models": "Level",
    "Furniture": "Level",
    "Furniture Systems": "Level",
    "Mechanical Equipment": "Level",
    "Plumbing Fixtures": "Level",
    "Electrical Equipment": "Level",
    "Electrical Fixtures": "Level",
    "Lighting Fixtures": "Level",
    "Casework": "Level",
    "Specialty Equipment": "Level",
    "Site": "nvt",  # Site elements usually don't have a level
    "Topography": "nvt",  # Topography has no level parameter
    "Columns": "Base Level",
    "Ducts": "Reference Level",
    "Pipes": "Reference Level",
    "Sprinklers": "Reference Level",
    "Grids": "nvt",  # Grids do not belong to a specific level
    "Levels": "nvt",  # Levels themselves do not have a level parameter
    "Detail Items": "nvt",  # 2D elements do not have levels
    "Gutters": "Host Level"
}
