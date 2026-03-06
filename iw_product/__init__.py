"""
iw_product — ImageWall Product GH Definition in Python
Complete replacement for IW-Product-v1.3.5.gh (3,212 components)

Modules:
    config_loader       - Excel import + all project settings
    grid_params         - Derived grid parameters + gate indices
    uniform_grid        - Uniform panel grid geometry
    nonuniform_grid     - Variable-width panel grid
    panel_faces         - Panel face dimensions, joints, corners
    diagonal_grid       - 45-degree rotated grid patterns
    point_grid          - Perforation point grid generation
    die_selection       - Punch die size selection
    imagelines          - Image-mapped perforation patterns
    image_processor     - Image loading, blur, threshold, brightness
    fastener_clearance  - Remove perfs near fasteners
    fastener_geometry   - Fastener hole curves + connection sorting
    collision_check     - StayOutside perf-to-edge collision
    rule_zone           - Restricted perforation zones
    panel_unfold        - Flat pattern unfolding
    brake_legs          - Brake legs + corner notching
    drop_locks          - Drop lock block placement
    panel_naming        - Panel names + CNC rotation
    inner_corners       - Inner corner special conditions
    cross_seam          - Cross-seam joint variations
    structural_members  - Sticks, hooks, mullion geometry
    scribe              - Scribe/engraving marks
    image_resolution    - Render resolution calculation
    file_path_builder   - Output file path construction
    perf_image_renderer - Raster image rendering
    submittal_maker     - Submittal documentation data
    excel_writer        - Write data back to Excel
    bake_geometry       - Bake to Rhino with layers
    layout_manager      - Rhino layout pages + index sheets
    dxf_export          - DXF export for CNC
    nesting             - Sheet nesting optimization
    multi_scope         - Multiple scope support
    group_visibility    - Rhino group on/off control
    shared              - Inter-component data storage
"""

__version__ = "0.2.0"
