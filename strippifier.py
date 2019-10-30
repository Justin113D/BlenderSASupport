
# can be used to transform a triangle list into a triangle strip (using an index list)

#base classes, which can be used in any strippifier algorithm

from collections import Counter

class TopologyError(Exception):

    def __init__(self, message):
        super().__init__(message)

class Mesh:
    """contains all vertices, faces and edges from a tri list"""
    triangles = list() #triangles of the mesh
    edges = list() #edges of the mesh
    vertices = list() #vertices of the mesh

    def __init__(self, triList):
        self.triangles = [None] * (int(len(triList) / 3))
        self.edges = list()

        vertCount = max(triList) + 1

        self.vertices = [None] * vertCount
        for v in range(vertCount):
            self.vertices[v] = Vertex(v)

        for i in range(0, len(triList), 3):
            tri = Triangle( int(i / 3),
                            self.vertices[triList[i]],
                            self.vertices[triList[i+1]],
                            self.vertices[triList[i+2]],
                            self.edges)
            self.triangles[int(i / 3)] = tri
            

class Triangle:

    index = 0
    neighbours = list() # The triangles that this triangle is connected through its adjacencies (max. 3)
    edges = [None] * 3 # The three adjacencies that this triangle consists of
    vertices = [None] * 3 # The three vertices that this triangle consists of
    used = False # Whether the triangle is in any strip
    inList = False # Whether the triangle is already in the priority list

    def __init__(self, index, v1, v2, v3, edges):
        #setting vertices
        self.index = index

        self.vertices = [v1, v2, v3]

        v1.triangles.append(self)
        v2.triangles.append(self)
        v3.triangles.append(self)

        self.neighbours = list()

        #getting or creating the edges
        e1 = self.addEdge(v1, v2, edges)
        e2 = self.addEdge(v1, v3, edges)
        e3 = self.addEdge(v2, v3, edges)

        self.edges = [e1, e2, e3]
        if None in self.edges:
            self.edges = None
        
    def addEdge(self, v1, v2, edges):
        e = v1.isConnectedWith(v2)
        if e is None:
            e = v1.connect(v2)
            e.triangles.append(self)
            self.edges.append(e)
        else: # if edge existed before, then it has to have a triangle attached to it
            self.neighbours.append(e.triangles[0])
            e.triangles[0].neighbours.append(self)
            e.setTriangle(self)
            
        return e

    def hasVertex(self, v):
        """Checks whether the vertex is part of the tri"""
        return v in self.vertices

    def getThirdVertex(self, v1, v2):
        """both v1 and v2 should be part of the triangle. returns the third vertex of the triangle"""
        for v in self.vertices:
            if v is v1 or v is v2:
                continue
            return v
        return None

    def getCommonAdjacency(self, otherTri):
        if otherTri not in self.neighbours:
            print("tris no neighbours")
            return None
        for e in self.edges:
            for oe in otherTri.edges:
                if e is oe:
                    return e
        return None

    def availableNeighbours(self):
        result = list()
        for t in self.neighbours:
            if not t.used:
                result.append(t)
        return result

    def getNextStripTri(self, prevVert = None, curVert = None):
        """ """
        # checking how many tris can be used at all
        trisToUse = self.availableNeighbours()
        hasBase = prevVert is not None and curVert is not None

        # if no tri can be used, return null, ending the strip
        if len(trisToUse) == 0:
            return None
        elif len(trisToUse) == 1: # if there is only one, use it
            return trisToUse[0]
        
        # if there are more than one, get the usable one
        weights = [0] * len(trisToUse)
        vConnection = [0] * len(trisToUse)
        biggestConnection = 0

        # base weights and getting triangle connectivity
        for i, t in enumerate(trisToUse):
            weights[i] = len(t.availableNeighbours())
            
            if weights[i] == 0:
                return t

            if hasBase:
                # if a swap is needed, add weight
                if t.hasVertex(curVert):
                    weights[i] -= 1
                    vConnection[i] = prevVert.availableTris()
                else:
                    weights[i] += 1
                    vConnection[i] = curVert.availableTris()
            else:
                e = t.getCommonAdjacency(self)
                vConnection[i] = e.vertices[0].availableTris() + e.vertices[1].availableTris() - 2

            if vConnection[i] > biggestConnection:
                biggestConnection = vConnection[i]
        
        # integrating connectivity into the weights
        for i, v in enumerate(vConnection):
            if v < biggestConnection:
                weights[i] -= 1
            else:
                weights[i] += 1

        # getting the triangle with the lowest weight
        index = 0
        for i in range(1, len(trisToUse)):
            if weights[i] < weights[index]:
                index = i
            elif hasBase and weights[i] == weights[index]:
                if trisToUse[i].hasVertex(curVert):
                    index = i
        
        return trisToUse[index]

    def getNextStripTriSeq(self, prevVert, curvVert):
        e = curvVert.isConnectedWith(prevVert)
        #print(e is None)
        #getting the other triangle
        t = None
        if e.triangles[0] is self:
            if len(e.triangles) == 1:
                return None
            else:
                t = e.triangles[1]
        else:
            t = e.triangles[0]

        if t.used:
            return None
        else:
            return t

    def __str__(self):
        return str(self.index) + ": " + str(self.used) + ", " + "(" + str(self.vertices[0]) + ", " + str(self.vertices[1]) + ", " + str(self.vertices[2]) +")"

class Edge:
    """An Edge/Adjacency in between two vertices"""
    vertices = [None] * 2 # The two vertices that this adjacency consists of    
    triangles = list() # The triangles that consist of this adjacency (min. 1, max. 2)

    def __init__(self, vertex1, vertex2):
        self.vertices = [vertex1, vertex2]
        self.triangles = list()
        
    def setTriangle(self, triangle):
        """Sets a triangle to be part of the adjacency"""
        if len(self.triangles) < 2:
            self.triangles.append(triangle)
        else:
            raise TopologyError("Some Edge has more than 2 faces! cant strippify!")

    def __str__(self):
        return str(self.vertices[0]) + ", " + str(self.vertices[1])

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
            if e.vertices[0] is otherVert or e.vertices[1] is otherVert:
                return e
        return None
        
    def connect(self, otherVert):
        """Creates and returns a new Adjacency (updated other vertex too)"""
        edge = Edge(self, otherVert)
        self.edges.append(edge)
        otherVert.edges.append(edge)
        return edge
    
    def __str__(self):
        return str(self.index)


class Strippifier:
    # based on the paper written by David Kronmann:
    # https://pdfs.semanticscholar.org/9749/331d92f865282c3f5a19b73b25c4f0ac02bc.pdf
    # The code has been written and slightly modified by me Justin113D, and added
    # options such as noSwaps, and also slightly optimized the strips by handling
    # the priority list slightly different

    def addZTriangle(self, tri: Triangle):
        """creates a strip from a triangle with no (free) neighbours"""
        v = tri.vertices
        self.strips.append([v[0].index, v[1].index, v[2].index])
        self.written += 1
        tri.used = True

    def priorityFill(self):
        """Fills the priority list, which is used to get the starting triangle"""
        if len(self.priorityTris) > 0:
            for t in self.priorityTris:
                t.inList = False

        self.priorityTris = list()

        # gets an initial starting point
        startIndex = 1
        for i, t in enumerate(self.mesh.triangles):
            if not t.used: # and not t.inList:
                if len(t.availableNeighbours()) == 0:
                    self.addZTriangle(t)
                    continue
                self.priorityTris.append(t)
                t.inList = True
                startIndex = i + 1
                break
            
        # if there are no more tris that can be added to a strip, we are done
        if len(self.priorityTris) == 0:
            return
        
        # opponent neighbours
        oN = len(self.priorityTris[0].availableNeighbours())

        # when a triangle with only one available neighbour was found,
        # then its not worth looking for more triangles
        if oN == 1:
            self.indexC2 = 0
            return

        self.indexC2 = 1

        # fills the priority list
        for i in range(startIndex, len(self.mesh.triangles)):
            t = self.mesh.triangles[i]
            if t.used:
                continue
                
            n = len(t.availableNeighbours())

            # this case can only take place if oN is bigger than 1, so there is no need to increase indexC2
            if n == oN:
                self.priorityTris.append(t)
                t.inList = True
            elif n < oN and n != 0:
                for lt in self.priorityTris:
                    lt.inList = False
                self.priorityTris = list([t])
                t.inList = True

                # updating opponent neighbours
                oN = len(t.availableNeighbours())

                if oN == 1:
                    self.indexC2 = 1
                    return
                self.indexC2 = 0

    def Strippify(self, indexList, doSwaps = False, concat = False):
        """creates a triangle strip from a triangle list.
        
        If concat is True, all strips will be combined into one.
        
        If its False, it will return an array of strips"""
        self.strips = list()

        # reading the index data into a mesh
        self.mesh = Mesh(indexList)
        # amount of written triangles
        self.written = 0

        # index to know where to append triangles with 2 neighbours (1 is start, 3 is end)
        self.indexC2 = 0

        # getting rid of lone triangles first
        for t in self.mesh.triangles:
            if len(t.availableNeighbours()) == 0:
                self.addZTriangle(t)

        # priority list of potential starting tris
        self.priorityTris = list()

        self.priorityFill()

        # as long as some triangles remain to be written, keep the loop running
        triCount = len(self.mesh.triangles)

        while self.written != triCount:
            
            # getting the starting tris
            firstTri = self.priorityTris[0]
            currentTri = firstTri
            currentTri.used = True

            newTri = currentTri.getNextStripTri()
            newTri.used = True   

            secNewTri = newTri.getNextStripTri()                    

            # get the starting vert (the one which is not connected with the new tri)
            commonEdge = currentTri.getCommonAdjacency(newTri)
            prevVert = currentTri.getThirdVertex(commonEdge.vertices[0], commonEdge.vertices[1])

            # get the vertex which wouldnt be connected to the tri afterwards, to prevent swapping

            if secNewTri is None:
                currentVert = commonEdge.vertices[0]
                thirdVert = commonEdge.vertices[1]
            elif secNewTri.hasVertex(commonEdge.vertices[0]):
                currentVert = commonEdge.vertices[1]
                thirdVert = commonEdge.vertices[0]
            else:
                currentVert = commonEdge.vertices[0]
                thirdVert = commonEdge.vertices[1]

            # initializing strip base
            self.strip = list([prevVert.index, currentVert.index, thirdVert.index])
            self.written += 1

            # shift verts one forward
            prevVert = thirdVert
            currentVert = newTri.getThirdVertex(currentVert, thirdVert)
            
            # shift triangles one forward
            currentTri = newTri
            newTri = secNewTri

            # creating a strip
            reachedEnd = False
            reversedList = False
            while not reachedEnd:
            
                #writing the next index
                self.strip.append(currentVert.index) 
                self.written += 1     

                # ending the loop when the current tri is None (end of the strip)
                if newTri is None:
                    if len(firstTri.availableNeighbours()) > 0 and not reversedList:
                        reversedList = True
                        prevVert = self.mesh.vertices[self.strip[1]]
                        currentVert = self.mesh.vertices[self.strip[0]]
                        if doSwaps:
                            newTri = firstTri.getNextStripTri(prevVert, currentVert)
                        else:
                            newTri = firstTri.getNextStripTriSeq(prevVert, currentVert)
                            if newTri is None:
                                reachedEnd = True
                                continue
                        self.strip.reverse()

                    else:
                        reachedEnd = True
                        continue

                #swapping if necessary
                if doSwaps:
                    secNewTri = newTri.getNextStripTri(prevVert, currentVert)
                    if secNewTri is not None and not secNewTri.hasVertex(currentVert):
                        self.strip.append(prevVert.index)

                        #swapping the vertices
                        t = prevVert
                        prevVert = currentVert
                        currentVert = t          

                # getting the new vertex to write
                thirdVert = newTri.getThirdVertex(prevVert, currentVert)

                prevVert = currentVert
                currentVert = thirdVert

                currentTri = newTri
                currentTri.used = True

                if doSwaps:
                    newTri = secNewTri
                else:
                    newTri = currentTri.getNextStripTriSeq(prevVert, currentVert)


            
            self.strips.append(self.strip)

            self.priorityFill()

        # now that we got all strips, we need to concat them (if we want that)
        if concat:
            # stitching the strips together
            result = self.strips[0]
            if len(self.strips) > 1:
                result.append(result[-1])
                for i in range(1, len(self.strips)):
                    result.append(self.strips[i][0])
                    result.extend(self.strips[i])
                    result.append(result[-1])
                del result[-1]
        else: # or we just return as is
            result = self.strips

        return result
