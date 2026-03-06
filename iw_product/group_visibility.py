"""
Module: Group Visibility
==========================
Controls Rhino layer and group visibility based on project state.
Handles the on/off color coding of groups.

Replaces: Enable/Disable Object, Set Group Properties,
Get Objects in Group components.

Usage:
    from iw_product.group_visibility import update_group_visibility
"""

try:
    import Rhino
    import Rhino.Geometry as rg
    import Rhino.DocObjects as rd
    import scriptcontext as sc
    import System.Drawing as SD
    HAS_RHINO = True
except ImportError:
    HAS_RHINO = False


def update_group_visibility(config, grid_params):
    """
    Update Rhino group visibility and colors based on current style and state.

    Args:
        config: dict from config_loader
        grid_params: dict from grid_params

    Returns:
        dict with groups_updated count
    """
    if not HAS_RHINO:
        return {"groups_updated": 0}

    doc = Rhino.RhinoDoc.ActiveDoc
    if not doc:
        return {"groups_updated": 0}

    style_index = grid_params["style_index"]
    on_color = SD.Color.FromArgb(0, 200, 0)    # green = active
    off_color = SD.Color.FromArgb(200, 0, 0)   # red = inactive

    # Group name patterns and which styles they apply to
    # This maps GH group toggle logic
    group_rules = {
        "Double Return": lambda si: si in (0, 1, 2, 3),
        "Droplock": lambda si: si in (4, 5),
        "Flat": lambda si: si in (6, 7),
        "Long Span": lambda si: si in (0, 1),
        "Short Span": lambda si: si in (2, 3),
    }

    updated = 0
    group_table = doc.Groups
    for i in range(group_table.Count):
        group = group_table.GroupAt(i)
        if group is None:
            continue
        group_name = group.Name or ""

        for pattern, check_fn in group_rules.items():
            if pattern.lower() in group_name.lower():
                is_active = check_fn(style_index)
                # Get objects in group
                member_ids = doc.Groups.GroupMembers(i)
                if member_ids:
                    for obj_id in member_ids:
                        obj = doc.Objects.FindId(obj_id)
                        if obj:
                            attrs = obj.Attributes.Duplicate()
                            attrs.Visible = is_active
                            doc.Objects.ModifyAttributes(obj, attrs, True)
                updated += 1
                break

    doc.Views.Redraw()
    return {"groups_updated": updated}
