"""
ProteinArea.py
A package to calculate time-series protein area profile of MD data.

Use 2D voronoi cells to create realistic protein area with protein embedded 
in lipids. The code assumes the membrane in MD data is oriented in X-Y plane.

"""

import MDAnalysis as mda
import numpy as np
import shapely.geometry as geo

from MDAnalysis.analysis.base import AnalysisBase
from scipy.spatial import Voronoi
from scipy.spatial import voronoi_plot_2d
from numpy.linalg import norm


def calc_area_per_slice(ag, nopbc=False):
    '''
    nopbc: flag to turn off pbc images, set to False.
    '''

    # create coordinates
    if nopbc:
        points_p, points_np = voronoi_pbc(ag, nopbc)
        points = np.concatenate((points_p, points_np))
    
    else:
        points_p, points_np, points_pbc = voronoi_pbc(ag)
        points = np.concatenate((points_p, points_np, points_pbc))

    # if no protein atom is in this slice, return 0
    p_size = len(points_p)

    if p_size == 0:
        return 0.0

    # do voronoi
    vor = Voronoi(points)

    # calculate area
    area_per_slice = 0
    for region_index in vor.point_region[:p_size]:
        region_vertices = vor.vertices[vor.regions[region_index]]
        area_per_cell = geo.Polygon(region_vertices).area
        area_per_slice += area_per_cell

    return area_per_slice


def voronoi_pbc(ag, nopbc=False):
    '''
    Create pbc images for ag slice. 
    For current setup, there are in total 8 images as we are doing voronoi 
    in 2D

    nopbc: flag to turn off pbc images, set to False.
    '''
    x, y, z = ag.dimensions[0:3]

    # create protein and non-protein coordinates
    points_p = ag.select_atoms('protein').positions[:, 0:2]
    points_np = ag.select_atoms('not protein').positions[:, 0:2]

    if nopbc:
        return points_p, points_np

    # create 8 pbc images
    pbc_arrays = np.array(
        [
            [x, 0],
            [x, y],
            [x, -y],
            [-x, 0],
            [-x, y],
            [-x, -y],
            [0, y],
            [0, -y]
        ]
    )

    # create pbc coordinates
    points_pbc = ag.copy().atoms.positions[:, 0:2] + pbc_arrays[0]

    for pbc_array in pbc_arrays[1:]:
        pos_pbc = ag.copy().atoms.positions[:, 0:2] + pbc_array
        points_pbc = np.concatenate((points_pbc, pos_pbc))

    return points_p, points_np, points_pbc


class ProteinArea(AnalysisBase):
    '''
    zmin:  estimated zmin, should be lower than 
        the minimal z of the whole traj. Default=0
    zmax:  estimated zmax, should be higher 
        than the maximal z of the whole traj. Default=150
    layer: thickness of a layer. default=0.5
    nopbc: flag to turn off pbc images, set to False.
    '''
    def __init__(self, atomgroup, zmin=0, zmax=150, layer=0.5, nopbc=False, **kwargs):
        super(ProteinArea, self).__init__(atomgroup.universe.trajectory,
                                          **kwargs)
        self._zmin = zmin
        self._zmax = zmax
        self._layer = layer
        self._ag = atomgroup
        self._nopbc = nopbc

    def _prepare(self):
        self.results.area_per_frame = []

        # slicing a frame
        self._slices = np.arange(self._zmin, self._zmax, self._layer)



    def _single_frame(self):
        for slice_index, slice in enumerate(self._slices[:-1]):
            slice = self._ag.select_atoms('prop z > ' + 
                                          str(self._slices[slice_index]) + 
                                          ' and prop z < ' + 
                                          str(self._slices[slice_index+1]))
            self.results.area_per_frame.append(
                np.array(calc_area_per_slice(slice, self._nopbc))
                )

    def _conclude(self):
        self.results.area_per_frame = np.array(self.results.area_per_frame)
        