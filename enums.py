from enum import Enum, Flag

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


class Chunktypes(Enum):
    """Meta Data type"""
    null = 0x0
    Label = 0x4C42414C  # LABl
    Animation = 0x4d494e41  # ANIM
    Morph = 0x46524F4D  # MORF
    Author = 0x48545541  # AUTH
    Tool = 0x4C4F4F54  # TOOL
    Description = 0x43534544  # DESC
    Texture = 0x00584554  # TEX
    End = 0x00444E45  # END

    @classmethod
    def _missing_(cls, value):
        print("invalid chunk type:", '{:04x}'.format(value))
        return Chunktypes.null


class ObjectFlags(Flag):
    """Object flags used in models"""
    null = 0x00
    NoPosition = 0x01
    NoRotate = 0x02
    NoScale = 0x04
    NoDisplay = 0x08
    NoChildren = 0x10
    RotateZYX = 0x20
    NoAnimate = 0x40
    NoMorph = 0x80


class SA1SurfaceFlags(Flag):
    """Surface interaction Flags for SA1 landtable COL"""
    null = 0x0
    Solid = 0x1
    Water = 0x2
    NoFriction = 0x4
    NoAcceleration = 0x8
    CannotLand = 0x40
    IncreasedAcceleration = 0x80
    Diggable = 0x100
    Unclimbable = 0x1000
    Hurt = 0x10000
    Footprints = 0x100000
    Visible = 0x80000000

    collision = (Solid
                 | Water
                 | NoFriction
                 | NoAcceleration
                 | CannotLand
                 | IncreasedAcceleration
                 | Diggable
                 | Unclimbable
                 | Hurt
                 | Footprints)

    known = (Solid
             | Water
             | NoFriction
             | NoAcceleration
             | CannotLand
             | IncreasedAcceleration
             | Diggable
             | Unclimbable
             | Hurt
             | Footprints
             | Visible)


class SA2SurfaceFlags(Flag):
    """Surface interaction Flags for SA2 landtable COL"""
    null = 0x00
    Solid = 0x01
    Water = 0x02
    Diggable = 0x20
    Unclimbable = 0x80
    StandOnSlope = 0x100
    Hurt = 0x0400
    Footprints = 0x800
    CannotLand = 0x1000
    Water2 = 0x2000
    NoShadows = 0x8000
    noFog = 0x400000
    Unknown24 = 0x01000000
    Unknown29 = 0x20000000
    Unknown30 = 0x40000000
    Visible = 0x80000000

    collision = (Solid
                 | Water
                 | StandOnSlope
                 | Diggable
                 | Unclimbable
                 | Hurt
                 | CannotLand
                 | Water2
                 | Unknown24
                 | Unknown29
                 | Unknown30)

    known = (Solid
             | Water
             | StandOnSlope
             | Diggable
             | Unclimbable
             | Hurt
             | CannotLand
             | Water2
             | NoShadows
             | noFog
             | Unknown24
             | Unknown29
             | Unknown30
             | Visible)

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
    Null = 255


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

    @property
    def length(self) -> int:
        if self == DataType.Unsigned8 \
                or self == DataType.Signed8:
            return 1
        elif self == DataType.Unsigned16 \
                or self == DataType.Signed16 \
                or self == DataType.RGB565 \
                or self == DataType.RGBA4:
            return 2
        elif self == DataType.RGBA6 \
                or self == DataType.RGB8:
            return 3
        return 4


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

    @property
    def length(self) -> int:
        if self == ComponentCount.TexCoord_S \
                or self == ComponentCount.Color_RGB \
                or self == ComponentCount.Color_RGBA:
            return 1
        elif self == ComponentCount.Position_XY \
                or self == ComponentCount.TexCoord_ST:
            return 2
        elif self == ComponentCount.Position_XYZ \
                or self == ComponentCount.Normal_XYZ:
            return 3
        return 4


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
    null = 0x00
    Bit0 = 0x01  # unused
    Bit1 = 0x02  # unused
    Position16BitIndex = 0x04
    HasPosition = 0x08
    Normal16BitIndex = 0x10
    HasNormal = 0x20
    Color16BitIndex = 0x40
    HasColor = 0x80
    Bit8 = 0x0100  # unused
    Bit9 = 0x0200  # unused
    UV16BitIndex = 0x0400
    HasUV = 0x0800
    Bit12 = 0x1000  # unused
    Bit13 = 0x2000  # unused
    Bit14 = 0x4000  # unused
    Bit15 = 0x8000  # unused


class AlphaInstruction(Enum):
    """The way in which the alpha of a
    texture should be handled when rendering"""
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
    null = 0x00
    WrapV = 0x01
    MirrorV = 0x02
    WrapU = 0x04
    MirrorU = 0x08
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
    TexCoordMax = 8  # last uv map?
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
    """Which values of the mesh should be
    used for generating the texture coordinates"""
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
    Matrix0 = 0
    Matrix1 = 1
    Matrix2 = 2
    Matrix3 = 3
    Matrix4 = 4
    Matrix5 = 5
    Matrix6 = 6
    Matrix7 = 7
    Matrix8 = 8
    Matrix9 = 9
    Identity = 10


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
    null = 0x00
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

# CHUNK format enums and flags:


class ChunkType(Enum):
    """Chunk format types"""
    Null = 0
    # Bits
    Bits_BlendAlpha = 1
    Bits_MipmapDAdjust = 2
    Bits_SpecularExponent = 3
    Bits_CachePolygonList = 4
    Bits_DrawPolygonList = 5
    # Tiny
    Tiny_TextureID = 8
    Tiny_TextureID2 = 9
    # Material
    Material = 16
    Material_Diffuse = 17
    Material_Ambient = 18
    Material_DiffuseAmbient = 19
    Material_Specular = 20
    Material_DiffuseSpecular = 21
    Material_AmbientSpecular = 22
    Material_DiffuseAmbientSpecular = 23
    Material_Bump = 24
    Material_Diffuse2 = 25
    Material_Ambient2 = 26
    Material_DiffuseAmbient2 = 27
    Material_Specular2 = 28
    Material_DiffuseSpecular2 = 29
    Material_AmbientSpecular2 = 30
    Material_DiffuseAmbientSpecular2 = 31
    # Vertex
    Vertex_VertexSH = 32
    Vertex_VertexNormalSH = 33
    Vertex_Vertex = 34
    Vertex_VertexDiffuse8 = 35
    Vertex_VertexUserFlags = 36
    Vertex_VertexNinjaFlags = 37
    Vertex_VertexDiffuseSpecular5 = 38
    Vertex_VertexDiffuseSpecular4 = 39
    Vertex_VertexDiffuseSpecular16 = 40
    Vertex_VertexNormal = 41
    Vertex_VertexNormalDiffuse8 = 42
    Vertex_VertexNormalUserFlags = 43
    Vertex_VertexNormalNinjaFlags = 44
    Vertex_VertexNormalDiffuseSpecular5 = 45
    Vertex_VertexNormalDiffuseSpecular4 = 46
    Vertex_VertexNormalDiffuseSpecular16 = 47
    Vertex_VertexNormalX = 48
    Vertex_VertexNormalXDiffuse8 = 49
    Vertex_VertexNormalXUserFlags = 50
    # Volume
    Volume_Polygon3 = 56
    Volume_Polygon4 = 57
    Volume_Strip = 58
    # Strip
    Strip_Strip = 64
    Strip_StripUVN = 65
    Strip_StripUVH = 66
    Strip_StripNormal = 67
    Strip_StripUVNNormal = 68
    Strip_StripUVHNormal = 69
    Strip_StripColor = 70
    Strip_StripUVNColor = 71
    Strip_StripUVHColor = 72
    Strip_Strip2 = 73
    Strip_StripUVN2 = 74
    Strip_StripUVH2 = 75
    # End
    End = 255


class WeightStatus(Enum):
    Start = 0
    Middle = 1
    End = 2


class SA2AlphaInstructions(Flag):
    null = 0x0
    # Destination alpha blending
    DA_ONE = 0x1
    DA_OTHER = 0x2
    DA_SRC = 0x4
    DA_INV_OTHER = DA_ONE | DA_OTHER
    DA_INV_SRC = DA_ONE | DA_SRC
    DA_DST = DA_OTHER | DA_SRC
    DA_INV_DST = DA_ONE | DA_OTHER | DA_SRC
    # Source Alpha Blending
    SA_ONE = 0x8
    SA_OTHER = 0x10
    SA_SRC = 0x20
    SA_INV_OTHER = SA_ONE | SA_OTHER
    SA_INV_SRC = SA_ONE | SA_SRC
    SA_DST = SA_OTHER | SA_SRC
    SA_INV_DST = SA_ONE | SA_OTHER | SA_SRC


class MipMapDistanceAdjust(Flag):
    null = 0x0
    D_025 = 0x1
    D_050 = 0x2
    D_100 = 0x4
    D_200 = 0x8


class TextureIDFlags(Flag):
    null = 0x0
    D_025 = 0x01
    D_050 = 0x02
    D_100 = 0x04
    D_200 = 0x08
    CLAMP_V = 0x10
    CLAMP_U = 0x20
    FLIP_V = 0x40
    FLIP_U = 0x80


class TextureFiltering(Enum):
    Point = 0
    Bilinear = 1
    Trilinear = 2
    Blend = 3


class StripFlags(Flag):
    null = 0x0
    IGNORE_LIGHT = 0x01
    INGORE_SPECULAR = 0x02
    IGNORE_AMBIENT = 0x04
    USE_ALPHA = 0x08
    DOUBLE_SIDE = 0x10
    FLAT_SHADING = 0x20
    ENV_MAPPING = 0x40
    Unknown = 0x80
