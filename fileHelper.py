import bpy
import os
import mathutils
import struct
import tempfile


class FileWriter:
    """Handles file writing
    
    Contains methods to make binary writing easier

    Default endian: little
    """

    def __init__(self, filepath = None):
        if filepath is None:
            self.oFile = tempfile.TemporaryFile(mode="wb+") # write and read, binary  
            self.filepath = self.oFile.name
        else:
            self.oFile = open(filepath, "wb+") # write and read, binary        
            self.filepath = filepath

        self.endian = "<"

    # general methods

    def setBigEndian(self, bigEndian = False):
        self.endian = ">" if bigEndian else "<"
    
    def isBigEndian(self):
        return self.endian == ">"

    def tell(self):
        """Returns current position in file"""
        return self.oFile.tell()

    def seek(self, offset, relativeTo):
        """Moves writer position in current file
        
        relativeTo: 0 = start, 1 = current position, 2 = end
        """
        self.oFile.seek(offset, relativeTo)

    def seekEnd(self):
        """Returns writer position to the end of the file"""
        self.oFile.seek(0, 2)

    def close(self):
        """Closes File"""
        self.oFile.close()

    def align(self, by):
        size = self.tell()
        remaining = by - (size % by)
        if remaining == by:
            return
        self.w(bytes([0] * remaining))

    def pad(self, start, padding):
        length = self.tell() - start
        newlength = length + (padding - 1) & ~(0x1F)
        addLength = newlength - length
        self.w(bytes([0] * addLength))

    #Writer methods

    def w(self, value):
        """Writes value to file"""
        self.oFile.write(value)

    def wByte(self, value):
        """Writes single byte"""
        self.w(struct.pack(self.endian + "B", value))

    def wShort(self, value):
        """Writes a signed Short"""
        self.w(struct.pack(self.endian + "h", value))

    def wUShort(self, value):
        """Writes an unsigned Short"""
        self.w(struct.pack(self.endian + "H", value))

    def wHalf(self, value):
        """Writes a Float"""
        self.w(struct.pack(self.endian + "e", value))  

    def wInt(self, value):
        """Writes a signed Integer"""
        self.w(struct.pack(self.endian + "i", value))
      
    def wUInt(self, value):
        """Writes an unsigned Integer"""
        self.w(struct.pack(self.endian + "I", value))

    def wFloat(self, value):
        """Writes a Float"""
        self.w(struct.pack(self.endian + "f", value))        

    def wLong(self, value):
        """Writes a signed Long"""
        self.w(struct.pack(self.endian + "q", value))

    def wULong(self, value):
        """Writes an unsigned Long"""
        self.w(struct.pack(self.endian + "Q", value))
    
    def wDouble(self, value):
        """Writes a Double"""
        self.w(struct.pack(self.endian + "d", value))     

    def wString(self, string):
        """Writes a String in utf-8"""
        self.w(string.encode('utf-8'))
        self.wByte(0x00)

class FileReader:


    def __init__(self, filepath: str):
        import os
        if filepath is None or not os.path.exists(filepath):
            print("Invalid file path")
            self.filepath = None
        else:
            oFile = open(filepath, "rb") # read, binary 
            self.fileC = oFile.read()
            oFile.close()
            self.filepath = filepath
            self.endian = "<"

    def setBigEndian(self, bigEndian = False):
        self.endian = ">" if bigEndian else "<"
    
    def isBigEndian(self):
        return self.endian == ">"

    # reading bytes in a specific way

    def rByte(self, address: int):
        """Returns a Byte"""
        return struct.unpack_from("B", self.fileC, address)[0]

    def rShort(self, address: int):
        """Returns a Short"""
        return struct.unpack_from(self.endian + "h", self.fileC, address)[0]

    def rUShort(self, address: int):
        """Returns an unsigned Short"""
        return struct.unpack_from(self.endian + "H", self.fileC, address)[0]

    def rHalf(self, address: int):
        """Returns a Half"""
        return struct.unpack_from(self.endian + "e", self.fileC, address)[0]

    def rInt(self, address: int):
        """Returns an Integer"""
        return struct.unpack_from(self.endian + "i", self.fileC, address)[0]
    
    def rUInt(self, address: int):
        """Returns an unsigned Integer"""
        return struct.unpack_from(self.endian + "I", self.fileC, address)[0]

    def rFloat(self, address: int):
        """Returns a Float"""
        return struct.unpack_from(self.endian + "f", self.fileC, address)[0]

    def rLong(self, address: int):
        """Returns a Long"""
        return struct.unpack_from(self.endian + "q", self.fileC, address)[0]

    def rULong(self, address: int):
        """Returns an unsigned Long"""
        return struct.unpack_from(self.endian + "Q", self.fileC, address)[0]

    def rDouble(self, address: int):
        """Returns a Double"""
        return struct.unpack_from(self.endian + "d", self.fileC, address)[0]

    def rString(self, address: int):
        string = []
        i = self.fileC[address]
        while i != 0:
            string.append(i)
            address += 1
            i = self.fileC[address]
        string.append(i) # adding the 0


        return bytes(string).decode('utf-8')
