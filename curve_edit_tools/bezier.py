import numpy as np

class CubicBezier(object):
    def __init__(self, points):
        self.points = np.array(points).astype(np.float32)

    def at(self, t):
        pt =  1 *        (1 - t)**3 * self.points[0]
        pt += 3 * t**1 * (1 - t)**2 * self.points[1]
        pt += 3 * t**2 * (1 - t)**1 * self.points[2]
        pt += 1 * t**3              * self.points[3]
        return pt

    def split(self, t):
        p1, p2, p3, p4 = self.points
        
        p12 = (p2-p1)*t+p1
        p23 = (p3-p2)*t+p2
        p34 = (p4-p3)*t+p3
        p123 = (p23-p12)*t+p12
        p234 = (p34-p23)*t+p23
        p1234 = (p234-p123)*t+p123

        return [p1,p12,p123,p1234,p234,p34,p4]