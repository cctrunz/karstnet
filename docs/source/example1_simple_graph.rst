A simple example
==================

To illustrate how Karstnet can be used, let us start with a simple example.
The aim is to generate a karstic network from scratch, using only a set of
nodes (including their positions) and a set of edges connecting the nodes.
From these data, the graph is generated, plotted and its statistical
properties are computed.


Create network
--------------

First, one has to import the karstnet module::

    import karstnet as kn


We then create a dictionnary of nodes. Each node is defined by a key
(here an integer ID number) and its position in 2D (can also be in 3D).
The second structure is a list of edges. Each edge is a tuple containing
a pair of nodes::

    nodes = {1 : (0, 0), 2 : (0, 1), 3 : (-1, 2), 4 : (1, 2),
             5 : (-1.5, 3), 6 : (-0.5, 3), 7 : (0.5, 3), 8 : (1.5, 3),
             9 : (-2, 4), 10 : (-1, 4), 11 : (0, 4), 12 : (1, 4), 13 : (0.5, 5)}
    edges = [(1, 2), (2, 3), (2, 4), (3, 5), (3, 6), (4, 7),
             (4, 8), (5, 9), (5, 10), (7, 11), (7, 12), (7, 13)]

The next step is to create the karst network object using karstnet::

    k = kn.KGraph(edges, nodes)

At this step, karstnet has created the internal structure of the graph and
precomputed all the information that it requires, like for example the
distance between the nodes, the orientation of the edges, and stored everything
in the object.

Visualize and compute the statistics
------------------------------------

Before going further, it is possible to plot the network in 2D::

    k.plot2()

Other functions are available to plot in 3D or to improve the graphical
representations. But for the moment, let us just compute the statistical
characteristics of this network. We just have to call this function::

    results = k.characterize_graph( verbose = True )
