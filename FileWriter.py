import bpy
import os
import mathutils
import struct
import tempfile


class FileWriter(object):
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
        """Closes File and returns bytes"""
        self.oFile.seek(0,0)
        data = self.oFile.read()
        self.oFile.close()
        return data

    def align(self, by):
        size = self.tell()
        remaining = by - (size % by)
        if remaining == by:
            return
        self.w(bytes([0] * remaining))

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