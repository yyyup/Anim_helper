import bpy

# Change the active area to Graph Editor
original_area_type = bpy.context.area.type
bpy.context.area.type = 'GRAPH_EDITOR'

# Decimate F-Curves with a 75% ratio
bpy.ops.graph.decimate(mode='RATIO', factor=0.75)

# Restore the original area type
bpy.context.area.type = original_area_type
