
# can be used to transform a triangle list into a triangle strip (using an index list)

#base classes, which can be used in any strippifier algorithm

from collections import Counter
from typing import List, Tuple

raiseTopoErrorG = True

class TopologyError(Exception):

    def __init__(self, message):
        super().__init__(message)

class Vertex:
    """A single point in the Mesh."""
    index: int # The local index of the vertex
    edges: List # The adjacencies which it is part of
    triangles: List # The triangles which it is part of

    def __init__(self, index: int):
        self.index = index
        self.edges = list()
        self.triangles = list()

    def availableTris(self) -> int:
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
            if otherVert in e.vertices:
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

class Edge:
    """An Edge/Adjacency in between two vertices"""
    vertices: Tuple[Vertex, Vertex] # The two vertices that this adjacency consists of
    triangles: List # The triangles that consist of this adjacency (min. 1, max. 2)

    def __init__(self, vertex1: Vertex, vertex2: Vertex):
        self.vertices = (vertex1, vertex2)
        self.triangles = list()

    def addTriangle(self, tri):
        for t in self.triangles:
            t.neighbours.append(tri)
            tri.neighbours.append(t)

        self.triangles.append(tri)
        tri.edges.append(self)

    def __str__(self):
        return "(" + str(self.vertices[0]) + ", " + str(self.vertices[1]) + ")"

class Triangle:

    index: int
    neighbours: List[Edge] # The triangles that this triangle is connected through its adjacencies (max. 3)
    edges: List[Edge] # The three adjacencies that this triangle consists of
    vertices: List[Vertex] # The three vertices that this triangle consists of
    used: bool # Whether the triangle is in any strip
    inList: bool # Whether the triangle is already in the priority list

    def __init__(self, index, verts, edges):
        #setting vertices
        self.index = index

        self.vertices = verts
        self.edges = list()
        self.neighbours = list()
        for i in range(-1, 2):
            self.vertices[i].triangles.append(self)
            self.addEdge(self.vertices[i], self.vertices[i + 1], edges)

        self.used = False
        self.inList = False

    def addEdge(self, v1, v2, edges):
        e = v1.isConnectedWith(v2)

        if e is None:
            e = v1.connect(v2)
            edges.append(e)

        # if edge existed before, then it has to have a triangle attached to it
        elif raiseTopoErrorG and len(e.triangles) > 1:
            raise TopologyError("Some Edge has more than 2 faces! cant strippify!")

        e.addTriangle(self)

        return e

    def hasVertex(self, v):
        """Checks whether the vertex is part of the tri"""
        return v in self.vertices

    def getThirdVertex(self, v1, v2) -> Vertex:
        """both v1 and v2 should be part of the triangle. returns the third vertex of the triangle"""
        if not (v1 in self.vertices and v2 in self.vertices):
            return None
        for v in self.vertices:
            if v is v1 or v is v2:
                continue
            return v
        print("Vertex not in triangle")
        return None

    def getCommonAdjacency(self, otherTri):
        if otherTri not in self.neighbours:
            print("tris no neighbours")
            return None
        for e in self.edges:
            if e in otherTri.edges:
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
        e = prevVert.isConnectedWith(curvVert)

        #getting the other triangle
        for tri in e.triangles:
            if tri is not self and not tri.used:
                return tri

        return None

    def __str__(self):
        return str(self.index) + ": " + str(self.used) + ", " + "(" + str(self.vertices[0]) + ", " + str(self.vertices[1]) + ", " + str(self.vertices[2]) +")"

class Mesh:
    """contains all vertices, faces and edges from a tri list"""
    triangles = list() #triangles of the mesh
    edges = list() #edges of the mesh
    vertices = list() #vertices of the mesh

    def __init__(self, triList):
        vertCount = max(triList) + 1

        self.vertices = [Vertex(v) for v in range(vertCount)]

        self.edges = list()
        self.triangles = [  Triangle( int(i / 3),
                            [self.vertices[triList[i + t]] for t in range(3)],
                            self.edges)
                            for i in range(0, len(triList), 3)]

        # checking for tripple edges
        triEdgeCount = 0
        for e in self.edges:
            if len(e.triangles) > 2:
                triEdgeCount += 1

        if triEdgeCount > 0:
            print("There are", triEdgeCount, "edges with more than two faces")


class Strippifier:
    # based on the paper written by David Kronmann:
    # https://pdfs.semanticscholar.org/9749/331d92f865282c3f5a19b73b25c4f0ac02bc.pdf
    # The code has been written and slightly modified by me Justin113D, and added
    # options such as noSwaps, and also slightly optimized the strips by handling
    # the priority list slightly different

    def addZTriangle(self, tri: Triangle):
        """creates a strip from a triangle with no (free) neighbours"""
        v = tri.vertices
        self.strips.append([v[0].index, v[2].index, v[1].index])
        self.written += 1
        tri.used = True

    def getFirstTri(self):
        resultTri = None
        curNCount = 0xFFFF

        for i, t in enumerate(self.mesh.triangles):
            if not t.used:
                tnCount = len(t.availableNeighbours())
                if tnCount == 0:
                    self.addZTriangle(t)
                    continue
                if tnCount < curNCount:
                    if tnCount == 1:
                        return t
                    curNCount = tnCount
                    resultTri = t

        if resultTri is None:
            print()

        return resultTri

    @classmethod
    def brokenCullFlow(cls, triA: Triangle, triB: Triangle) -> bool:
        for v in triA.vertices:
            if v in triB.vertices:
                t = triB.vertices.index(v)
                tt = triA.vertices.index(v)
                if triB.vertices[t-1] is triA.vertices[tt-1]:
                    t -= 1
                    tt -= 1
                return triB.vertices[t - 2] is triA.vertices[tt - 2]
        return None

    def Strippify(self, indexList, doSwaps = False, concat = False, raiseTopoError = False):
        """creates a triangle strip from a triangle list.

        If concat is True, all strips will be combined into one.

        If its False, it will return an array of strips"""

        import time
        now = time.time()

        global raiseTopoErrorG
        raiseTopoErrorG = raiseTopoError

        self.mesh = Mesh(indexList)     # reading the index data into a mesh
        self.written = 0                # amount of written triangles
        self.strips = list()            # the result list

        # as long as some triangles remain to be written, keep the loop running
        triCount = len(self.mesh.triangles)

        firstTri = self.getFirstTri()

        while self.written != triCount:
            # when looking for the first triangle, we also filter out some single triangles,
            # which means that it will alter the written count
            # thats why we have to call it before the loop starts and before the end of the loop, instead of once at the start

            # the first thing we gotta do is determine the first (max) 3 triangles to write
            currentTri = firstTri
            currentTri.used = True

            newTri = currentTri.getNextStripTri()

            # If the two triangles have a broken cull flow, then dont continue the strip
            # (well ok, there is a chance it could continue on another tri, but its not worth looking for such a triangle)
            if Strippifier.brokenCullFlow(currentTri, newTri):
                self.addZTriangle(currentTri)
                firstTri = self.getFirstTri() # since we are wrapping back around, we have to set the first tri too
                continue

            newTri.used = True # confirmed that we are using it now

            # get the starting vert (the one which is not connected with the new tri)
            sharedVerts = currentTri.getCommonAdjacency(newTri).vertices
            prevVert = currentTri.getThirdVertex(sharedVerts[0], sharedVerts[1])

            # get the vertex which wouldnt be connected to the tri afterwards, to prevent swapping
            secNewTri = newTri.getNextStripTri()

            # if the third tri isnt valid, just end the strip
            # now you might be thinking "but justin, what if the strip can be reversed?"
            # good point, but! if the third triangle already doesnt exist, then that would mean
            # that the second tri has only one neighbour, which can only occur if the first tri
            # also has only one neighbour. Only two triangles in the strip! boom!
            if secNewTri is None:
                currentVert = sharedVerts[1]
                thirdVert = sharedVerts[0]

                self.strips.append([prevVert.index, currentVert.index, thirdVert.index, newTri.getThirdVertex(currentVert, thirdVert).index])
                self.written += 2

                firstTri = self.getFirstTri() # since we are wrapping back around, we have to set the first tri too
                continue

            elif secNewTri.hasVertex(sharedVerts[0]):
                currentVert = sharedVerts[1]
                thirdVert = sharedVerts[0]
            else:
                currentVert = sharedVerts[0]
                thirdVert = sharedVerts[1]

            # initializing strip base
            self.strip = [prevVert.index, currentVert.index, thirdVert.index]
            self.written += 1

            # shift verts two forward
            prevVert = thirdVert
            currentVert = newTri.getThirdVertex(currentVert, thirdVert)

            # shift triangles one forward
            oldTri = currentTri
            currentTri = newTri
            newTri = secNewTri

            if Strippifier.brokenCullFlow(currentTri, newTri):
                newTri = None

            # creating a strip
            reachedEnd = False
            reversedList = False
            while not reachedEnd:

                #writing the next index
                self.strip.append(currentVert.index)
                self.written += 1

                # ending or reversing the loop when the current tri is None (end of the strip)
                if newTri is None:

                    if not reversedList and len(firstTri.availableNeighbours()) > 0:
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

                        tTri = firstTri
                        firstTri = currentTri
                        currentTri = tTri

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

                if thirdVert is None:
                    reachedEnd = True
                    print("third vert not found... weird")
                    continue

                prevVert = currentVert
                currentVert = thirdVert

                oldTri = currentTri
                currentTri = newTri
                currentTri.used = True

                if Strippifier.brokenCullFlow(oldTri, currentTri):
                    newTri = None
                elif doSwaps:
                    newTri = secNewTri
                else:
                    newTri = currentTri.getNextStripTriSeq(prevVert, currentVert)

            #checking if the triangle is reversed

            for i in range(3):
                if self.strip[i] == firstTri.vertices[0].index:
                    if firstTri.vertices[1].index == self.strip[0 if i == 2 else i + 1]:
                        self.strip.insert(0, self.strip[0])
                    break

            self.strips.append(self.strip)

            # getting the first tri
            firstTri = self.getFirstTri()

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
            result = [result]
        else: # or we just return as is
            result = self.strips

        now = time.time() - now
        print(now)

        return result
