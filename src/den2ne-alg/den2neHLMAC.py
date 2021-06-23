#!/usr/bin/python3


class HLMAC(object):
    """
        Clase para gestionar las HLMACs asignadas
    """

    def __init__(self, hlmac_parent_addr, name):
        """
            Constructor de la clase HLMAC 
        """
        self.hlmac = HLMAC.hlmac_assign_address(hlmac_parent_addr, name)

    @staticmethod
    def hlmac_assign_address(hlmac_parent_addr, name):
        """
            Método para asignar una HLMAC a partir de una addr padre
        """
        new_addr = list()

        if hlmac_parent_addr is not None:
            # No podemos asignar sin más la lista ya que si no se coparten referencias, y serían mutables entre ellas.
            # Por ello, hay que llamar a copy()
            new_addr = hlmac_parent_addr.hlmac.copy()

        return new_addr.append(name)

    @staticmethod
    def hlmac_cmp_address(hlmac_a, hlmac_b):
        """
            Funcion para comparar dos addr HLMAC
        """
        return hlmac_a.hlmac == hlmac_b.hlmac

    @staticmethod
    def hlmac_addr_print(addr):
        """
            Funcion para imprimir una HLMAC
        """
        print('.'.join(map(str, addr.hlmac)))
