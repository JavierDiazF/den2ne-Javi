#!/usr/bin/python3

from numpy.lib.function_base import append
from .den2neHLMAC import HLMAC


class Den2ne(object):
    """
        Clase para gestionar la lógica del algoritmo
    """

    # Declaramos tipos de criterio para la decisión entre IDs
    CRITERION_NUM_HOPS = 0
    CRITERION_DISTANCE = 1
    CRITERION_POWER_BALANCE = 2
    CRITERION_POWER_BALANCE_WITH_LOSSES = 3
    CRITERION_LINKS_LOSSES = 4

    def __init__(self, graph):
        """
            Constructor de la clase Den2ne
        """
        self.G = graph
        self.global_ids = list()
        self.root = graph.root

    def spread_ids(self):
        """
            Funcion para difundir los IDs entre todos los nodos del grafo
        """

        # Var aux: lista con los nodos que debemos visitar (Va a funcionar como una pila)
        nodes_to_attend = list()

        # Empezamos por el root, como no tiene padre el root, su HLMAC parent addr es None -> No hereda.
        # además, no tiene ninguna dependencia (es decir no tiene ninguno enlace por delante de el de tipo switch)
        self.G.nodes[self.G.findNode(self.root)[0]].ids.append(HLMAC(None, self.root, None))

        # El primero en ser visitado es el root
        nodes_to_attend.append(self.root)

        # Mientras haya nodos a visitar...
        while len(nodes_to_attend) > 0:

            curr_node = self.G.findNode(nodes_to_attend[0])

            # Iteramos por las posibles IDs disponibles en el nodo
            for i in range(0, len(curr_node[1].ids)):

                if not curr_node[1].ids[i].used:

                    # Iteramos por los vecinos del primer nodo a atender
                    for neighbor in curr_node[1].neighbors:

                        # Vamos a comprobar antes de asignar IDs al vecino, que no hay bucles
                        if HLMAC.hlmac_check_loop(curr_node[1].ids[i], neighbor):
                            pass
                        else:
                            # Si no hay bucles asignamos la ID al vecino

                            # Vamos a comprobar si la relación del nodo con el vecino viene dada por un enlace de tipo switch
                            id_switch_node = self.G.findSwitchID(curr_node[1].name)
                            id_switch_neighbor = self.G.findSwitchID(neighbor)
                            if id_switch_node == id_switch_neighbor:
                                self.G.nodes[self.G.findNode(neighbor)[0]].ids.append(HLMAC(curr_node[1].ids[i], neighbor, id_switch_node))
                            else:
                                self.G.nodes[self.G.findNode(neighbor)[0]].ids.append(HLMAC(curr_node[1].ids[i], neighbor, None))

                            # Registramos el vecino emn la pila para ser visitado más adelante
                            nodes_to_attend.append(neighbor)

                    # Y tenemos que marcar la HLMAC como que ya ha sido usada
                    self.G.nodes[curr_node[0]].ids[i].used = True

            # Por último desalojamos al nodo atendido
            nodes_to_attend.pop(0)

    def collectActiveIDs(self):
        """
            Funcion que recoje en una variable global las IDs en uso para establecer el grafo elegido
        """
        for node in self.G.nodes:
            self.global_ids.append(node.getActiveID())

    def selectBestIDs(self, criterion):
        """
            Función para decidir la mejor ID de en nodo dado un criterio
        """

        # Vamos a elegir la mejor ID para cada nodo
        if Den2ne.CRITERION_NUM_HOPS == criterion:
            self.selectBestID_by_hops()

        elif Den2ne.CRITERION_DISTANCE == criterion:
            self.selectBestID_by_distance()

        elif Den2ne.CRITERION_POWER_BALANCE == criterion:
            self.selectBestID_by_balance()

        elif Den2ne.CRITERION_POWER_BALANCE_WITH_LOSSES == criterion:
            self.selectBestID_by_balance_with_Losses()

        elif Den2ne.CRITERION_LINKS_LOSSES == criterion:
            self.selectBestID_by_Links_Losses()

        # Una vez elegidas vamos a recoger las IDs activas de cada nodo
        self.collectActiveIDs()

        # Por último, vamos a ver el las dependencias con los switchs y activar aquellos que sean necesarios
        dependences = list(set(sum([active_ids.depends_on for active_ids in self.global_ids], [])))

        for sw in self.G.sw_config:
            if not self.G.sw_config[sw]["pruned"]:
                self.G.setSwitchConfig(sw, 'open')

        for deps in dependences:
            self.G.setSwitchConfig(deps, 'closed')

    def selectBestID_by_hops(self):
        """
            Función para decidir la mejor ID de un nodo por numero de saltos al root
        """
        for node in self.G.nodes:
            lens = [len(id.hlmac) for id in node.ids]

            # La ID con un menor tamaño será la ID con menor numero de saltos al root
            # Por ello, esa será la activa.
            self.G.nodes[self.G.nodes.index(node)].ids[lens.index(min(lens))].active = True

    def selectBestID_by_distance(self):
        """
            Función para decidir la mejor ID de un nodo por distancia al root
        """
        for node in self.G.nodes:
            dists = [self.getTotalDistance(id) for id in node.ids]

            self.G.nodes[self.G.nodes.index(node)].ids[dists.index(min(dists))].active = True

    def getTotalDistance(self, id):
        """
            Funcion para calcular la distancia total de una HLMAC
        """
        distances = 0
        for i in range(0, len(id.hlmac)-1):
            distances += self.G.findNode(id.hlmac[i])[1].links[self.G.findNode(id.hlmac[i])[1].neighbors.index(id.hlmac[i+1])].dist

        return distances

    def selectBestID_by_balance(self):
        """
            Función para decidir la mejor ID de un nodo por balance de potencia al root
        """
        for node in self.G.nodes:
            balances = [self.getTotalBalance(id) for id in node.ids]

            self.G.nodes[self.G.nodes.index(node)].ids[balances.index(max(balances))].active = True

    def getTotalBalance(self, id):
        """
            Funcion para calcular el balance de potencias total de una HLMAC
        """
        balance = 0
        for i in range(0, len(id.hlmac)):
            balance += self.G.findNode(id.hlmac[i])[1].load

        return balance

    def selectBestID_by_balance_with_Losses(self):
        """
            Función para decidir la mejor ID de un nodo por balance de potencia al root con perdidas
        """
        for node in self.G.nodes:
            balances = [self.getTotalBalance_with_Losses(id) for id in node.ids]

            self.G.nodes[self.G.nodes.index(node)].ids[balances.index(max(balances))].active = True

    def getTotalBalance_with_Losses(self, id):
        """
            Funcion para calcular el balance de potencias total de una HLMAC con perdidas
        """
        balance = 0
        for i in range(len(id.hlmac)-1, 0, -1):
            curr_node = self.G.findNode(id.hlmac[i])

            # No tenemos en cuenta el root.. es uno nodo virtual, nos ahorramos comprobaciones y sumar 0
            balance += (curr_node[1].load - curr_node[1].links[curr_node[1].neighbors.index(id.hlmac[i-1])].getLosses(curr_node[1].load + balance))

        return balance

    def selectBestID_by_Links_Losses(self):
        """
            Función para decidir la mejor ID de un nodo en función de sus perdidas al root
        """
        for node in self.G.nodes:
            losses = [self.getTotalLinks_Losses(id) for id in node.ids]

            self.G.nodes[self.G.nodes.index(node)].ids[losses.index(min(losses))].active = True

    def getTotalLinks_Losses(self, id):
        """
            Funcion para calcular las perdidas desde un nodo dado al root
        """

        init_node = self.G.findNode(id.hlmac[len(id.hlmac)-1])
        curr_load = init_node[1].load
        losses = 0

        for i in range(len(id.hlmac)-1, 0, -1):
            curr_node = self.G.findNode(id.hlmac[i])

            losses += curr_node[1].links[curr_node[1].neighbors.index(id.hlmac[i-1])].getLosses(curr_load)
            curr_load -= losses

        return losses

    def globalBalance(self, withLosses):
        """
            Funcion que obtniene el balance global de la red y la dirección de cada enlace (hacia donde va el flujo de potencia) 
        """

        # Primero hay que ordenar la lista de global_ids de mayor a menor
        self.global_ids.sort(key=Den2ne.key_sort_by_HLMAC_len, reverse=True)

        # Vamos a estudiar tambien el abs() del movimiento de flujo de Potencia
        abs_flux = 0.0

        # Vamos tambien a prestar atencion a la capacidad
        cap = 0.0

        # Mientras haya IDs != del root -> Vamos a trabajar con listado global como si fuera una pila
        while len(self.global_ids) > 1:

            # Origen
            [origin_index, origin] = self.G.findNode(self.global_ids[0].getOrigin())

            # Destino
            [dst_index, dst] = self.G.findNode(self.global_ids[0].getNextHop())

            # Establecemos la dirección del flujo de potencia en el enlace
            if origin.load < 0:
                self.G.setLinkDirection(origin.name, dst.name, 'down')
                self.G.setLinkDirection(dst.name, origin.name, 'up')
            else:
                self.G.setLinkDirection(origin.name, dst.name, 'up')
                self.G.setLinkDirection(dst.name, origin.name, 'down')

            cap = self.G.getLinkCapacity(origin.name, dst.name)

            # Agregamos la carga de origen a destino
            if withLosses:
                # if cap is None or cap >= origin.load:
                #     self.G.nodes[dst_index].load += origin.load - origin.links[origin.neighbors.index(dst.name)].getLosses(origin.load)
                    
                #     # Actualizamos el flujo absoluto
                #     abs_flux += abs(origin.load - origin.links[origin.neighbors.index(dst.name)].getLosses(origin.load))

                # else:
                #     self.G.nodes[dst_index].load += cap - origin.links[origin.neighbors.index(dst.name)].getLosses(cap)

                #     # Actualizamos el flujo absoluto
                #     abs_flux += abs(cap - origin.links[origin.neighbors.index(dst.name)].getLosses(cap))
                self.G.nodes[dst_index].load += origin.load - origin.links[origin.neighbors.index(dst.name)].getLosses(origin.load)
                    
                # Actualizamos el flujo absoluto
                abs_flux += abs(origin.load - origin.links[origin.neighbors.index(dst.name)].getLosses(origin.load))
            else:
                # if cap is None or cap >= origin.load:
                #     self.G.nodes[dst_index].load += origin.load

                #     # Actualizamos el flujo absoluto
                #     abs_flux += abs(origin.load)
                # else:
                #     self.G.nodes[dst_index].load += cap

                #     # Actualizamos el flujo absoluto
                #     abs_flux += abs(cap)
                self.G.nodes[dst_index].load += origin.load

                # Actualizamos el flujo absoluto
                abs_flux += abs(origin.load)

            # Ajustamos a cero el valor de la carga en origen
            self.G.nodes[origin_index].load = 0.0

            # Una vez atendida la ID más larga de la lista, la desalojamos
            self.global_ids.pop(0)

        # Devolvemos el balance total
        return [self.G.findNode(self.root)[1].load, abs_flux]

    @ staticmethod
    def key_sort_by_HLMAC_len(id):
        """
            Función para key para ordenar el listado global de IDs en función de la longitud de las HLMACs
        """
        return len(id.hlmac)

    def updateLoads(self, loads, delta):
        """
            Funcion para actualizar las cargas de los nodos del grafo
        """

        # Como solo tenemos las cargas de los nodos normales, vamos a poner a 0 todos y establecer las cargas de los normales
        for i in range(0, len(self.G.nodes)):
            if self.G.nodes[i].name in loads:
                self.G.nodes[i].load = loads[self.G.nodes[i].name][delta]
            else:
                self.G.nodes[i].load = 0

    def clearSelectedIDs(self):
        """
            Función para borrar el flag de active de todas las IDs de cada nodo
        """
        # Limpiamos las IDs globales
        self.global_ids = list()

        # De esta forma podemos volver a tomar una función objetivo
        for i in range(0, len(self.G.nodes)):
            for j in range(0, len(self.G.nodes[i].ids)):
                self.G.nodes[i].ids[j].active = False

    def write_ids_report(self, filename):
        """
            Función que genera un fichero de log con el resultado de las asignaciones de las IDs
        """
        with open(filename, 'w') as file:
            for node in self.G.nodes:
                file.write('-------------------------------------------------------------------------')
                file.write('-------------------------------------------------------------------------\n')
                file.write(f'| Node: {node.name}  | Type: {node.type} | Neighbors: {len(node.neighbors)} \n')
                file.write('-------------------------------------------------------------------------')
                file.write('-------------------------------------------------------------------------\n')
                file.write('|  Status  |  ID                                                              \n')
                file.write('-------------------------------------------------------------------------')
                file.write('-------------------------------------------------------------------------\n')
                for id in node.ids:
                    file.write(f'|   {id.used}   |  {HLMAC.hlmac_addr_print(id)} \n')
                file.write('-------------------------------------------------------------------------')
                file.write('-------------------------------------------------------------------------\n')
                file.write('\n')

    def write_loads_report(self, filename):
        """
            Función que genera un fichero de log con el resultado de las asignaciones de carga
        """
        with open(filename, 'w') as file:
            for node in self.G.nodes:
                file.write('-------------------------------------------------------------------------')
                file.write('-------------------------------------------------------------------------\n')
                file.write(f'| Node: {node.name}  | Type: {node.type} | Neighbors: {len(node.neighbors)} | Load: {node.load} \n')
                file.write('-------------------------------------------------------------------------')
                file.write('-------------------------------------------------------------------------\n')
                file.write('|    Flag    |  ID                                                              \n')
                file.write('-------------------------------------------------------------------------')
                file.write('-------------------------------------------------------------------------\n')
                for id in node.ids:
                    file.write(
                        f'|     {int(id.active)}     |  {HLMAC.hlmac_addr_print(id)} \n')
                file.write('-------------------------------------------------------------------------')
                file.write('-------------------------------------------------------------------------\n')
                file.write('\n')


    def write_swConfig_report(self, filename):
        """
            Función que genera un fichero de log con el resultado de la config lógica de la red
        """
        with open(filename, 'w') as file:
            for key in self.G.sw_config:
                file.write('-------------------------------------------------------------------------\n')
                file.write(f'| ID: {key}  | Node A: {self.G.sw_config[key]["node_a"]} | Node B: {self.G.sw_config[key]["node_b"]} | Status: {self.G.sw_config[key]["state"]}                    |\n')
                file.write('-------------------------------------------------------------------------\n')
                file.write('\n')

    def write_swConfig_CSV(self, filename):
        """
            Función que genera un fichero CSV con el resultado de la config lógica de la red
        """
        with open(filename, 'w') as file:
            file.write('ID,Node A,Node B,State\n')
            for key in self.G.sw_config:
                file.write(f'{key},{self.G.sw_config[key]["node_a"]},{self.G.sw_config[key]["node_b"]},{self.G.sw_config[key]["state"]}\n')
