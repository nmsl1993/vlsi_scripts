import phidl
import numpy as np
import gdspy
import argparse

# using parameters from cadence initially:
DEFAULT_TRACE_WIDTH = 3 #um
DEFAULT_INNER_RADIUS = 30 #um
DEFAULT_NUM_TURNS = 3
DEFAULT_GUARD_RING_DISTANCE = 50 #um
DEFAULT_SPACING = 3 #um



def generate_spiral_inductor(trace_width, inner_radius, num_turns, guard_ring_distance, spacing):
    # Generates a spiral inductor with the given parameters
    # Define transition to be at bottom of octagon and entry/exit to be at top of octagon   
    
    # Parameters:
    #   cell: the cell to add the spiral to
    #   width: the width of the spiral
    #   inner_radius: the inner radius of the spiral
    #   num_turns: the number of turns in the spiral
    #   guard_ring_distance: the distance of the guard ring from the spiral 
    #   spacing: the spacing between the turns
    
    # The GDSII file is called a library, which contains multiple cells.
    lib = gdspy.GdsLibrary()
    # Geometry must be placed in cells.
    cell = lib.new_cell('spiral_inductor_python')

    for turn_idx in range(num_turns):
        trace_inner_radius = inner_radius + turn_idx * (spacing + trace_width)
        trace_outer_radius = trace_inner_radius + trace_width
        # Draw octagon for inner radius
        for quad_idx in [0, 2, 4, 6]:
            points = []
            for radius, stride in [(trace_inner_radius, 1), (trace_outer_radius, -1)]:
                for angle_idx in range(quad_idx, quad_idx + 3)[::stride]:
                    angle = angle_idx * np.pi / 4 + np.pi / 8
                    x2 = np.around(radius * np.cos(angle), 10)    
                    y2 = np.around(radius * np.sin(angle), 10)
                    points.append((x2, y2))
        
            segment = gdspy.Polygon(points)
            cell.add(segment)
    # Save as GDS file
    lib.write_gds('outputs/spiral_inductor.gds')
    
    # Save as SVG file for visualization
    cell.write_svg('outputs/ spiral_inductor.svg')
    
    # Show the cell in a GUI window
    gdspy.LayoutViewer(lib)
    
    #outer_radius = inner_radius + (num_turns - 1) * spacing
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a spiral inductor')
    parser.add_argument('--trace_width', type=float, default=DEFAULT_TRACE_WIDTH, help='Width of the spiral')
    parser.add_argument('--inner_radius', type=float, default=DEFAULT_INNER_RADIUS, help='Inner radius of the spiral')
    parser.add_argument('--num_turns', type=int, default=DEFAULT_NUM_TURNS, help='Number of turns in the spiral')
    parser.add_argument('--guard_ring_distance', type=float, default=DEFAULT_GUARD_RING_DISTANCE, help='Distance of the guard ring from the spiral')
    parser.add_argument('--spacing', type=float, default=DEFAULT_SPACING, help='Spacing between the turns')
    args = parser.parse_args()

    generate_spiral_inductor(args.trace_width, args.inner_radius, args.num_turns, args.guard_ring_distance, args.spacing)
