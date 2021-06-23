#!/usr/bin/python3

from graph.graph import Graph
from den2ne.den2neALG import Den2ne
from dataCollector.dataCollector import DataGatherer


def main():

    # Recolectamos los datos
    loads = DataGatherer.getLoads('data/loads.csv', 3)
    edges = DataGatherer.getEdges('data/links.csv')
    sw_edges = DataGatherer.getSwitches('data/switches.csv')
    positions = DataGatherer.getPositions('data/node_positions.csv')

    # Creamos la var del grafo para el primer instante
    G = Graph(0, loads, edges, sw_edges)

    # Parseamos a NetworkX y pintamos el grafo
    G.plotGraph(positions, 'IEEE 123 Node test feeder - Graph')

    # Lo ideal sería automatizar el proceso de poda del grafo de aquellos nodos virtuales que estén a modo de ampliación.
    # De momento lo vamos a hacer a mano, ya que vamos mal de tiempo.
    to_prune = ['250', '251', '350', '450', '451', '61', '610']
    for nodes in to_prune:
        G.removeNode(nodes)

    # Podemos vovler a pintar para comprobar la poda realziada
    G.plotGraph(positions, ' IEEE 123 Node test feeder - Pruned Graph')

    # Iniciamos el algoritmo
    G_den2ne_alg = Den2ne(G, root='150')

    # Primera fase: difusión de IDs
    G_den2ne_alg.spread_ids()
    G_den2ne_alg.write_ids_report('results/report_ids.txt')

    # Sacamos las figuras en modo iteractivo (Metodo que bloquea el flujo del script)
    G.showGraph()


if __name__ == "__main__":
    main()
