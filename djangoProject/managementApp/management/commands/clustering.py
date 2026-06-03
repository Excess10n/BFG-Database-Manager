from django.core.management.base import BaseCommand
from ...models import Fungi, FungiCurrent, FungiArchive, FungiCentroids
from ...viewFunctions import getFungiObjects, getAllCurrentFungiObjects
import os
import random
import numpy as np
import matplotlib.pyplot as plt
import math
import time

class Command(BaseCommand):
    def handle(self, *args, **options):
        random.seed(10)
        NUM_CENTROIDS = 3
        VIGOR = 0.75
        NUM_CLOSE = 0

        timer = 0
        def start():
            return time.time()
        def end(x):
            return time.time() - x

        def customRNG(max):
            diff = max
            num = random.randrange(0,1000) / 1000.0
            return (num * diff)
        
        def getAllByIndex(data, i, c=None):
            x = []
            for d in data:
                if (c == None) or (d[3] == c):
                    x.append(d[i])
            return x
        
        def getAllByCent(data, c):
            x = []
            for d in data:
                if d[3] == c:
                    x.append(d)
            return x
        
        def calcDistance(p1, p2):
            dist = math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)
            return dist
        
        def calcCentroidVect(points, cent):
            # calculate each individual vector and divide by total
            vect = [0,0,0]
            num = 0.0
            for x in points:
                vect = [vect[0] + (x[0] - cent[0]), vect[1] + (x[1] - cent[1]), vect[2] + (x[2] - cent[2])]
                num += 1.0
            return [vect[0] / num * VIGOR, vect[1] / num * VIGOR, vect[2] / num * VIGOR]
            
        
        def assignPoints(data, cent):
            for d in data:
                closest = -1
                bestDist = 10000000000
                for i in range(NUM_CENTROIDS):
                    dist = calcDistance(d, cent[i])
                    if dist < bestDist:
                        closest = i
                        bestDist = dist
                d[3] = closest
            return data
        
        timer = start()
        
        objects = getAllCurrentFungiObjects()
        data = []
        centroids = []
        for x in objects:
            data.append([x.capRadius, x.colourDarkness, x.height, -1])
        rMax = max(getAllByIndex(data, 0))
        dMax = max(getAllByIndex(data, 1))
        hMax = max(getAllByIndex(data, 2))

        # pick initial centroid position (must be far apart)
        for i in range(NUM_CENTROIDS):
            done = False
            while not done:
                point = [customRNG(rMax), customRNG(dMax), customRNG(hMax)]
                for j in range(len(centroids)):
                    if abs(point[0] - centroids[j][0]) < rMax / 5.0:
                        break
                    if abs(point[1] - centroids[j][1]) < dMax / 5.0:
                        break
                    if abs(point[2] - centroids[j][2]) < hMax / 5.0:
                        break
                else:
                    done = True
                
                if not done:
                    continue
                done = False
                
                count = 0
                for j in range(len(data)):
                    if abs(point[0] - data[j][0]) < rMax / 100.0:
                        continue
                    if abs(point[1] - data[j][1]) < dMax / 100.0:
                        continue
                    if abs(point[2] - data[j][2]) < hMax / 100.0:
                        continue
                    count += 1
                if count >= NUM_CLOSE:
                    done = True

            centroids.append(point)
        
        data = assignPoints(data, centroids)

        # calculate the cut-off distance
        CUTOFF = calcDistance([rMax, dMax, hMax], [0,0,0]) / 1000.0

        loop = True
        while loop:
            maxDist = 0
            for i in range(NUM_CENTROIDS):
                # get vector of this centroid
                vect = calcCentroidVect(getAllByCent(data, i), centroids[i])
                centroids[i] = [centroids[i][0] + vect[0], centroids[i][1] + vect[1], centroids[i][2] + vect[2]]

                # set maxDist to the highest distance
                dist = calcDistance(vect, [0,0,0])
                if dist > maxDist:
                    maxDist = dist

            # re-assign points
            data = assignPoints(data, centroids)

            if maxDist < CUTOFF:
                loop = False
        
        # set the centroid data in the database
        for i in range(len(data)):
            objects[i].centroid = data[i][3]
            objects[i].save()
        
        FungiCentroids.objects.all().delete()
        for i in range(NUM_CENTROIDS):
            kwargs = {
                'capRadius': centroids[i][0],
                'colourDarkness': centroids[i][1],
                'height': centroids[i][2]
            }
            
        
        print(end(timer))

        kplot = plt.axes(projection='3d')
        #xline = np.linspace(0, 15, 1000)
        #yline = np.linspace(0, 15, 1000)
        #zline = np.linspace(0, 15, 1000)
        #kplot.plot3D(xline, yline, zline, 'black')
        # Data for three-dimensional scattered points
        kplot.scatter3D(getAllByIndex(data, 0, 0), getAllByIndex(data, 1, 0), getAllByIndex(data, 2, 0), c='red', label = 'Cluster 1')
        kplot.scatter3D(getAllByIndex(data, 0, 1), getAllByIndex(data, 1, 1), getAllByIndex(data, 2, 1), c='green', label = 'Cluster 2')
        kplot.scatter3D(getAllByIndex(data, 0, 2), getAllByIndex(data, 1, 2), getAllByIndex(data, 2, 2), c='blue', label = 'Cluster 3')
        kplot.scatter3D(getAllByIndex(centroids, 0), getAllByIndex(centroids, 1), getAllByIndex(centroids, 2), c = 'indigo', s = 200)
        plt.legend()
        kplot.set_xlabel("Height")
        kplot.set_ylabel("Darkness")
        kplot.set_zlabel("Cap radius")
        plt.title("Kmeans")
        plt.show()