import phidl
import numpy as np
import gdspy
import argparse
import json
import os
# using parameters from cadence initially:
DEFAULT_TRACE_WIDTH = 3 #um
DEFAULT_INNER_RADIUS = 20 #um
DEFAULT_NUM_TURNS = 3
DEFAULT_GUARD_RING_DISTANCE = 50 #um
DEFAULT_SPACING = 3 #um
POLYGON_NSIDES = 8 # Octagon

process_config = json.load(open(os.path.join(os.path.dirname(__file__), 'configs/my_process.json')))
print(process_config)
def generate_spiral_transformer(
    cell, trace_width, inner_radius,
    num_turns, guard_ring_distance,
    spacing, opposite_side_entry, add_entry_exit_traces):
    # Generates a spiral transformer with the given parameters
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
    vertex_angles = np.arange(np.pi/2, 2*np.pi+np.pi/2, POLYGON_INNER_ANGLE/2)
    vertex_normalized_radius = np.ones_like(vertex_angles) 
    vertex_normalized_radius[np.arange(0, len(vertex_angles)) % 2 == 0] = np.cos(np.pi/8)
    
    for coil_idx in range(2):
        _entry_inner = ()
        _entry_outer = ()
        _exit_inner = ()
        _exit_outer = ()
        for turn_idx in range(num_turns):
            trace_inner_radius = inner_radius + (2*turn_idx + coil_idx) * (spacing + trace_width)
            trace_outer_radius = trace_inner_radius + trace_width
            quad_range = range(4)
            if opposite_side_entry and coil_idx == 1 and turn_idx == 0:
                quad_range = [0,1]
            elif opposite_side_entry and coil_idx == 1 and turn_idx == num_turns - 1:
                quad_range = [2,3]
            for quad_idx in quad_range:
                points = []
                for radius, stride in [(trace_inner_radius, 1), (trace_outer_radius, -1)]:
                    for angle_idx in range(4*quad_idx, 4*quad_idx + 5)[::stride]:
                        original_angle_idx = angle_idx
                        if opposite_side_entry and coil_idx == 1:
                            angle_idx = angle_idx + len(vertex_angles)//2
                        angle = vertex_angles[angle_idx % len(vertex_angles)]
                        if quad_idx == 3 and angle_idx > 4*quad_idx and (coil_idx == 0 or not opposite_side_entry):
                            local_radius_y = vertex_normalized_radius[angle_idx % len(vertex_normalized_radius)]*(radius + 2*(spacing+trace_width))
                            local_radius_x = vertex_normalized_radius[angle_idx % len(vertex_normalized_radius)]*radius
                        elif opposite_side_entry and coil_idx == 1 and quad_idx == 1 and angle_idx > 4*quad_idx:
                            local_radius_y = vertex_normalized_radius[angle_idx % len(vertex_normalized_radius)]*(radius + 2*(spacing+trace_width))
                            local_radius_x = vertex_normalized_radius[angle_idx % len(vertex_normalized_radius)]*radius
                        else:
                            local_radius_x = vertex_normalized_radius[angle_idx % len(vertex_normalized_radius)]*radius
                            local_radius_y = vertex_normalized_radius[angle_idx % len(vertex_normalized_radius)]*radius
                        if turn_idx == 0 and original_angle_idx == 4*quad_idx+4:
                            if stride == 1:
                                _entry_inner = np.array([local_radius_x, local_radius_y])
                            else:
                                _entry_outer = np.array([local_radius_x, local_radius_y])
                        elif turn_idx == num_turns - 1 and original_angle_idx == 4*quad_idx + 4:
                            if stride == 1:
                                _exit_inner = np.array([local_radius_x, local_radius_y])
                            else:
                                _exit_outer = np.array([local_radius_x, local_radius_y])
                        x2 = np.around(local_radius_x * np.cos(angle), 10)    
                        y2 = np.around(local_radius_y * np.sin(angle), 10)
                        points.append((x2, y2))
                segment = gdspy.Polygon(points, **process_config['M6'])
                cell.add(segment)
        # Draw entry/exit traces:
        if add_entry_exit_traces and opposite_side_entry:
            rectangle_length = inner_radius + num_turns*(spacing+trace_width)
            # Coil 0
            rectangle_points = np.array([
                (-trace_width/2, -trace_width/2),
                (trace_width/2, -trace_width/2),
                (trace_width/2, trace_width/2+rectangle_length),
                (-trace_width/2, trace_width/2+rectangle_length)
            ])
            coil_0_points = rectangle_points.copy()
            coil_0_points[:,1] += inner_radius
            coil_0_points[:,0] -= 2*trace_width
            segment = gdspy.Polygon(coil_0_points, **process_config['M5'])
            cell.add(segment)
            # Coil 1
            coil_1_points = rectangle_points.copy()
            coil_1_points[:,1] -= (inner_radius + trace_width+spacing+rectangle_length)
            coil_1_points[:,0] += 2*trace_width
            segment = gdspy.Polygon(coil_1_points, **process_config['M5'])
            cell.add(segment)   
            
    #outer_radius = inner_radius + (num_turns - 1) * spacing
if __name__ == "__main__":
    # The GDSII file is called a library, which contains multiple cells.
    lib = gdspy.GdsLibrary()
    # Geometry must be placed in cells.
    cell = lib.new_cell('spiral_transformer_python')

    parser = argparse.ArgumentParser(description='Generate a spiral transformer')
    parser.add_argument('--trace_width', type=float, default=DEFAULT_TRACE_WIDTH, help='Width of the spiral')
    parser.add_argument('--inner_radius', type=float, default=DEFAULT_INNER_RADIUS, help='Inner radius of the spiral')
    parser.add_argument('--num_turns', type=int, default=DEFAULT_NUM_TURNS, help='Number of turns in the spiral')
    parser.add_argument('--guard_ring_distance', type=float, default=DEFAULT_GUARD_RING_DISTANCE, help='Distance of the guard ring from the spiral')
    parser.add_argument('--spacing', type=float, default=DEFAULT_SPACING, help='Spacing between the turns')
    parser.add_argument('--same_side_entry', action='store_false', default=False, help='Whether to have the second coil enter from the opposite side')
    parser.add_argument('--no_entry_exit_traces', action='store_false', default=False, help='Do not add entry/exit traces')

    args = parser.parse_args()

    generate_spiral_transformer(
        cell, args.trace_width, args.inner_radius,
        args.num_turns, args.guard_ring_distance,
        args.spacing, not args.same_side_entry, not args.no_entry_exit_traces
    )
    # Save as GDS file
    lib.write_gds('outputs/spiral_transformer.gds')
    # Save as SVG file for visualization
    cell.write_svg('outputs/ spiral_transformer.svg')
    
    # Show the cell in a GUI window
    gdspy.LayoutViewer(lib)