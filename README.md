# BlenderSA2Support
An addon for Blender 2.8, which adds exporting options for .sa1mdl, .sa2bmdl, and .sa2blvl, so that entire SA1/2 stages can be created inside Blender without needing external stage editors!
so far only the sa1mdl exporter is working

How to install:
  1. download the repo as a zip
  2. open blender 2.8, open the preferences and go to the addon tab
  3. hit install in the top right
  4. navigate to the zip, then select it
  5. if the addon didnt appear in the addon list, look up "SA2 Model formats support"
  6. enable the addon
  7. Enjoy!

Usage Guide:

Material editor:
  Each material will now have an "SA Material Properties" menu, in which you can edit the material properties for the corresponding formats. Hovering above a property will display a description. (material previewing in blender not possible yet)
 
Author and description:
  In the scene tab of the properties panel, the menu "SA file menu" has been added, which holds the Author and Description, which will be written into the file at export
 
How to export:
  when ready, you can export through the export menu, in which there is a sub menu called "SA formats", which hosts all of the exportable formats. select one to export the scene
