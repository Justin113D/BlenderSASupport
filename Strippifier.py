
# can be used to transform a triangle list into a triangle strip (using an index list)
# based on the paper written by David Kronmann:
# https://pdfs.semanticscholar.org/9749/331d92f865282c3f5a19b73b25c4f0ac02bc.pdf

#base classes, which can be used in any strippifier algorithm

from collections import Counter

class Mesh:
    """contains all vertices, faces and edges from a tri list"""
    triangles = list() #triangles of the mesh
    edges = list() #edges of the mesh
    vertices = list() #vertices of the mesh

    def __init__(self, triList):
        triangles = [None] * (len(triList) / 3)
        edges = list()

        vertCount = max(triList) + 1

        vertices = [None] * vertCount
        for v in range(vertCount):
            vertices[v] = Vertex(v)

        for i in range(0, len(triList), 3):
            triangles[i / 3] = Triangle(vertices[triList[i]],
                                        vertices[triList[i+1]],
                                        vertices[triList[i+2]],
                                        edges)

class Triangle:

    neighbours = list() # The triangles that this triangle is connected through its adjacencies (max. 3)
    edges = [None] * 3 # The three adjacencies that this triangle consists of
    vertices = [None] * 3 # The three vertices that this triangle consists of
    used = False # Whether the triangle is in any strip
    inList = False # Whether the triangle is already in the priority list

    def __init__(self, v1, v2, v3, edges):
        #setting vertices
        vertices = [v1, v2, v3]

        v1.triangles.append(self)
        v2.triangles.append(self)
        v3.triangles.append(self)

        neighbours = list()

        #getting or creating the edges
        e1 = addEdge(v1, v2, edges)
        e2 = addEdge(v1, v3, edges)
        e3 = addEdge(v2, v3, edges)

        edges = [e1, e2, e3]
        
    def addEdge(self, v1, v2, edges):
        e = v1.isConnectedWith(v2):
        if e == None:
            e = v1.connect(v2)
            e.triangles = [self]
            edges.append(e)
        else: # if edge existed before, then it has to have a triangle attached to it
            neighbours.append(e.triangles[0])
            e.triangles[0].neighbours.append(self)
            e.setTriangle(self)
        return e

    def hasVertex(self, v):
        """Checks whether the vertex is part of the tri"""
        return v in self.vertices

    def getThirdVertex(self, v1, v2):
        """both v1 and v2 should be part of the triangle. returns the third vertex of the triangle"""
        for v in vertices:
            if v == v1 or v == v2:
                continue
            if result is None:
                return v
        return None

    def getCommonAdjacency(self, otherTri):
        if othertri not in self.neighbours:
            print("tris no neighbours")
            return None
        for e in self.edges:
            for oe in otherTri.neighbours:
                if e == oe:
                    return e
        return None

    def availableNeighbours(self):
        result = 0
        for t in self.neighbours:
            if not t.used:
                result += 1
        return result
            
class Edge:
    """An Edge/Adjacency in between two vertices"""
    vertices = [None] * 2 # The two vertices that this adjacency consists of    
    triangles = list() # The triangles that consist of this adjacency (min. 1, max. 2)

    def __init__(self, vertex1, vertex2):
        vertices = [vertex1, vertex2]
        triangles = list()
        
    def setTriangle(self, triangle):
        """Sets a triangle to be part of the adjacency"""
        if len(self.triangles) < 2:
            self.triangles.append(triangle)
        else:
            print("Edge between " + str(self) + " already has 2 faces assigned")


    def __str__(self):
        return str(vertices[0] + ", " + vertices[1])

class Vertex:
    """A single point in the Mesh."""
    index = 0 # The local index of the vertex
    edges = list() # The adjacencies which it is part of
    triangles = list() # The triangles which it is part of

    def __init__(self, index):
        self.index = index
        self.edges = list()
        self.triangles = list()

    def availableTris(self):
        """Returns the amount of tris that arent written into a strip yet"""
        result = 0
        for t in self.triangles:
            if not t.used:
                result += 1
        return result

    def isConnectedWith(self, otherVert):
        """If a vertex is connected to another vertex, this method will return that adjacency
            
        otherwise it will return None"""
        for e in self.edges:
            if e.vertices[0] == otherVert or e.vertices[1] == otherVert:
                return e
        return None
        
    def connect(self, otherVert):
        """Creates and returns a new Adjacency (updated other vertex too)"""
        edge = Edge(self, otherVert)
        edges.append(edge)
        otherVert.edges.append(edge)
        return edge
    
    def __str__(self):
        return str(index)

def strippify(indexList):
    #todo
    return indexList
