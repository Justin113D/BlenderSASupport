
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
        if e is None:
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
            if v is v1 or v is v2:
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
            weights[i] = t.availableNeighbours()

            if hasBase:
                # if a swap is needed, add weight
                if t.hasVertex(curVert):
                    weights[i] += 1
                    vConnection[i] = prevVert.availableTris()
                else:
                    weights[i] -= 1
                    vConnection[i] = curVert.availableTris()
            else:
                e = t.getCommonAdjacency(self)
                vConnection[i] = e.vertices[0].availableTris() + e.vertices[1].availableTris()

            if vConnection[i] > biggestConnection:
                biggestConnection = vConnection[i]

        # integrating connectivity into the weights
        for i in range(len(trisToUse)):
            if vConnection[i] < biggestConnection:
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
        return trisToUse[i]

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
            if e.vertices[0] is otherVert or e.vertices[1] is otherVert:
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

def strippify(indexList, concat = True):
    """creates a triangle strip from a triangle list.
    
    If concat is True, all strips will be combined into one.
    
    If its False, it will return an array of strips"""
    strips = list()

    # reading the index data into a mesh
    mesh = Mesh(indexList)
    # amount of written triangles
    written = 0

    # index to know where to append triangles with 2 neighbours (1 is start, 3 is end)
    indexC2 = 0

    # creates a strip from a triangle with no (free) neighbours
    def addZTriangle(tri: Triangle):
        v = tri.vertices
        strips.append([v[0].index, v[1].index, v[2].index])
        written += 1
        tri.used = True

    # getting rid of lone triangles first
    for t in mesh.triangles:
        if len(t.availableNeighbours()) == 1:
            addZTriangle(t)

    # priority list of potential starting tris
    priorityTris = list()

    # fills the priority list
    def priorityFill():
        priorityTris = list()

        # gets an initial starting point
        startIndex = 1
        for i, t in enumerate(mesh.triangles):
            if not t.used: # and not t.inList:
                if len(t.availableNeighbours()) == 0:
                    addZTriangle(t)
                    continue
                priorityTris.append(t)
                t.inList = True
                startIndex = i
                break
            
        # if there are no more tris that can be added to a strip, we are done
        if len(priorityTris) == 0:
            return
        
        # opponent neighbours
        oN = len(priorityTris[0].availableNeighbours())

        # when a triangle with only one available neighbour was found,
        # then its not worth looking for more triangles
        if oN == 1:
            indexC2 = 0
            return

        indexC2 = 1

        # fills the priority list
        for i in range(startIndex, len(mesh.triangles)):
            t = mesh.triangles[i]
            if t.used:
                continue
                
            n = len(t.availableNeighbours())

            # this case can only take place if oN is bigger than 1, so there is no need to increase indexC2
            if n == oN:
                priorityTris.append(t)
                t.inList = True
            elif n < oN and n not 0:
                for lt in priorityTris:
                    lt.inList = False
                priorityTris = list([t])
                t.inList = True

                # updating opponent neighbours
                oN = len(t.availableNeighbours())

                if oN == 1:
                    indexC2 = 1
                    return
                indexC2 = 0

    # add a triangle to the priority list
    def priorityAdd(tri: Triangle):
        if tri.inList or tri.used:
            return

        avTriCount = len(tri.availableNeighbours())
        if avTriCount == 0:
            addZTriangle(tri)
        elif avTriCount == 1:
            priorityTris.insert(0, tri)
            indexC2 += 1
        elif avTriCount == 2:
            priorityTris.insert(indexC2, tri)
        else:
            priorityTris.append(tri)

    # removes all used triangles from the priority list and updates the indices
    def priorityClear():
        newPL = list()
        for t in priorityTris:
            if len(t.availableNeighbours()) == 0:
                addZTriangle(t)
            elif not t.used:
                newPL.append(t)
        priorityTris = newPL

        indexC2 = 0
        for i, t in enumerate(priorityTris):
            if len(t.priorityTris.availableNeighbours()) > 1:
                indexC2 = i
                break

    priorityFill()

    # as long as some triangles remain to be written, keep the loop running
    triCount = len(mesh.triangles)
    while written != triCount:
        
        # getting the starting tris
        currentTri = priorityTris[0]
        newTri = currentTri.getNextStripTri()

        # get the starting vert (the one which is not connected with the new tri)
        commonEdge = currentTri.getCommonAdjacency(newTri)
        prevVert = currentTri.getThirdVertex(commonEdge.vertices[0], commonEdge.vertices[1])

        # get the vertex which wouldnt be connected to the tri afterwards, to prevent swapping
        currentTri.used = True
        secNewTri = newTri.getNextStripTri()

        if secNewTri is None:
            currentVert = commonEdge.vertices[0]
            thirdVert = commonEdge.vertices[1]
        elif secNewTri.hasVertex(commonEdge.vertices[0]):
            currentVert = commonEdge.vertices[1]
            thirdVert = commonEdge.vertices[0]
        else:
            currentVert = commonEdge.vertices[0]
            thirdVert = commonEdge.vertices[1]

        #mark the tri as written
        written += 1

        # initializing strip base
        strip = list([prevVert.index, currentVert.index, thirdVert.index])

        # shift verts one forward
        prevVert = currentVert
        currentVert = thirdVert
        
        # shift triangles one forward
        currentTri = newTri
        currentTri.used = True
        newTri = secNewTri
        written += 1

        reachedEnd = False
        while not reachedEnd:
            # ending the loop when the current tri is None (end of the strip)
            if newTri is None:
                #writing the last index
                strip.append(currentTri.getThirdVertex(prevVert, currentVert).index)
                reachedEnd = True
                continue

            #swapping if necessary
            if not newTri.hasVertex(currentVert):
                strip.append(prevVert.index)

                #swapping the vertices
                t = prevVert
                prevVert = currentVert
                currentVert = t

            # getting the new vertex to write
            thirdVert = currentTri.getThirdVertex(prevVert, currentVert).index
            strip.append(secNewTri.index)
            prevVert = currentVert
            currentVert = thirdVert

            currentTri = newTri
            currentTri.used = True
            written += 1

            # updating priority list
            for n in currentTri.neighbours:
                priorityAdd(n)

            # getting the next tri
            newTri = currentTri.getNextStripTri(prevVert, currentVert)
        
        strips.append(strip)
        priorityClear()

        if len(priorityTris) == 0:
            priorityFill()

    # now that we got all strips, we need to concat them (if we want that)
    if concat:
        # stitching the strips together
        result = strips[i]
        if len(strips) > 1:
            result.append(result[-1])
            for i in range(1, len(strips)):
                result.append(strips[i][0])
                result.extend(strips[i])
                result.append(result[-1])
            del result[-1]
    else: # or we just return as is
        result = strips

    return result
