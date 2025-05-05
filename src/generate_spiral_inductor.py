import phidl
import numpy as np
import gdspy
import argparse
import json
import os
# using parameters from cadence initially:
DEFAULT_TRACE_WIDTH = 3 #um
DEFAULT_INNER_RADIUS = 20 #um
DEFAULT_NUM_TURNS = 1
DEFAULT_GUARD_RING_DISTANCE = 50 #um
DEFAULT_SPACING = 8 #um
POLYGON_NSIDES = 8 # Octagon

process_config = json.load(open(os.path.join(os.path.dirname(__file__), 'configs/my_process.json')))
print(process_config)
def generate_spiral_inductor(cell, trace_width, inner_radius, num_turns, guard_ring_distance, spacing):
    # Generates a spiral inductor with the given parameters
    # Define transition to be at bottom of octagon and entry/exit to be at top of octagon   
    
    # Parameters:
    #   cell: the cell to add the spiral to
    #   width: the width of the spiral
    #   inner_radius: the inner radius of the spiral
    #   num_turns: the number of turns in the spiral
    #   guard_ring_distance: the distance of the guard ring from the spiral 
    #   spacing: the spacing between the turns

    POLYGON_OUTER_ANGLE = (POLYGON_NSIDES - 2) * np.pi / POLYGON_NSIDES
    POLYGON_INNER_ANGLE = (np.pi - POLYGON_OUTER_ANGLE/2 - np.pi/2)*2
    vertex_indices = np.arange(4, 4+(POLYGON_NSIDES*2)) % (POLYGON_NSIDES*2)
    # Drop vertices that are multiple of 45 degrees
    vertex_indices = vertex_indices[np.arange(0, len(vertex_indices)) % 4 != 2]
    print(f'vertex_indices: {vertex_indices}')
    vertex_angles = np.pi/POLYGON_NSIDES * vertex_indices

    print(len(vertex_angles))
    vertex_normalized_radius = np.ones_like(vertex_angles) 
    vertex_normalized_radius[vertex_indices % 2 == 0] = np.cos(np.pi/8)
   
    print(f'vertex_angles: {np.degrees(vertex_angles)}')

    for turn_idx in range(num_turns):
        print(f'\nturn_idx: {turn_idx}\n')
        for quad_idx in range(4):
            points = []
            print(f'quad_idx: {quad_idx}')
            for radius_modifier, stride in [(-trace_width/2, 1), (trace_width/2, -1)]:
                if stride == 1:
                    print(f'INNER:\n')
                else:
                    print(f'OUTER:\n')
                for angle_idx in range(3*quad_idx, 3*quad_idx + 4)[::stride]:
                    angle = vertex_angles[angle_idx % len(vertex_angles)]
                    fractional_turn_idx = turn_idx+ quad_idx/4 + (angle_idx > (3*quad_idx+1))/4
                    radius = (inner_radius + fractional_turn_idx * (spacing + trace_width) + radius_modifier)*vertex_normalized_radius[angle_idx % len(vertex_normalized_radius)]
                    print(f'''angle_idx: {angle_idx},angle: {np.degrees(angle)}, radius: {radius},'''
                          f'''turn_idx: {turn_idx}, quad_idx: {quad_idx}, fractional_turn_idx: {fractional_turn_idx}''')

                    x2 = radius * np.cos(angle)#np.around(local_radius_x * np.cos(angle), 10)    
                    y2 = radius * np.sin(angle) #np.around(local_radius_y * np.sin(angle), 10)
                    points.append((x2, y2))
            print(f'points: \n{np.around(np.array(points), 10)}')
            segment = gdspy.Polygon(points, **process_config['M6'])
            cell.add(segment)


    
    #outer_radius = inner_radius + (num_turns - 1) * spacing
if __name__ == "__main__":
    # The GDSII file is called a library, which contains multiple cells.
    lib = gdspy.GdsLibrary()
    # Geometry must be placed in cells.
    cell = lib.new_cell('spiral_inductor_python')

    parser = argparse.ArgumentParser(description='Generate a spiral inductor')
    parser.add_argument('--trace_width', type=float, default=DEFAULT_TRACE_WIDTH, help='Width of the spiral')
    parser.add_argument('--inner_radius', type=float, default=DEFAULT_INNER_RADIUS, help='Inner radius of the spiral')
    parser.add_argument('--num_turns', type=int, default=DEFAULT_NUM_TURNS, help='Number of turns in the spiral')
    parser.add_argument('--guard_ring_distance', type=float, default=DEFAULT_GUARD_RING_DISTANCE, help='Distance of the guard ring from the spiral')
    parser.add_argument('--spacing', type=float, default=DEFAULT_SPACING, help='Spacing between the turns')
    args = parser.parse_args()

    generate_spiral_inductor(cell, args.trace_width, args.inner_radius, args.num_turns, args.guard_ring_distance, args.spacing)
    # Save as GDS file
    lib.write_gds('outputs/spiral_inductor.gds')
    # Save as SVG file for visualization
    cell.write_svg('outputs/ spiral_inductor.svg')
    
    # Show the cell in a GUI window
    gdspy.LayoutViewer(lib)