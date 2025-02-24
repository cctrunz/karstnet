import os
import networkx as nx
import numpy as np
from shapely.geometry import Point, LineString



def to_shp(positions,links,crs,outputdir='',name='', type='graph'):
    '''
    Transform graph data into an esri shapefile. Function written by Ana Tanaka
    crs OxBelHa: 'EPSG:32616'

    positions: dict (id:[x,y,z])

    links: list of list of links id
    '''
    import geopandas as gpd
    
    if type == 'nodes':
        node_data = {'id': list(positions.keys()), 'geometry': [Point(pos) for pos in positions.values()]}
        node_gdf = gpd.GeoDataFrame(node_data, crs=crs)
        node_gdf.to_file(os.path.join(outputdir,f'{name}nodes.shp'))

    if type == 'edges':
        edge_data = []
        for u, v in links:
            edge_data.append({'geometry': LineString([positions[u], positions[v]]), 'source': u, 'target': v})

        edge_gdf = gpd.GeoDataFrame(edge_data, crs=crs)   
        edge_gdf.to_file(os.path.join(outputdir,f'{name}edges.shp'))


def graph_to_branches(G):
    """Breaks down networkx graph into individual branches, by creating new points with unique value index at interesections.
    This was conceived by Nina. for the purpose of the gocad export, which requires to loop through each branch.
    This creates as many connected components as there is branches.
    What it does is that it looks at each intersection (node degree >2) and disconnect (randomly) at the intersection.
    To disconnect, it take randomly a segment, remove it and recreate a segment at the same spot but with a different name
    For example, at an intersection of degree 3, it will only keep 2 segments attached and detach one segement. 

    Args:
        G (networkx Graph): 
            a graph containing values of position, connected_component_number, and intersection

    Returns:
        networkx Graph: separated in branches. 
    """    
    def add_cc_attribute(G):
        """_summary_

        Parameters
        ----------
        G : networkx graph
            adds a number as an attribute for all the connected components, from 0 to i (i is the number of connected components)
            This is useful for gocad plotting for example
        """
        id_cc = []
        value_cc = []
        
        for i,cc in enumerate(nx.connected_components(G)):
            id_cc += list(cc)
            value_cc += [i] * len(cc)
        
        cc_number = dict(zip(id_cc, value_cc))
        nx.set_node_attributes(G, cc_number, 'connected_component_number') 

    #!!!here we should find a way to add any attrtibutes to the new create node number!!!
    #and create atoms to link points at branches intersection
    #BREAK THE GRAPH IN SINGLE BRANCHES
    max_value = max(G.nodes) 
    H = G.copy()

    # add connected component number to the graph
    add_cc_attribute(H)

    #loop through all nodes with degree larger than 2
    for intersection in [node for node,degree in dict(H.degree()).items() if degree >2]:
        #loop through all the neighbours minus the first two
        for node in [n for n in H.neighbors(intersection)][2:]:
            #set the new id for the new node
            max_value += 1  
            #create a new node at the intersection
            H.add_node(max_value,   pos=H.nodes('pos')[intersection], 
                                    connected_component_number=H.nodes('connected_component_number')[intersection],
                                    intersection=intersection)  
            #create an edge that connects the new node
            H.add_edge(max_value,node) 
            #remove the old ege
            H.remove_edge(intersection,node)      
    return H



def export_to_gocad(G, 
                    data_type = 'lines', #or 'points'
                    properties = [], #['cs_height', 'cs_width']
                    nodata_value = '-999999999',
                    name = 'graph_gocad_export',
                    node_id = [], #list of nodes id to export
                    pos_attr = 'pos'
                    ):
    """Export networkx graph data into a format readable by Gocad (.pl).
    This export requires x,y,z coordinate information attached as an attribute on each node on graph as a list of [x,y,z]
    It is possible to only give a few points or the entire dataset. It is also possible to add several properties.

    idea for improvement: 
    1. instead of having to attached x,y,z to the graph, give a dictionnary into the function??
    2. 


    Parameters
    ----------
    G : networkx graph
        Graph with coordinates position
    data_type : str, optional
        Choose data type between 'lines' and 'points', by default 'lines'
    properties : list of string(s)
        List containing the name of all the graph attributes to add to the Gocad output, by default []
        For now, the properties have to be a single value per node. 
    nodata_value : string
        by default '-999999999'
    name : str, optional
        path and name of the file to save. The extension is .pl , by default 'graph_gocad_export'
    node_id : list of node id, optional
        List of node id to use for the export, by default []
        If [] then the entire graph is selected
    pos_attr : str, optional
        name of the attribute containing the list of coordinates, by default 'pos'

    returns:
    --------
    saves a .pl file readable in Gocad
    """
    



    #the properties have to be a single value per node
    nodata_string = 'NO_DATA_VALUES ' + " ".join(str(item) for item in [nodata_value] * (len(properties)+3))
    
    if data_type=='points':
        header = 'GOCAD VSet 1.0'
        header_dataset = 'SUBVSET'
        
        #nodes
        if node_id == []:
            nodes = G.nodes
        else:
            nodes = node_id

        dataset = []

        for node in nodes:               
            #write coordinate string ex: '-6.53 -10.24 -28.11'
            # print(G.nodes('pos')[node])
            string_coordinates = " ".join(str(item) for item in G.nodes('pos_attr')[node])
            #write attribute string ex: 'att1 att2 atti'
            string_attribute = ''

            # string_id = " ".join(str(item) for item in nodes)
            
            for attribute in properties:
                if G.nodes(attribute)[node] is not None:
                    string_attribute += str(G.nodes(attribute)[node]) + ' '
                else:
                    # in the case there is no data
                    string_attribute += nodata_value
            
            #create a list of lines containing the notes attributes  
            dataset.append('PVRTX '+ str(node) +  ' ' + string_coordinates + ' ' + str(node) + ' ' + string_attribute)

        #write the lines
        lines = [   header, 
                'HEADER{',
                'name:' + name ,
                '}',
                'GOCAD_ORIGINAL_COORDINATE_SYSTEM',
                'ZPOSITIVE Elevation',
                'END_ORIGINAL_COORDINATE_SYSTEM',
                'PROPERTIES ID ' + " ".join(str(item) for item in properties),  
                nodata_string,
                header_dataset] + dataset + ['END']
    
    if data_type=='lines':
        header = 'GOCAD PLine 1'
        header_dataset = ''
        
        H = graph_to_branches(G)
        
        #write lines containing pline information
        #Gocad only read the pline right by single branch, with points in the right order
        dataset = []
        if nx.is_connected(H) == False:
            #iterate through the connectec components to find nodes where disconnection occured
            #search for the nodes that used to be degree >1 and are now degree 1.
            for i, subgraph_index in enumerate(nx.connected_components(H)):
                subgraph = nx.subgraph(H, subgraph_index)
                # print(subgraph)
                #segments
                seg = []
                nodes_start_end = [node for node,degree in dict(subgraph.degree()).items() if degree ==1]
                # print(nodes_start_end)

                #make sure its not a loop
                #in the case of a segment in the form of a loop, 
                # here will be no node of degree 1, so we replace by the first node in the list
                if nodes_start_end:
                    for path in nx.all_simple_edge_paths(subgraph, nodes_start_end[0],nodes_start_end[1]):
                        for edge in path:   
                            # print(edge) 
                            seg.append(" ".join(str(item) for item in edge))              
                            #nodes
                else:
                    #create a new node at the intersection
                    #take a random node in the loop:
                    intersection = list(subgraph.nodes())[0]
                    max_value = np.array(G.nodes()).max()
                    subgraph = subgraph.copy()
                    subgraph.add_node(max_value,   pos=subgraph.nodes(pos_attr)[intersection], 
                                            connected_component_number=subgraph.nodes('connected_component_number')[intersection],
                                            intersection=intersection)  
                    #create an edge that connects the new node
                    node = list(subgraph.neighbors(intersection))[0]
                    subgraph.add_edge(max_value,node) 
                    #remove the old ege
                    subgraph.remove_edge(intersection,node)  

                    seg = []
                    nodes_start_end = [node for node,degree in dict(subgraph.degree()).items() if degree ==1]

                    for path in nx.all_simple_edge_paths(subgraph, nodes_start_end[0],nodes_start_end[1]):
                        for edge in path:   
                            # print(edge) 
                            seg.append(" ".join(str(item) for item in edge))              
                            #nodes

                
                pvrtx = []
                for node in nx.shortest_path(subgraph, source=nodes_start_end[0], target=nodes_start_end[1]):               
                    #write coordinate string ex: '-6.53 -10.24 -28.11'
                    string_coordinates = " ".join(str(item) for item in subgraph.nodes(pos_attr)[node])
                    #write attribute string ex: 'att1 att2 atti'
                    string_attribute = ''
                    
                    for attribute in properties:
                        if subgraph.nodes(attribute)[node] is not None:
                            string_attribute += str(subgraph.nodes(attribute)[node]) + ' '
                        else:
                            # in the case there is no data
                            print('no properties for node: ', node )
                            string_attribute += nodata_value
                    
                    #create a list of lines  
                    pvrtx.append('PVRTX '+ str(node) +  ' ' + string_coordinates + ' ' + string_attribute)
                # create each branch text    
                dataset += ['ILINE'] + pvrtx + seg
           
     
        lines = [   header, 
                    'HEADER{',
                    'name:' + name ,
                    '}',
                    'GOCAD_ORIGINAL_COORDINATE_SYSTEM',
                    'ZPOSITIVE Elevation',
                    'END_ORIGINAL_COORDINATE_SYSTEM',
                    'PROPERTIES ' + " ".join(str(item) for item in properties),  
                    nodata_string,
                    header_dataset] + dataset + ['END']
               
    with open(name + '.pl', 'w') as f:
        f.write('\n'.join(lines))



def find_disconnected_node(G, H):
    """_summary_

    Parameters
    ----------
    G : networkx graph
        Graph exported from therion, containing all the data
    H : networkx graph
        Graph without the surface and duplicate shots

    Returns
    -------
    _type_
        list of disconnected node ids
    """    
    # G_raw = load_raw_therion_data(basename)    
    # G = load_therion_without_flagged_edges(basename)
    print( 'There is ', nx.number_connected_components(G), 'connected components in the original graph')
    print( 'There is ', nx.number_connected_components(H), 'connected components in the graph without flagged edges')
    
    closeby_all = []
    keys_disconnected_all =[]
    
    #cc_number = 0
    if nx.is_connected(H) == False:
        #iterate through the connectec components to find nodes where disconnection occured
        #search for the nodes that used to be degree >1 and are now degree 1.
        for i, subgraph_index in enumerate(nx.connected_components(H)):
            #print(i,subgraph_index )
            subgraph = nx.subgraph(H, subgraph_index)

            keys_disconnected_subgraph=[]   
            #find all the nodes where disconnection happened
            #look for all the nodes degree smaller in the cleaned file than in the original file 
            #keys_disconnected_subgraph = [k for k, v in dict(subgraph.degree()).items() if v == 1 and G_raw.degree()[k] >1]   
            for k in subgraph.nodes(): #dict(subgraph.degree()).items():
                #print(k)
                if subgraph.degree()[k]==1 and G.degree()[k] >1:
                    keys_disconnected_subgraph.append(k)

                
            keys_disconnected_all = keys_disconnected_all + keys_disconnected_subgraph
        return keys_disconnected_all
    else:
        print('There is no disconnected components, no need to merge')




# ----------------------------------------------------------------------------
def get_potential_connection(
        G,
        dist_horiz_max,
        dist_vert_max,
        node_deg=1,
        exclude_neighbors_up_to_edge=3,
        pos_attr='pos',
        return_dist=False,
        return_angle=False):
    """
    Retrieves list of potential new edges for a graph.

    For every node `u` of given degree `node_deg`:

    1. the nodes within a cylindrical box of horizontal radius `dist_horiz_max`
    and height `dist_vert_max` centered at `u` are retrieved in a list

    2. The nodes of this list at a distance in number of edges less than or
    equal to `exclude_neighbors_up_to_edge` are excluded.

    3. Then, the nearst node `v` to `u` (checking horizontal Euclidean distance)
    in this list is identified, and the tuple `(u, v)` is considered as a potential
    edge to be added to the graph (new connection)

    Parameters
    ----------
    G : networkx.Graph
        graph

    dist_horiz_max : float (positive)
        maximal horizontal distance (radius of the cylinder around checked nodes)

    dist_vert_max : float (positive)
        maximal vertical distance (height of the cylinder around checked nodes)

    exclude_neighbors_up_to_edge : int, default: 3
        distance in number of edges, nodes to a distance from a checked node at
        distance smaller than or equal to `exclude_neighbors_up_to_edge` are excluded
        from potential edge with the checked node

    node_deg : int, default: 1
        degree of the nodes to be checked as an extremity for
        potential new edge

    return_dist : bool, default: False
        if `True`, the length of the potential new edges (distance between the
        two extremities) are returned

    return_angle : bool, default: False
        if `True`, xxxxthe length of the potential new edges (distance between the
        two extremities) are returned

    Returns
    -------
    edges_list : list of 2-tuples
        list of potential new edges, each element is a 2-tuple (u, v), where
        u and v are the node ids of the two extremities of a potential new edge

    dist_list : list of floats, optional
        returned if `return_dist=True`, list of same length as `edges_list`, of the
        lengths of the potential new edges (distance between the two extremities)

    angle_list : list of lists of float(s), optional
        returned if `return_angle=True`, list of same length as `edges_list`, where
        `angle_list[i]` is the list of angles between the potential new edge `edge_list[i]`
        and the existing edge(s) whose one extremity is the node ``edge_list[i][0]`;
        each angle is in degree in the interval [0, 180]
    """
    # Set dictionary to convert node label (id) to node index, and vice versa
    node_label2index = {u:i for i, u in enumerate(G.nodes())}
    node_index2label = {i:u for i, u in enumerate(G.nodes())}

    pos = nx.get_node_attributes(G, pos_attr)
    pos = {k:np.asarray(v) for k, v in pos.items()} # convert tuple to array

    # Matrix of all positions
    pos_arr = np.asarray(list(pos.values()))

    rh2 = dist_horiz_max**2
    rv = dist_vert_max

    edges_list = []
    for u in G.nodes():
        if G.degree(u) != node_deg:
            continue

        # Get array (sel_ind_arr) of index of nodes within the cylindrical box centered at u:
        ind = node_label2index[u]
        lag = pos_arr - pos_arr[ind]
        disth2 = np.sum(lag[:,:2]**2, axis=1)
        distv = np.abs(lag[:,2])
        sel = np.all((disth2 <= rh2, distv <= rv), axis=0) # True at least for node u (at index ind)
        sel_ind_arr = np.where(sel)[0]
        if sel_ind_arr.size <= 1:
            continue

        # Get array (neigh_to_exclude_ind_arr) of neighbors index to exclude
        neigh_to_exclude_ind_arr = np.asarray([node_label2index[v] for v in list(nx.single_source_shortest_path_length(G, u, cutoff=exclude_neighbors_up_to_edge).keys())])

        # Update sel_ind_array
        sel_ind_arr = np.setdiff1d(sel_ind_arr, neigh_to_exclude_ind_arr)

        if sel_ind_arr.size == 0:
            continue

        # Get v the nearest node to u : potential edge (u, v)
        min_ind = sel_ind_arr[np.argmin(disth2[sel_ind_arr])]
        v = node_index2label[min_ind]
        edges_list.append((u, v))

    out = [edges_list]

    if return_dist:
        if len(edges_list):
            dist_list = [pos_arr[node_label2index[u]] - pos_arr[node_label2index[v]] for u, v in edges_list]
            dist_list = list(np.sqrt(np.sum(np.asarray(dist_list)**2, axis=1)))
        else:
            dist_list = []
        out.append(dist_list)

    if return_angle:
        angle_list = []
        for u, v in edges_list:
            pos_u = pos_arr[node_label2index[u]]
            pos_v = pos_arr[node_label2index[v]]
            uv = pos_v - pos_u
            uv_norm = np.sqrt(np.sum(uv**2))
            a = []
            for _, vi in G.edges(u):
                pos_vi = pos_arr[node_label2index[vi]]
                uvi = pos_vi - pos_u
                uvi_norm = np.sqrt(np.sum(uvi**2))
                a.append(np.rad2deg(np.arccos(np.sum(uv*uvi)/(uv_norm*uvi_norm))))
            angle_list.append(a)
        out.append(angle_list)

    if len(out) == 1:
        out = out[0]
    else:
        out = tuple(out)

    return out
# ----------------------------------------------------------------------------