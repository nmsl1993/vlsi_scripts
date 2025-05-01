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
DEFAULT_SPACING = 5 #um
POLYGON_NSIDES = 8 # Octagon
DEFAULT_VIA_SIDE_LENGTH = 0.36 #um
DEFAULT_VIA_SPACING = 1.06 #um
DEFAULT_ENTRY_EXIT_DISTANCE = 10 #um

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
    #   inner_radius: the inner radius of the spiral,
    #       defined as the distance from the center of the octagon to the center of the first trace
    #   num_turns: the number of turns in the spiral
    #   guard_ring_distance: the distance of the guard ring from the spiral 
    #   spacing: the spacing between the turns

    POLYGON_OUTER_ANGLE = (POLYGON_NSIDES - 2) * np.pi / POLYGON_NSIDES
    POLYGON_INNER_ANGLE = (np.pi - POLYGON_OUTER_ANGLE/2 - np.pi/2)*2
    vertex_angles = np.arange(np.pi/2, 2*np.pi+np.pi/2, POLYGON_INNER_ANGLE/2)
    vertex_normalized_radius = np.ones_like(vertex_angles) 
    vertex_normalized_radius[np.arange(0, len(vertex_angles)) % 2 == 0] = np.cos(np.pi/8)
    def generate_via_polygons(x, y, number_of_x_vias=2, number_of_y_vias=2, via_side_length=DEFAULT_VIA_SIDE_LENGTH, via_spacing=DEFAULT_VIA_SPACING):
        for nx in range(number_of_x_vias):
            for ny in range(number_of_y_vias):
                xx = x + (nx-(number_of_x_vias-1)/2)*via_spacing
                yy = y + (ny-(number_of_y_vias-1)/2)*via_spacing
                # via_points = np.array([
                #     (xx+via_side_length/2, yy+via_side_length/2),
                #     (xx+via_side_length/2, yy-via_side_length/2),
                #     (xx-via_side_length/2, yy-via_side_length/2),
                #     (xx-via_side_length/2, yy+via_side_length/2),
                # ])
                # segment = gdspy.Polygon(via_points, **process_config['vias'])
                segment = gdspy.Rectangle(
                    point1=(xx-via_side_length/2, yy-via_side_length/2), 
                    point2=(xx+via_side_length/2, yy+via_side_length/2), 
                    **process_config['vias']
                )
                cell.add(segment)  
    for coil_idx in range(2):
        for turn_idx in range(num_turns):
            turn_inner_radius = inner_radius + (2*turn_idx + coil_idx) * (spacing + trace_width)
            quad_range = range(4)
            if turn_idx == 0:
                print(f'coil_idx: {coil_idx}')
            if opposite_side_entry and coil_idx == 1 and turn_idx == 0:
                quad_range = [0,1]
            elif opposite_side_entry and coil_idx == 1 and turn_idx == num_turns - 1:
                quad_range = [2,3]
            for quad_idx in quad_range:
                points = []
                for radius, stride in [('inner', 1), ('outer', -1)]:
                    for angle_idx in range(4*quad_idx, 4*quad_idx + 5)[::stride]:
                        original_angle_idx = angle_idx
                        if opposite_side_entry and coil_idx == 1:
                            angle_idx = angle_idx + len(vertex_angles)//2
                        angle = vertex_angles[angle_idx % len(vertex_angles)]
                        octagon_radius = vertex_normalized_radius[angle_idx % len(vertex_normalized_radius)]
                        octagon_inner_radius = turn_inner_radius*vertex_normalized_radius[angle_idx % len(vertex_normalized_radius)]
                        #print(f'angle_idx: {angle_idx}, angle {angle}, angled {np.degrees(angle)}')
                        if angle_idx % 2 == 1:
                            octagon_outer_radius = octagon_inner_radius + trace_width/np.cos(np.pi/8)
                        else:
                         octagon_outer_radius = octagon_inner_radius + trace_width
                        # if quad_idx == 3 and angle_idx > 4*quad_idx and (coil_idx == 0 or not opposite_side_entry):
                        #     local_radius_y = vertex_normalized_radius[angle_idx % len(vertex_normalized_radius)]*(radius + 2*(spacing+trace_width))
                        #     local_radius_x = vertex_normalized_radius[angle_idx % len(vertex_normalized_radius)]*radius
                        # elif opposite_side_entry and coil_idx == 1 and quad_idx == 1 and angle_idx > 4*quad_idx:
                        #     local_radius_y = vertex_normalized_radius[angle_idx % len(vertex_normalized_radius)]*(radius + 2*(spacing+trace_width))
                        #     local_radius_x = vertex_normalized_radius[angle_idx % len(vertex_normalized_radius)]*radius
                        #else:
                        y_modifier = 0
                        if quad_idx == 3 and angle_idx >= 4*quad_idx  and (coil_idx == 0 or not opposite_side_entry):
                            y_modifier = 2*(spacing+trace_width)
                            if angle_idx == len(vertex_angles):
                                y_modifier = 2*(spacing+trace_width)*np.cos(np.pi/8) 
                        elif opposite_side_entry and coil_idx == 1 and quad_idx == 1 and angle_idx > 4*quad_idx:
                            y_modifier = 2*(spacing+trace_width)
                            if angle_idx == len(vertex_angles):
                                y_modifier = 2*(spacing+trace_width)*np.cos(np.pi/8)                             
                        if radius == 'inner':
                            local_radius_x = octagon_inner_radius
                            local_radius_y = octagon_inner_radius + y_modifier
                        else:
                            local_radius_x = octagon_outer_radius
                            local_radius_y = octagon_outer_radius + y_modifier
                        x2 = local_radius_x * np.cos(angle)   
                        y2 = local_radius_y * np.sin(angle)
                        points.append((x2, y2))
                segment = gdspy.Polygon(points, **process_config['M6'])
                cell.add(segment)
        # Draw entry/exit traces:
        if add_entry_exit_traces and opposite_side_entry:
            COS_PI_8 = np.cos(np.pi/8)
            coil_0_entry = np.array([-2*trace_width, inner_radius*COS_PI_8+trace_width/2])
            coil_1_entry = np.array([2*trace_width, -(inner_radius*COS_PI_8+trace_width/2 + (trace_width + spacing)*COS_PI_8)])# + 3/2*trace_width + spacing)])
            coil_0_exit = np.array([2*trace_width, inner_radius*COS_PI_8+trace_width/2 + 2*num_turns*(spacing+trace_width)*COS_PI_8])
            coil_1_exit = np.array([-2*trace_width, -(inner_radius*COS_PI_8+trace_width/2 + (2*num_turns-1)*(spacing+trace_width)*COS_PI_8)])


            def add_entry_exit_traces(coil_entry, y_direction, rectangle_length):
                if y_direction == 1:
                    rectangle_points = np.array([
                        (-trace_width/2, -trace_width/2),
                        (trace_width/2, -trace_width/2),
                        (trace_width/2, trace_width/2+rectangle_length),
                        (-trace_width/2, trace_width/2+rectangle_length)
                    ])
                else:
                    rectangle_points = np.array([
                        (-trace_width/2, -trace_width/2-rectangle_length),
                        (trace_width/2, -trace_width/2-rectangle_length),
                        (trace_width/2, trace_width/2),
                        (-trace_width/2, trace_width/2)
                    ])
                coil_points = rectangle_points.copy()
                coil_points[:,0] += coil_entry[0]
                coil_points[:,1] += coil_entry[1]
                segment = gdspy.Polygon(coil_points, **process_config['M5'])
                cell.add(segment)
                generate_via_polygons(x=coil_entry[0], y=coil_entry[1])
            
            max_radius = np.max(np.abs([coil_0_entry[1], coil_1_entry[1], coil_0_exit[1], coil_1_exit[1]]))

            add_entry_exit_traces(
                coil_0_entry, y_direction=1, 
                rectangle_length=(max_radius-np.abs(coil_0_entry[1])+DEFAULT_ENTRY_EXIT_DISTANCE)
            )
            add_entry_exit_traces(
                coil_1_entry, y_direction=-1, 
                rectangle_length=(max_radius-np.abs(coil_1_entry[1])+DEFAULT_ENTRY_EXIT_DISTANCE)
            )   
            add_entry_exit_traces(
                coil_0_exit, y_direction=1, 
                rectangle_length=(max_radius-np.abs(coil_0_exit[1])+DEFAULT_ENTRY_EXIT_DISTANCE)
            )
            add_entry_exit_traces(
                coil_1_exit, y_direction=-1, 
                rectangle_length=(max_radius-np.abs(coil_1_exit[1])+DEFAULT_ENTRY_EXIT_DISTANCE)
            )   
 
            
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
    suffix = f'tw{args.trace_width}_ir{args.inner_radius}_nt{args.num_turns}_s{args.spacing}'
    # Save as GDS file
    lib.write_gds(f'{os.path.join(os.path.dirname(__file__), "..", "outputs", f"spiral_transformer.{suffix}.gds")}')
    print(f'{os.path.join(os.path.dirname(__file__), "..", "outputs", f"spiral_transformer.{suffix}.gds")}')
    # Save as SVG file for visualization
    cell.write_svg(f'{os.path.join(os.path.dirname(__file__), "..", "outputs", f"spiral_transformer.{suffix}.svg")}')
    
    # Show the cell in a GUI window
    gdspy.LayoutViewer(lib)