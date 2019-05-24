import numpy as np
from operator import sub


def _dump(gnss, pix):
    for s, t in  zip(gnss, pix):
        print("%s -> %s " % (s, t))


def _make_A(gnss):
    A = np.zeros((0, 4))

    for p in gnss:
        A = np.append(A, [p + (0, 0)], axis=0)
        A = np.append(A, [(0, 0) + p], axis=0)

    return A


def _make_B(pix):
    B = np.zeros((0, 0))

    for p in pix:
        B = np.append(B, p)

    return B


class Translate:
    def __init__(self, gnss_origin, pix_origin, T):

        self.gnss_orig_x, self.gnss_orig_y = gnss_origin
        self.pix_orig_x, self.pix_orig_y = pix_origin
        self.T = T
        self.iT = np.linalg.inv(T)

    def to_pix(self, x, y):
        x -= self.gnss_orig_x
        y -= self.gnss_orig_y

        print("with origin applied %s %s" % (x, y))
        pix_xy = np.matmul(self.T, np.array([x, y]))
        print("foo %s" % pix_xy)

        return pix_xy[0] + self.pix_orig_x, pix_xy[1] + self.pix_orig_y

    def to_gnss(self, x, y):
        x -= self.pix_orig_x
        y -= self.pix_orig_y

        print("with origin applied %s %s" % (x, y))
        gnss_xy = np.matmul(self.iT, np.array([x, y]))

        return gnss_xy[0] + self.gnss_orig_x, gnss_xy[1] + self.gnss_orig_y



def gen_sol(gnss, pix):
    print("input")
    _dump(gnss, pix)

    # change gnss origin
    gnss_origin = gnss[0]
    print("using %s, %s as gnss origin" % gnss_origin)
    gnss = [tuple(map(sub, x, gnss_origin)) for x in gnss[1:]]

    # change pix origin
    pix_origin = pix[0]
    print("using %s, %s as pix origin" % pix_origin)
    pix = [tuple(map(sub, x, pix_origin)) for x in pix[1:]]

    _dump(gnss, pix)

    A = _make_A(gnss)
    B = _make_B(pix)

    vals = np.linalg.lstsq(A, B, rcond=None)[0]

    T = np.array([[vals[0], vals[1]],
                  [vals[2], vals[3]]])

    return Translate(gnss_origin, pix_origin, T)





