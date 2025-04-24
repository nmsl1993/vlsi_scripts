import phidl
import numpy
import gdspy

# The GDSII file is called a library, which contains multiple cells.
lib = gdspy.GdsLibrary()

# Geometry must be placed in cells.
cell = lib.new_cell('FIRST')

# Create the geometry (a single rectangle) and add it to the cell.
path2 = gdspy.Path(0.5, (0, 0))

# Start the path with a smooth Bezier S-curve
path2.bezier([(0, 5), (5, 5), (5, 10)])

# We want to add a spiral curve to the path.  The spiral is defined
# as a parametric curve.  We make sure spiral(0) = (0, 0) so that
# the path is continuous.
def spiral(u):
    r = 4 - 3 * u
    theta = 5 * u * numpy.pi
    x = r * numpy.cos(theta) - 4
    y = r * numpy.sin(theta)
    return (x, y)

# It is recommended to also define the derivative of the parametric
# curve, otherwise this derivative must be calculated nummerically.
# The derivative is used to define the side boundaries of the path,
# so, in this case, to ensure continuity with the existing S-curve,
# we make sure the the direction at the start of the spiral is
# pointing exactly upwards, as if is radius were constant.
# Additionally, the exact magnitude of the derivative is not
# important; gdspy only uses its direction.
def dspiral_dt(u):
    theta = 5 * u * numpy.pi
    dx_dt = -numpy.sin(theta)
    dy_dt = numpy.cos(theta)
    return (dx_dt, dy_dt)

# Add the parametric spiral to the path
path2.parametric(spiral, dspiral_dt)
cell.add(path2)

# Save the library in a file called 'first.gds'.
lib.write_gds('outputs/first.gds')

# Optionally, save an image of the cell as SVG.
cell.write_svg('outputs/first.svg')

# Display all cells using the internal viewer.
gdspy.LayoutViewer(lib)

# path2 = gdspy.Path(0.5, (0, 0))

# # Start the path with a smooth Bezier S-curve
# path2.bezier([(0, 5), (5, 5), (5, 10)])

# # We want to add a spiral curve to the path.  The spiral is defined
# # as a parametric curve.  We make sure spiral(0) = (0, 0) so that
# # the path is continuous.
# def spiral(u):
#     r = 4 - 3 * u
#     theta = 5 * u * numpy.pi
#     x = r * numpy.cos(theta) - 4
#     y = r * numpy.sin(theta)
#     return (x, y)
# import gdspy
# # It is recommended to also define the derivative of the parametric
# # curve, otherwise this derivative must be calculated nummerically.
# # The derivative is used to define the side boundaries of the path,
# # so, in this case, to ensure continuity with the existing S-curve,
# # we make sure the the direction at the start of the spiral is
# # pointing exactly upwards, as if is radius were constant.
# # Additionally, the exact magnitude of the derivative is not
# # important; gdspy only uses its direction.
# def dspiral_dt(u):
#     theta = 5 * u * numpy.pi
#     dx_dt = -numpy.sin(theta)
#     dy_dt = numpy.cos(theta)
#     return (dx_dt, dy_dt)

# # Add the parametric spiral to the path
# path2.parametric(spiral, dspiral_dt)