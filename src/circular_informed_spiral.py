import numpy as np
import gdspy
import argparse
import json
import os
from collections import deque

# Define the 8 directions for an octagon (0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°)
DIRECTIONS = deque([
    (-1, 0),   # 180° (left)
    (-1, -1),  # 225° (down-left)
    (0, -1),   # 270° (down)
    (1, -1),    # 315° (down-right)
    (1, 0),    # 0° (right)
    (1, 1),    # 45° (up-right)
    (0, 1),    # 90° (up)
    (-1, 1),   # 135° (up-left)
])

# Default parameters
DEFAULT_TRACE_WIDTH = 3  # um
DEFAULT_INNER_RADIUS = 20  # um
DEFAULT_NUM_TURNS = 4
DEFAULT_SPACING = 7 # um
DEFAULT_LAYER = 0
DEFAULT_DATATYPE = 0
DEFAULT_INITIAL_DIRECTION = DIRECTIONS[2]
def generate_octagon_spiral(
    cell, trace_width=DEFAULT_TRACE_WIDTH, 
    inner_radius=DEFAULT_INNER_RADIUS,
    num_turns=DEFAULT_NUM_TURNS,
    spacing=DEFAULT_SPACING,
    layer=DEFAULT_LAYER,
    datatype=DEFAULT_DATATYPE,
    initial_direction=DEFAULT_INITIAL_DIRECTION
):
    """
    Generate a spiral with octagonal shape using only segments that are
    parallel to x-axis, y-axis, or at 45-degree angles. Each octagon is
    centered within the next larger octagon.
    
    Parameters:
    -----------
    cell : gdspy.Cell
        The cell to add the spiral to
    trace_width : float
        Width of the spiral trace
    inner_radius : float
        Inner radius of the spiral
    num_turns : int
        Number of turns in the spiral
    spacing : float
        Spacing between adjacent turns
    layer : int
        Layer number for the polygon
    datatype : int
        Datatype for the polygon
    """
    
    assert initial_direction in DIRECTIONS, f"Invalid initial direction: {initial_direction}"

    starting_direction_idx = DIRECTIONS.index(initial_direction)
    print(f"starting_direction_idx: {starting_direction_idx}")
    ordered_directions = DIRECTIONS.copy()
    ordered_directions.rotate(-starting_direction_idx)#.tolist()
    print(f"ordered_directions: {ordered_directions}")
    # Starting point
    current_radius = inner_radius
    points = []
    x, y = 0, 0  # Start at the center
    
    #for radius in np.linspace(inner_radius, inner_radius + num_turns * (spacing + trace_width), 8*num_turns):
    COS_PI_8 = np.cos(np.pi/8)
    x = inner_radius*np.cos(3*np.pi/8 + np.pi/4 * starting_direction_idx)
    y = inner_radius*np.sin(3*np.pi/8 + np.pi/4 * starting_direction_idx) 
    print(f'starting point: {x}, {y}')
    for idx, step in enumerate(np.arange(0, num_turns, 1/8)):
        radius = inner_radius + step * (spacing + trace_width)
        next_radius = inner_radius + (step + 1/8) * (spacing + trace_width)/COS_PI_8
        
        #print(f"idx: {idx} step: {step} radius: {radius}")

        # bounding circle
        # path = gdspy.Round((0,0), radius, radius, layer=27, datatype=0)
        # cell.add(path)

        # Add the octagon side
        # path = gdspy.Polygon([
        #     (x-trace_width/2, y-trace_width/2),
        #     (x+trace_width/2, y-trace_width/2),
        #     (x+trace_width/2, y+trace_width/2),
        #     (x-trace_width/2, y+trace_width/2)],
        #     layer=37, datatype=0
        #     )
        #print(f"x: {x} y: {y}")
        path = gdspy.Text(f"{idx}", position=(x, y), size=1, layer=30, datatype=0)
        cell.add(path)
        pdx, pdy = ordered_directions[(idx-1) % len(ordered_directions)]
        dx, dy = ordered_directions[idx % len(ordered_directions)]
        ndx, ndy = ordered_directions[(idx+1) % len(ordered_directions)]
        print(f"dx: {dx} dy: {dy}")
        # Equation of circle cecntered at zero is:
        # x^2 + y^2 = radius^2
        # Equation of line is:
        # y = mx + b
        # where m is the slope and b is the y-intercept
        # m = dy/dx
        # b = y - mx

        if dx == 0:
            # vertical line
            #print(f"vertical line")
            xnext = x
            # y^2 +x^2 - next_radius^2 = 0
            quad_a = 1
            quad_b = 0
            quad_c = xnext**2 - next_radius**2

            yn1 = (-quad_b - np.sqrt(quad_b**2 - 4*quad_a*quad_c))/(2*quad_a)
            yn2 = (-quad_b + np.sqrt(quad_b**2 - 4*quad_a*quad_c))/(2*quad_a)

            # larger difference solution is the next y
            ynext = yn1 if abs(yn1 - y) > abs(yn2 - y) else yn2
            
        else:
            m = dy/dx
            b = y - m*x
            #print(f"m: {m} b: {b}")
            quad_a = (1+m**2)
            quad_b = 2*m*b
            quad_c = b**2 - next_radius**2
            # Quadratic formula:
            # x = (-b ± sqrt(b^2 - 4ac)) / 2a   
            xn1 = (-quad_b - np.sqrt(quad_b**2 - 4*quad_a*quad_c))/(2*quad_a)
            xn2 = (-quad_b + np.sqrt(quad_b**2 - 4*quad_a*quad_c))/(2*quad_a)

            # larger difference solution is the next x
            xnext = xn1 if abs(xn1 - x) > abs(xn2 - x) else xn2
            ynext = m*xnext + b
        

        if dx == 0 or dy == 0:
            vertex_angle = np.arctan2(pdy, pdx) + np.pi/2 + np.pi/8
            next_vertex_angle = np.arctan2(ndy, ndx)  + np.pi/2 - np.pi/8            
        else:
            vertex_angle = np.arctan2(dy, dx) + np.pi/2 - np.pi/8
            next_vertex_angle = np.arctan2(dy, dx) + np.pi/2 + np.pi/8    
        #vertex_angle = np.arctan2(y, x)
        #next_vertex_angle = np.arctan2(ynext, xnext)
                
        #print(f'y: {y} x: {x}')
        #print(f'next_y: {ynext} next_x: {xnext}')
        # points = np.around(np.array([
        #     (x-trace_width*np.cos(vertex_angle)/2,y-trace_width*np.sin(vertex_angle)/2),
        #     (xnext-trace_width*np.cos(next_vertex_angle)/2, ynext-trace_width*np.sin(next_vertex_angle)/2),
        #     (xnext+trace_width*np.cos(next_vertex_angle)/2, ynext+trace_width*np.sin(next_vertex_angle)/2),
        #     (x+trace_width*np.cos(vertex_angle)/2, y+trace_width*np.sin(vertex_angle)/2)]),3)
        points = np.around(np.array([
            (x,y),
            (xnext, ynext),
            (xnext+trace_width*np.cos(next_vertex_angle)/COS_PI_8, ynext+trace_width*np.sin(next_vertex_angle)/COS_PI_8),
            (x+trace_width*np.cos(vertex_angle)/COS_PI_8, y+trace_width*np.sin(vertex_angle)/COS_PI_8)]),3)
        #print(f"points: {points}")
        path = gdspy.Polygon(points, layer=37, datatype=0)
        cell.add(path)

        x = xnext
        y = ynext

    return cell

if __name__ == "__main__":
    # Create a new GDSII library and cell
    lib = gdspy.GdsLibrary()
    cell = lib.new_cell("octagon_spiral")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate an octagonal spiral")
    parser.add_argument("--trace_width", type=float, default=DEFAULT_TRACE_WIDTH, help="Width of the spiral trace")
    parser.add_argument("--inner_radius", type=float, default=DEFAULT_INNER_RADIUS, help="Inner radius of the spiral")
    parser.add_argument("--num_turns", type=int, default=DEFAULT_NUM_TURNS, help="Number of turns in the spiral")
    parser.add_argument("--spacing", type=float, default=DEFAULT_SPACING, help="Spacing between adjacent turns")
    parser.add_argument("--layer", type=int, default=DEFAULT_LAYER, help="Layer number for the polygon")
    parser.add_argument("--datatype", type=int, default=DEFAULT_DATATYPE, help="Datatype for the polygon")
    args = parser.parse_args()
    
    # Generate the spiral
    generate_octagon_spiral(
        cell,
        trace_width=args.trace_width,
        inner_radius=args.inner_radius,
        num_turns=args.num_turns,
        spacing=args.spacing,
        layer=args.layer,
        datatype=args.datatype
    )
    
    # Save the GDSII file
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "octagon_spiral.gds")
    lib.write_gds(output_file)
    print(f"Spiral saved to {output_file}")
    
    # Also save as SVG for visualization
    svg_file = os.path.join(output_dir, "octagon_spiral.svg")
    cell.write_svg(svg_file)
    print(f"SVG visualization saved to {svg_file}")
    
    # Show the cell in a GUI window
    gdspy.LayoutViewer(lib)
