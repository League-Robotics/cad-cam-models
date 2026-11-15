"""Helpers for the labelled 2D drawings: cut or project an OpenSCAD mesh and dimension it.

Each part's *_pics.py exports its STL with OpenSCAD, loads it with trimesh and
draws with these. `axes` picks which model axes become the screen's x and y,
e.g. (0, 2) for a front view (x right, z up).
"""
import numpy as np
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
from shapely.geometry import Polygon
from shapely.ops import unary_union


def section_geom(mesh, origin, normal, axes):
    """A planar cut as shapely geometry with its holes (loops combined even-odd)."""
    s = mesh.section(plane_origin=origin, plane_normal=normal)
    g = Polygon()
    for poly in (s.discrete if s is not None else []):
        g = g.symmetric_difference(Polygon(poly[:, list(axes)]).buffer(0))
    return g


def silhouette(mesh, axes):
    """The mesh's outline seen along the axis not in `axes`: the union of its projected triangles."""
    tri = mesh.vertices[mesh.faces][:, :, list(axes)]
    e1, e2 = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    keep = np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]) > 1e-9
    return unary_union([Polygon(t) for t in tri[keep]])


def draw_geom(ax, g, color, alpha=0.45, lw=1.0):
    """Fill shapely polygons, holes left open."""
    for p in getattr(g, "geoms", [g]):
        if p.is_empty or not hasattr(p, "exterior"):
            continue
        rings = [np.asarray(p.exterior.coords)] + [np.asarray(r.coords) for r in p.interiors]
        verts = np.concatenate(rings)
        codes = np.concatenate([[MPath.MOVETO] + [MPath.LINETO] * (len(r) - 2) + [MPath.CLOSEPOLY] for r in rings])
        ax.add_patch(PathPatch(MPath(verts, codes), fc=color, alpha=alpha, ec="none"))
        for r in rings:
            ax.plot(r[:, 0], r[:, 1], color=color, lw=lw)


def dim(ax, p0, p1, text, off=(0, 0), color="#222"):
    ax.annotate("", p0, p1, arrowprops=dict(arrowstyle="<->", color=color, lw=1, shrinkA=0, shrinkB=0))
    m = ((p0[0] + p1[0]) / 2 + off[0], (p0[1] + p1[1]) / 2 + off[1])
    ax.text(*m, text, ha="center", va="center", fontsize=10, color=color,
            bbox=dict(fc="white", ec="none", pad=1.0))


def label(ax, xy, text, at, color="#222"):
    ax.annotate(text, xy, at, fontsize=10, color=color, ha="center", va="center",
                arrowprops=dict(arrowstyle="-", color=color, lw=0.8), bbox=dict(fc="white", ec=color, lw=0.5, pad=2))
