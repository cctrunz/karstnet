import networkx as nx



def add_edges(G,additional_edges, dict_address=None, flag = 'add'):
    """Add edges to a networkx cave graph, based on a list of edges
    Parameters
    ----------
    G : networkx graph 
        Graph produced with the function kn.from_therion_sql_enhanced

    additional_edges : list of tuple or list of lists
        list of edges to add to the graph. The edges will be created between already existing nodes, and a flag add will be added. 

        example:
        -----------
        in the case that use_fulladdress == True: additional_edges = [['full_address.0','full_address.1],['full_address.3','full_address.10]]
        if the current networkx key is used: additional_edges = [[67,2],[110,232]]

    dict_address : dict, optional
        by default this function takes the current networkx keys of the graph G. 
        When dict_address is not None, then it uses other node identifiers (for example, it can be the original node name)
        The dictionnary 
        stored in the graph attributes G.nodes('fulladdress').
        This attribute is created with the therion import function.

        example:
        --------
        Each current node id can be associated to a series of older ids, in the case that stations where regrouped because they were at the same positions.
        dict_address = {id_0:['old_id_20','old_id_1','old_id_200'], id_1:['old_id_3']}

        When the cave is processed created with the import function therion, then the original node name is stored in the 
        graph attributes G.nodes('fulladdress'), in the form of a full path from the main folder. This is a therion standard:
        dict_address = {id_0:['full_address.0','full_address.1','full_address.4'], id_1:['full_address.0']}

    """
    
    #create dictionnary to find current id based on the fulladdress
    if dict_address is not None:
        inverse_dict_address = { v: k for k, l in dict_address.items() for v in l }

    for edge in additional_edges:
        #check if there is flags already attached to the edges
        if dict_address is not None:
            #find node id based on the full address and attach the edge
            edge_from = inverse_dict_address[edge[0]]
            edge_to = inverse_dict_address[edge[1]]
            # edges[i][0] = [key for key, value in dict_address.items() if edge[0] in value ][0]
            # edges[i][1] = [key for key, value in dict_address.items() if edge[1] in value ][0]  
            # create a new edge with the flag value
            G.add_edge(edge_from,edge_to,flags=[flag])
        else: 
            # create a new edge with the flag value
            G.add_edge(edge[0],edge[1],flags=[flag])   


                
            


def flag_nodes(G,flagged_nodes, dict_address=None):
    
    """Add a string in the node attribute 'flag' of the networkx cave graph.

    Parameters
    ----------
    G : networkx graph 
        Graph produced with the function kn.from_therion_sql_enhanced
    
    flagged_nodes : dictionnary of list, optional
        list of nodes to be flagged, with associated flag.
        The dictionnary key is the flag, and the values associated with the key is the list of node ids to flag.

        Example of dictionnary: 
        -----------------------
        flagged_nodes = {'ent':['full_address.0','full_address.1','full_address.4']}
        flagged_nodes = {'ent':[old_id_1,old_id_4,old_id_400]}
        or 
        flagged_nodes = {'ent':[8,45,201]}

    dict_address : dict, optional
        by default this function takes the current networkx keys of the graph G. 
        When dict_address is not None, then it uses other node identifiers (for example, it can be the original node name)
        The dictionnary 
        stored in the graph attributes G.nodes('fulladdress').
        This attribute is created with the therion import function.
        
        example:
        --------
        Each current node id can be associated to a series of older ids, in the case that stations where regrouped because they were at the same positions.
        dict_address = {id_0:['old_id_20','old_id_1','old_id_200'], id_1:['old_id_3']}

        When the cave is processed created with the import function therion, then the original node name is stored in the 
        graph attributes G.nodes('fulladdress'), in the form of a full path from the main folder. This is a therion standard:
        dict_address = {id_0:['full_address.0','full_address.1','full_address.4'], id_1:['full_address.0']}


    """

    print(f'Therion Import - adding manual node flags: {flagged_nodes.keys()}')

    #create dictionnary to find current id based on the fulladdress
    if dict_address is not None:
        inverse_dict_address = { v: k for k, l in dict_address.items() for v in l }

        
    for flag in flagged_nodes.keys():
        #loop throught the flags
        for node in flagged_nodes[flag]:
            if dict_address is not None:
                id_node = inverse_dict_address[node]   
            else:
                id_node = node                   
            #check if node already has a flag
            #if not, create a new list of flag(s) attached to the node
            if G.nodes('flags')[id_node] is None:
                # pass
                #create flag on node
                nx.set_node_attributes(G, {id_node:[flag]}, name='flags')
            #if yes, append the new flag to the list
            elif G.nodes('flags')[id_node] is not None:
                #print(flag,id_node, fulladdress)
                G.nodes[id_node]['flags'].append(flag)



def flag_edges(G, flagged_edges, dict_address = None):
    """Add a string in the edge attribute 'flag' of the networkx cave graph.

    Parameters
    ----------
    G : networkx graph 
        Graph produced with the function kn.from_therion_sql_enhanced

    flagged_edges : dictionnary of list of tuple or list of lists, optional
        lists of edges to be flagged with corresponding flag to add. Any flag can be added. by default None
        However, for the duplicate edges and surface edges to be removed, it is necessary to use the correct flags.
        It is also possible to use the add edges with this dictionnary instead of using the 'add_edges' option.
        List of flagged edge that will be removed by default:  'dpl', 'srf', 'art', 'rmv', 'spl'

    use_fulladdress : bolean, default False
        by default this function takes the current networkx keys of the graph G. 
        When True, then it uses the "fulladdress" string stored in the graph attributes G.nodes('fulladdress').
        This attribute is created with the therion import function.

    Example of dictionnary: 
    ----------------------
    if use_fulladdress == True:
    flagged_edges = {'dpl':[['full_address.0','full_address.1],['full_address.3','full_address.10]], 'srf':[[full_address.3,full_address.2]]}   

    if we use the networkx key:
    flagged_edges = {'dpl':[[1,3],[11,5]], 'srf':[[5,11]]}   
    """
    print(f'Therion Import - adding manual edges flags: {flagged_edges.keys()}')

    #create dictionnary to find current id based on the fulladdress
    if dict_address is not None:
        inverse_dict_address = { v: k for k, l in dict_address.items() for v in l }

    
    #loop through all the flags
    for flag in flagged_edges.keys():
        print(flag)
        #loop through all the edges for each flag
        for edge in flagged_edges[flag]:
            if dict_address is not None:
                edge_from = inverse_dict_address[edge[0]]
                edge_to = inverse_dict_address[edge[1]]
            else:
                edge_from = edge[0]
                edge_to = edge[1]
            #check if edge exists already (for example to add a duplicate flag on an exisiting edge)
            if G.has_edge(edge_from,edge_to):
            #check if there is flags already attached to the edges
            #if not, create a new edge with the dictionnary 'flags' and the flag value
                if 'flags' not in G[edge_from][edge_to]:
                    # print(f'adding {flag} to edge {edge_from}-{edge_to}')
                    nx.set_edge_attributes(G,{(edge_from,edge_to):{'flags':[flag]}})
                    
                #if yes, append the flag to the list
                elif 'flags' in G[edge_from][edge_to]:
                    # print(f'appending {flag} to edge {edge_from}-{edge_to}')
                    G[edge_from][edge_to]['flags'].append(flag)
            #if edge does not exist yet, then just create a new edge with the appropriate flag name            
            else:
                # add the flag add by default?? if yes, implement this feature (20 fev 2025)
                # print(f'creating edge and adding {flag} to edge {edge_from}-{edge_to}')
                G.add_edge(edge_from,edge_to,flags=[flag])
                # print(f'graph length: {len(G)}')


# def remove_edges()

def remove_flagged_edges(G, flags_to_remove=['srf','dpl','rmv','art','spl'], attribute_name = 'flags'):
    """Remove edges flagged with certain strings.

    Parameters
    ----------
    G : networkx graph 
        Graph produced with the function kn.from_therion_sql_enhanced

    flags_to_remove : list of strings, optional
        list of the flags for which edges should be removed, by default ['srf','dpl','rmv','art','spl']
        - 'dpl' : duplicate
        - 'srf' : surface
        - 'art' : artificial
        - 'rmv' : remove
        - 'spl' : splay (for example when a shot is made in a large room, star shots, ...)
    attribute_name : string
        name of the attribute attached to the graph 


    """
    #edges_to_remove = list(dict(nx.get_edge_attributes(G,'flags')).keys()) 
    #extract flag unique values into a list
    flags = {x for l in list(nx.get_edge_attributes(G,attribute_name).values()) for x in l}
    #loop through the unique flags and 


    for flag in flags:
        #only remove edges with flag surface, duplicate, or remove
        if flag in flags_to_remove:
            
            list_edges = [edge for edge, action in nx.get_edge_attributes(G,attribute_name).items() if flag in action]
            #print('remove ', flag, list_edges)
            #remove edges    
            G.remove_edges_from(list_edges)
            #remove nodes that were isolated when removing the edges
            G.remove_nodes_from(list(nx.isolates(G)))
        else:
            pass
            #print('not removed', flag)



    # print(f'Initial Graph size: {len(G)}, Graph size after removing flagged edges: {len(H)}')
    # return H