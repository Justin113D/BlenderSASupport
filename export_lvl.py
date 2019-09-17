def write(context, 
         filepath, *, 
         apply_modifs,
         global_matrix,
         console_debug_output
         ):

    from . import format_BASIC, format_GC

    labels["b_col_material"] = 0x00000010
    dummyMat = format_BASIC.Material() 
    dummyMat.write(tFile)

    return {'FINISHED'}