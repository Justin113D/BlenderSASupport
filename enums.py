from enum import Enum
from flags import Flag

# General File Enums and Flags

class MDLFormatIndicator(Enum):
    """Format indicators for the model file"""
    SA1MDL = 0x00004C444D314153
    SA2MDL = 0x00004C444D324153
    SA2BMDL = 0x004C444D42324153

class LVLFormatIndicator(Enum):
    """Format indicators for the level file"""
    SA1LVL = 0x00004C564C314153
    SA2LVL = 0x00004C564C324153
    SA2BLVL = 0x004C564C42324153

class Chuntypes(Enum):
    """Meta Data type"""
    Label = 0x4C42414C # LABl
    Animation = 0x4C42414C # ANIM
    Morph = 0x46524F4D # MORF
    Author = 0x48545541 # AUTH
    Tool = 0x4C4F4F54 # TOOL
    Description = 0x43534544 # DESC
    Texture = 0x00584554 # TEX
    End = 0x00444E45 # END

class ObjectFlags(Flag):
    """Object flags used in models"""
    NoPosition = 0x01
    NoRotate = 0x02
    NoScale = 0x04
    NoDisplay = 0x08
    NoChildren = 0x10
    RotateZYX = 0x20
    NoAnimate = 0x40
    NoMorph = 0x80

class SurfaceFlags(Flag):
    """Surface interaction Flags for landtable COL"""
    Solid = 0x01
    Water = 0x02
    Visible = 0x80000000

# GC format Enums and Flags

class VertexAttribute(Enum):
    """Type of Vertex Attribute"""
    PositionMatrixID = 0
    Position = 1
    Normal = 2
    Color0 = 3
    Color1 = 4
    Tex0 = 5
    Tex1 = 6
    Tex2 = 7
    Tex3 = 8
    Tex4 = 9
    Tex5 = 10
    Tex6 = 11
    Tex7 = 12
    Null = 13

class DataType(Enum):
    """Type in which the attibute data gets saved"""
    Unsigned8 = 0
    Signed8 = 1
    Unsigned16 = 2
    Signed16 = 3
    Float32 = 4
    RGB565 = 5
    RGB8 = 6
    RGBX8 = 7
    RGBA4 = 8
    RGBA6 = 9
    RGBA8 = 10

class ComponentCount(Enum):
    """The amount and arranged of values in an attribute entry"""
    Position_XY = 0
    Position_XYZ = 1
    Normal_XYZ = 2
    Normal_NBT = 3
    Normal_NBT3 = 4
    Color_RGB = 5
    Color_RGBA = 6
    TexCoord_S = 7
    TexCoord_ST = 8

class ParameterType(Enum):
    """Type of Mesh Parameter"""
    VtxAttrFmt = 0
    IndexAttributeFlags = 1
    Lighting = 2
    BlendAlpha = 4
    AmbientColor = 5
    Texture = 8
    Unknown_9 = 9
    TexCoordGen = 10

class IndexAttributeFlags(Flag):
    """Flags for Index arrays in the mesh"""
    Bit0 = 0x01 # unused
    Bit1 = 0x02 # unused
    Position16BitIndex = 0x04
    HasPosition = 0x08
    Normal16BitIndex = 0x10
    HasNormal = 0x20
    Color16BitIndex = 0x40
    HasColor = 0x80
    Bit8 = 0x0100 # unused
    Bit9 = 0x0200 # unused
    UV16BitIndex = 0x0400
    HasUV = 0x0800
    Bit12 = 0x1000 # unused
    Bit13 = 0x2000 # unused
    Bit14 = 0x4000 # unused
    Bit15 = 0x8000 # unused

class AlphaInstruction(Enum):
    """The way in which the alpha of a texture should be handled when rendering"""
    Zero = 0
    One = 1
    SrcColor = 2
    InverseSrcColor = 3
    SrcAlpha = 4
    InverseSrcAlpha = 5
    DstAlpha = 6
    InverseDstAlpha = 7

class TileMode(Flag):
    """Tiling of Meshes' UVs"""
    WrapU = 0x01
    MirrorU = 0x02
    WrapV = 0x04
    MirrorV = 0x05
    unknown = 0x10

# to understand the next enums:
# http://tp.docs.aecx.cc/Dolphin+OS+Manual/gfx/gx/Geometry/GXSetTexCoordGen2.html

class TexCoordID(Enum):
    """Indicates which uv map of the mesh to use"""
    TexCoord0 = 0
    TexCoord1 = 1
    TexCoord2 = 2
    TexCoord3 = 3
    TexCoord4 = 4
    TexCoord5 = 5
    TexCoord6 = 6
    TexCoord7 = 7
    TexCoordMax = 8 # last uv map?
    TexCoordNull = 9

class TexGenType(Enum):
    """Function used to generate a texture coordinate"""
    # Source attribute multiplied with matrix (see matrixID)
    Matrix3x4 = 0
    Matrix2x4 = 1
    # Emboss style bump texture coordinate
    Bump0 = 2
    Bump1 = 3
    Bump2 = 4
    Bump3 = 5
    Bump4 = 6
    Bump5 = 7
    Bump6 = 8
    Bump7 = 9
    # Red/Green channels from texture as uv
    SRTG = 10

class TexGenSrc(Enum):
    """Which values of the mesh should be used for generating the texture coordinates"""
    Position = 0
    Normal = 1
    Binormal = 2
    Tangent = 3
    Tex0 = 4
    Tex1 = 5
    Tex2 = 6
    Tex3 = 7
    Tex4 = 8
    Tex5 = 9
    Tex6 = 10
    Tex7 = 11
    TexCoord0 = 12
    TexCoord1 = 13
    TexCoord2 = 14
    TexCoord3 = 15
    TexCoord4 = 16
    TexCoord5 = 17
    TexCoord6 = 18
    Color0 = 19
    Color1 = 20

class TexGenMtx(Enum):
    """Which matrix to use for generated texture coordinates"""
    Matrix0 = 30
    Matrix1 = 33
    Matrix2 = 36
    Matrix3 = 39
    Matrix4 = 42
    Matrix5 = 45
    Matrix6 = 48
    Matrix7 = 51
    Matrix8 = 54
    Matrix9 = 57
    Identity = 60

class PrimitiveType(Enum):
    """Determines the arrangement of poly indices"""
    Triangles = 144
    TriangleStrip = 152
    TriangleFan = 160
    Lines = 168
    LineStrip = 176
    Points = 184

# BASIC format Enums and Flags

class MaterialFlags(Flag):
    """BASIC format material flags"""
    # unused or unknown
    Bit0 = 0x01
    Bit1 = 0x02
    Bit2 = 0x04
    Bit4 = 0x08
    Bit5 = 0x10
    Bit6 = 0x20
    # Editor thing - irrelevant
    FLAG_PICK = 0x40
    # Mipmap distance multipler
    # (can be added together, max number is 3.75)
    D_025 = 0x80
    D_050 = 0x0100
    D_100 = 0x0200
    D_200 = 0x0400
    # Texture Filtering
    FLAG_USE_ANISOTROPIC = 0x0800
    FILTER_BILINEAR = 0x1000
    FILTER_TRILINEAR = 0x2000
    FILTER_BLEND = 0x4000
    # UV Properties
    FLAG_CLAMP_V = 0x008000
    FLAG_CLAMP_U = 0x010000
    FLAG_FLIP_V = 0x020000
    FLAG_FLIP_U = 0x040000
    # General material Properties
    FLAG_IGNORE_SPECULAR = 0x080000
    FLAG_USE_ALPHA = 0x100000
    FLAG_USE_TEXTURE = 0x200000
    FLAG_USE_ENV = 0x400000
    FLAG_DOUBLE_SIDE = 0x800000
    FLAG_USE_FLAT = 0x01000000
    FLAG_IGNORE_LIGHT = 0x02000000
    # Destination alpha blending
    DA_ONE = 0x04000000
    DA_OTHER = 0x08000000
    DA_SRC = 0x10000000
    DA_INV_OTHER = DA_ONE | DA_OTHER
    DA_INV_SRC = DA_ONE | DA_SRC
    DA_DST = DA_OTHER | DA_SRC
    DA_INV_DST = DA_ONE | DA_OTHER | DA_SRC
    # Source Alpha Blending
    SA_ONE = 0x20000000
    SA_OTHER = 0x40000000
    SA_SRC = 0x80000000
    SA_INV_OTHER = SA_ONE | SA_OTHER
    SA_INV_SRC = SA_ONE | SA_SRC
    SA_DST = SA_OTHER | SA_SRC
    SA_INV_DST = SA_ONE | SA_OTHER | SA_SRC

class PolyType(Enum):
    """Determines the arrangement of poly indices"""
    Triangles = 0
    Quads = 1
    NPoly = 2
    Strips = 3