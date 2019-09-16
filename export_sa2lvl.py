def write(context, 
         filepath, *, 
         apply_modifs,
         global_matrix,
         console_debug_output
         ):

     labels["b_col_material"] = 0x00000010
     dummyMat = BASIC.Material() 
     dummyMat.write(tFile)

    return {'FINISHED'}