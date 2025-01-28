import sys
import csv
import copy
import time

from collections import deque, OrderedDict
from math import inf

class Estado:
    def __init__(self, sucesores, ubicacion_vehiculo, pacientes_a_bordo, pacientes_por_recoger, energia, tipo, g, h, padre = None):
        self.sucesores = sucesores                                              #  Nodos adyacentes a los que puede acceder ??
        self.ubicacion_vehiculo = ubicacion_vehiculo                            # Una dupla. (x,y)
        self.pacientes_a_bordo = pacientes_a_bordo                              # Una dupla (i, j). i numero de no contagiosos y j numero de contagiosos
        self.pacientes_por_recoger = pacientes_por_recoger                      # Una lista de domicilios todavia sin recoger
        self.energia = energia                                                  # La energía de la ambulancia
        self.tipo = tipo                                                        # Tipo: P, N, C, CN, CC, 1, 2 
        self.g = g                                                              # Coste de los arcos total
        self.h = h                                                              # Función heurística
        self.padre = padre 

class Problema:
    def __init__(self, mapa):
        # Diversa información del mapa usada en el algoritmo 
        self.mapa = mapa
        pacientes = self.obtener_pacientes()
        fila_inicial, columna_inicial, adyacentes = self.obtener_parking()
        self.estado_inicial = Estado(adyacentes, (fila_inicial, columna_inicial), (0, 0), pacientes, 50, 'P', 0, 10000, None)
        self.estado_actual = self.estado_inicial
        self.parking = (fila_inicial, columna_inicial)
        self.centros = self.obtener_centros()
        self.contagiosos_max = 2
        self.no_contagiosos_max = 8 

    def obtener_parking(self):
        # Consigue la posición del parking del csv
        with open(self.mapa, newline='') as csvfile:
            lector_csv = csv.reader(csvfile, delimiter=';')
            for i, fila in enumerate(lector_csv, start=1):
                for j, valor in enumerate(fila, start=1):
                    if valor == 'P':
                        fila_p = i
                        columna_p = j
                        adyacentes = self.obtener_hijos(fila_p, columna_p)
                        return (fila_p, columna_p, adyacentes)
        return None
    
    def obtener_centros(self):
        # Obtiene las posiciones de los centros
        with open(self.mapa, newline='') as csvfile:
            lector_csv = csv.reader(csvfile, delimiter=';')
            for i, fila in enumerate(lector_csv, start=1):
                for j, valor in enumerate(fila, start=1):
                    if valor == 'CC':
                        fila_p = i
                        columna_p = j
                        centro_contagioso = (fila_p, columna_p)
                    if valor == 'CN':
                        fila_p = i
                        columna_p = j
                        centro_no_contagioso = (fila_p, columna_p)
        return (centro_contagioso, centro_no_contagioso)
    
    def anadir_numeros(self, adyacentes, clave, i, j):
        # Introduce el estado en la lista abierta segun su función f y si ya esta no lo introduce 
        if clave in adyacentes.keys():
            adyacentes[clave].append((i,j))
        else:
            adyacentes[clave] = [(i,j)]
        return adyacentes
    
    def obtener_hijos(self, fila, columna):
        # Obtiene los adyacentes a la casilla (fila, columna)
        adyacentes = {}
        with open(self.mapa, newline='') as csvfile:
            lector_csv = csv.reader(csvfile, delimiter=';')
            for i, fila_actual in enumerate(lector_csv, start=1):
                for j, valor in enumerate(fila_actual, start=1):
                    if valor != 'X' and ((i == fila and abs(j - columna) == 1) or (j == columna and abs(i - fila) == 1)):  # Si son adyacentes
                        adyacentes = self.anadir_numeros(adyacentes,valor, i, j)
        return adyacentes  
    
    def obtener_pacientes(self):
        # Obtiene los pacientes del mapa (fila, columna)
        pacientes = {"N": [], "C": []}
        with open(self.mapa, newline='') as csvfile:
            lector_csv = csv.reader(csvfile, delimiter=';')
            for i, fila_actual in enumerate(lector_csv, start=1):
                for j, valor in enumerate(fila_actual, start=1):
                    if valor == 'N':
                        pacientes[valor].append((i, j)) 
                    if valor == 'C':
                        pacientes[valor].append((i, j))
        return pacientes
    
    def cargar_tablero_desde_csv(self):
        with open(self.mapa, 'r') as archivo:
            lector = csv.reader(archivo, delimiter=';')
            tablero = [fila for fila in lector]
        return tablero
    
    def calcular_distancia_min(self, pos_inicio: tuple, pos_final: tuple, tablero):
        movimientos = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        # Usar BFS para encontrar el camino más corto
        cola = deque([(pos_inicio, 0)])  # La cola almacena la posición y la distancia desde el inicio
        visitado = set()
        while cola:
            actual, distancia = cola.popleft()
            visitado.add(actual)
            if actual == pos_final:
                return distancia
            for movimiento in movimientos:
                nueva_posicion = (actual[0] + movimiento[0], actual[1] + movimiento[1])
                if (0 < nueva_posicion[0] < len(tablero) + 1):
                    if (0 < nueva_posicion[1] < len(tablero)+ 1 ):
                        if nueva_posicion not in visitado:
                # Verificar si la nueva posición está dentro del tablero y no ha sido visitada
                            if (0 <= nueva_posicion[0] - 1 < len(tablero)) and (0 <= nueva_posicion[1] - 1 < len(tablero[0])) and (nueva_posicion not in visitado) and tablero[nueva_posicion[0]-1][nueva_posicion[1]-1] != 'X':   
                                cola.append((nueva_posicion, distancia + 1))
                                visitado.add(nueva_posicion)
    
    ############# Heurística 1  ##################
    def heuristica_1(self, estado:Estado):
        """Distancias a las casillas de interes"""
        tablero = self.cargar_tablero_desde_csv()
        dist_domicilio = 0
        dist_centro = 0
        i = 0
        j = 0 
        # Si tiene pacientes a recoger, calcular al distancia a todos los que le quedan y sumarlos 
        if len(estado.pacientes_por_recoger['N']) != 0 :
            for i in range(0, len(estado.pacientes_por_recoger['N'])):
                # Cuantos más domicilios tenga que recoger, más alta será la heurística. Por otro lado, cuanto más cerca este de un domicilio, mejor será la heurística
                dist = self.calcular_distancia_min(estado.ubicacion_vehiculo, estado.pacientes_por_recoger['N'][i], tablero) 
                dist_domicilio += dist
                i += 1
        if len(estado.pacientes_por_recoger['C']) !=0 :
            for i in range(0, len(estado.pacientes_por_recoger['C'])):
                # Cuantos más domicilios tenga que recoger, más alta será la heurística. Por otro lado, cuanto más cerca este de un domicilio, mejor será la heurística
                dist = self.calcular_distancia_min(estado.ubicacion_vehiculo, estado.pacientes_por_recoger['C'][i], tablero) 
                dist_domicilio += dist
                j += 1
        h_domicilios = dist_domicilio 

        # Cuantos más pacientes le queden por recoger, mayor sera la heurística. Con esto queremos favorecer que primero recoga a todos los pacientes y despues vaya a los centros 
        # Si se han recogido todos, solo será la distancia al centro, si no se aumentara la heurística en función de los pacientes que quedan por recoger 
        dist_centro_no_contagioso = self.calcular_distancia_min(estado.ubicacion_vehiculo, self.centros[1], tablero)
        dist_centro = dist_centro_no_contagioso + len(estado.pacientes_por_recoger['N']) 
        dist_centro_contagioso = self.calcular_distancia_min(estado.ubicacion_vehiculo, self.centros[0], tablero)
        dist_centro += dist_centro_contagioso + len(estado.pacientes_por_recoger['C']) 
        h_centro = dist_centro 

        if estado.pacientes_a_bordo[0] == 0 and estado.pacientes_a_bordo[1] == 0 and len(estado.pacientes_por_recoger['C']) ==0 and len(estado.pacientes_por_recoger['N']) == 0:
            # Ya ha llevado a todos los pacientes a los centros, se procede a dirigirse al parking. la h_centro = 0
            h_centro = 0
            
        dist_parking = self.calcular_distancia_min(estado.ubicacion_vehiculo, self.parking, tablero)
        h_parking = dist_parking 
        
        heuristica = h_domicilios + h_centro + h_parking
        estado.h = heuristica
        return estado


    def generar_sucesores_h1(self,key, value, i): 
        if key == 'C':
            if value[i] in self.estado_actual.pacientes_por_recoger['C']: 
                # Hay que recoger al paciente y cambiar los pacientes a bordo y pacientes por recoger
                por_recoger = copy.deepcopy(self.estado_actual.pacientes_por_recoger)
                por_recoger['C'].remove(value[i])
                a_bordo = (self.estado_actual.pacientes_a_bordo[0] ,self.estado_actual.pacientes_a_bordo[1]+ 1)
            else: # Pasa por la casilla C pero sin recoger al paciente
                a_bordo = self.estado_actual.pacientes_a_bordo
                por_recoger = self.estado_actual.pacientes_por_recoger
        elif key == 'N':
            # Hay que recoger al paciente y cambiar los pacientes a bordo y pacientes por recoger
            if value[i] in self.estado_actual.pacientes_por_recoger['N']: 
                por_recoger = copy.deepcopy(self.estado_actual.pacientes_por_recoger)
                por_recoger['N'].remove(value[i])
                a_bordo = (self.estado_actual.pacientes_a_bordo[0]+ 1, self.estado_actual.pacientes_a_bordo[1])
            else: # Pasa por la casilla N pero sin recoger al paciente
                a_bordo = self.estado_actual.pacientes_a_bordo
                por_recoger = self.estado_actual.pacientes_por_recoger
        elif key == 'CC':
            # Cambiar los pacientes a bordo que sean contagiosos por 0, ya que los deja
            if self.estado_actual.pacientes_a_bordo[1] != 0:
                a_bordo = (self.estado_actual.pacientes_a_bordo[0], 0)
            else: 
                a_bordo = self.estado_actual.pacientes_a_bordo
            por_recoger = self.estado_actual.pacientes_por_recoger
                        
        elif key == 'CN':
            # Cambiar los pacientes a bordo que sean contagiosos por 0, ya que los deja
            if self.estado_actual.pacientes_a_bordo[0] != 0:
                a_bordo = (0, self.estado_actual.pacientes_a_bordo[1])
            else: 
                a_bordo = self.estado_actual.pacientes_a_bordo
            por_recoger = self.estado_actual.pacientes_por_recoger
        elif key == 'P':
            a_bordo = self.estado_actual.pacientes_a_bordo
            por_recoger = self.estado_actual.pacientes_por_recoger
        else: # Cualquier numero
            a_bordo = self.estado_actual.pacientes_a_bordo
            por_recoger = self.estado_actual.pacientes_por_recoger

        sucesores_nuevos = self.obtener_hijos(value[i][0], value[i][1])
        nuevo_estado = Estado(sucesores_nuevos, value[i], a_bordo, por_recoger, 50, key,  self.estado_actual.g + 1, 'h', self.estado_actual)
        nuevo_estado = self.heuristica_1(nuevo_estado)
        f = nuevo_estado.h + nuevo_estado.g 

        return nuevo_estado, f
    
    ############# Heurística 2  ##################
    def heuristica_2(self, estado:Estado):
        """Energia entre casillas con limitaciones de energía, capacidad y orden de pacientes"""
        tablero = self.cargar_tablero_desde_csv()
        dist_domicilio_no_contagiosos = 0
        dist_domicilio_contagiosos = 0

        # Si esta a tope de pacientes no contagiosos, no hay que calcular su valor heurístico 
        if estado.pacientes_a_bordo[0] < self.no_contagiosos_max or (estado.pacientes_a_bordo[1] == 0 and (estado.pacientes_a_bordo[0] < self.no_contagiosos_max + self.contagiosos_max)): 
                if len(estado.pacientes_por_recoger['N']) != 0 :
                    for i in range(0, len(estado.pacientes_por_recoger['N'])):
                        # Cuantos más domicilios tenga que recoger, más alta será la heurística. Por otro lado, cuanto más cerca este de un domicilio, mejor será la heurística
                        dist = self.calcular_energia_min(estado.ubicacion_vehiculo, estado.pacientes_por_recoger['N'][i], tablero) * 2
                        dist_domicilio_no_contagiosos += dist
    
        if len(estado.pacientes_por_recoger['C']) !=0 :
            # Se penalizar que recoja contagiosos mientras que queden no contagiosos por recoger 
            for i in range(0, len(estado.pacientes_por_recoger['C'])):
                # Cuantos más domicilios tenga que recoger, más alta será la heurística. Por otro lado, cuanto más cerca este de un domicilio, mejor será la heurística
                dist = self.calcular_energia_min(estado.ubicacion_vehiculo, estado.pacientes_por_recoger['C'][i], tablero) 
                dist_domicilio_contagiosos += dist
        dist_domicilio = dist_domicilio_no_contagiosos + dist_domicilio_contagiosos  
        h_domicilios = dist_domicilio * 5

        # Cuantos más pacientes le queden por recoger, mayor sera la heurística. Con esto queremos favorecer que primero recoga a todos los pacientes y despues vaya a los centros 
        # Si se han recogido todos, solo será la distancia al centro, si no se aumentara la heurística en función de los pacientes que quedan por recoger 
        dist_centro_no_contagioso = self.calcular_energia_min(estado.ubicacion_vehiculo, self.centros[1], tablero) + len(estado.pacientes_por_recoger['N']) * 5
        dist_centro_contagioso = self.calcular_energia_min(estado.ubicacion_vehiculo, self.centros[0], tablero) + len(estado.pacientes_por_recoger['C']) * 5
        # En el caso de que lleve pacientes contagiosos ira antes a un CC
        if estado.pacientes_a_bordo[1] != 0:
            dist_centro_contagioso == dist_centro_contagioso * 5
        h_centro = (dist_centro_no_contagioso + dist_centro_contagioso) 

        if estado.pacientes_a_bordo[0] == 0 and estado.pacientes_a_bordo[1] == 0 and len(estado.pacientes_por_recoger['C']) ==0 and len(estado.pacientes_por_recoger['N']) == 0:
            # Ya ha llevado a todos los pacientes a los centros, se procede a dirigirse al parking. la h_centro = 0
            dist_parking = self.calcular_energia_min(estado.ubicacion_vehiculo, self.parking, tablero)
            h_parking = dist_parking 
            h_centro = 0
        elif estado.pacientes_a_bordo[0]!= 0 or estado.pacientes_a_bordo[1] !=0 or len(estado.pacientes_por_recoger['C']) !=0 or len(estado.pacientes_por_recoger['N']) != 0:
            # Todavía quedan pacientes por llevar, pero hay que darle valor a la h_parking, la distancia maxima entre dos puntos cada uno en una esquina  
            dist_parking = (len(tablero) - 1) + (len(tablero[0]) - 1)
            h_parking = dist_parking * 3

        heuristica = h_domicilios + h_centro + h_parking 
        estado.h = heuristica
        return estado

    def generar_sucesores_h2(self, key, value, i, heuristica):
        energia = 0 
        f = 0
        coste = 1 
        energia = 1
        if key == 'C':
            # Si ha llegado al máximo de pacientes contagiosos o el paciente de ese domicilio ya ha sido recogido, se quedan igual las listas de pacientes
            if self.estado_actual.pacientes_a_bordo[1] >= self.contagiosos_max or not (value[i] in self.estado_actual.pacientes_por_recoger['C']):
                a_bordo = self.estado_actual.pacientes_a_bordo
                por_recoger = self.estado_actual.pacientes_por_recoger
            elif value[i] in self.estado_actual.pacientes_por_recoger['C']: 
                por_recoger = copy.deepcopy(self.estado_actual.pacientes_por_recoger)
                por_recoger['C'].remove(value[i])
                a_bordo = (self.estado_actual.pacientes_a_bordo[0] ,self.estado_actual.pacientes_a_bordo[1]+ 1)
        elif key == 'N':
            # Si ha llegado al máximo de pacientes contagiosos o el paciente de ese domicilio ya ha sido recogido o ya hay algún contagioso en la ambulancia
            if (self.estado_actual.pacientes_a_bordo[0] == self.no_contagiosos_max and self.estado_actual.pacientes_a_bordo[1] != 0) or not (value[i] in self.estado_actual.pacientes_por_recoger['N']) or (self.estado_actual.pacientes_a_bordo[1] != 0):
                a_bordo = self.estado_actual.pacientes_a_bordo
                por_recoger = self.estado_actual.pacientes_por_recoger
            elif value[i] in self.estado_actual.pacientes_por_recoger['N'] and ((self.estado_actual.pacientes_a_bordo[0] <= self.no_contagiosos_max + self.contagiosos_max) and self.estado_actual.pacientes_a_bordo[1] == 0): 
                por_recoger = copy.deepcopy(self.estado_actual.pacientes_por_recoger)
                por_recoger['N'].remove(value[i])
                a_bordo = (self.estado_actual.pacientes_a_bordo[0]+ 1, self.estado_actual.pacientes_a_bordo[1])
        elif key == 'CC':
            if self.estado_actual.pacientes_a_bordo[1] != 0:
                a_bordo = (self.estado_actual.pacientes_a_bordo[0], 0)  # Cambiar los pacientes a bordo que sean contagiosos por 0, ya que los deja
            else: 
                a_bordo = self.estado_actual.pacientes_a_bordo
            por_recoger = self.estado_actual.pacientes_por_recoger
        elif key == 'CN':
            if self.estado_actual.pacientes_a_bordo[0] != 0 and self.estado_actual.pacientes_a_bordo[1] == 0:
                a_bordo = (0, self.estado_actual.pacientes_a_bordo[1]) # Cambiar los pacientes a bordo que sean no contagiosos por 0, ya que los deja
            else: 
                a_bordo = self.estado_actual.pacientes_a_bordo
            por_recoger = self.estado_actual.pacientes_por_recoger
        elif key == 'P':
            a_bordo = self.estado_actual.pacientes_a_bordo
            por_recoger = self.estado_actual.pacientes_por_recoger
        else: 
            try:
                numero = int(key)  # Intenta convertir la key a un número
                # Acción para keys numéricas
                energia = numero 
                coste = numero  
                a_bordo = self.estado_actual.pacientes_a_bordo
                por_recoger = self.estado_actual.pacientes_por_recoger
            except ValueError: # Acción por defecto si la key no es ni una cadena válida ni un número
                print(key, "key no reconocida")

        tablero = self.cargar_tablero_desde_csv()
        sucesores_nuevos = self.obtener_hijos(value[i][0], value[i][1])
        nuevo_estado = Estado(sucesores_nuevos, value[i], a_bordo, por_recoger, self.estado_actual.energia - energia, key,  self.estado_actual.g + coste, 'h', self.estado_actual)
        if self.calcular_energia_min(value[i], self.parking, tablero) > nuevo_estado.energia:
            nuevo_estado = None # Si es mayor no se va a generar el estado 
        if nuevo_estado:    
            if heuristica == '2':
                nuevo_estado = self.heuristica_2(nuevo_estado)
            elif heuristica =='3':
                nuevo_estado = self.heuristica_3(nuevo_estado)
            elif heuristica == '4':
                nuevo_estado = self.heuristica_4(nuevo_estado)
            f = nuevo_estado.h + nuevo_estado.g 
        return nuevo_estado, f
    
    def calcular_energia_min(self, pos_inicio: tuple, pos_final: tuple, tablero):
        movimientos = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        # Usar BFS para encontrar el camino más corto
        cola = deque([(pos_inicio, 0)])  # La cola almacena la posición y la distancia desde el inicio
        visitado = set()
        while cola:
            actual, distancia = cola.popleft()
            visitado.add(actual)
            if actual == pos_final:
                return distancia
            for movimiento in movimientos:
                nueva_posicion = (actual[0] + movimiento[0], actual[1] + movimiento[1])
                if (0 < nueva_posicion[0] < len(tablero) + 1):
                    if (0 < nueva_posicion[1] < len(tablero)+ 1 ):
                        if nueva_posicion not in visitado:
                # Verificar si la nueva posición está dentro del tablero y no ha sido visitada
                            if (0 <= nueva_posicion[0] - 1 < len(tablero)) and (0 <= nueva_posicion[1] - 1 < len(tablero[0])) and (nueva_posicion not in visitado) and tablero[nueva_posicion[0]-1][nueva_posicion[1]-1] != 'X':
                                energia = self.obtener_tipo(tablero, nueva_posicion[0], nueva_posicion[1])
                                cola.append((nueva_posicion, distancia + energia))
                                visitado.add(nueva_posicion)

    ############# Heurística 3  ##################
    def heuristica_3(self, estado:Estado):
        """Cambio en el orden de recogida de los pacientes"""
        tablero = self.cargar_tablero_desde_csv()
        dist_domicilio_no_contagiosos = 0
        dist_domicilio_contagiosos = 0

        # Si esta a tope de pacientes no contagiosos, no hay que calcular su valor heurístico 
        if estado.pacientes_a_bordo[0] < self.no_contagiosos_max or (estado.pacientes_a_bordo[1] == 0 and (estado.pacientes_a_bordo[0] < self.no_contagiosos_max + self.contagiosos_max)): 
                if len(estado.pacientes_por_recoger['N']) != 0 :
                    for i in range(0, len(estado.pacientes_por_recoger['N'])):
                        dist = self.calcular_distancia_min(estado.ubicacion_vehiculo, estado.pacientes_por_recoger['N'][i], tablero) 
                        dist_domicilio_no_contagiosos += dist

        if len(estado.pacientes_por_recoger['C']) !=0 :
            for i in range(0, len(estado.pacientes_por_recoger['C'])):
                # Cuantos más domicilios tenga que recoger, más alta será la heurística. Por otro lado, cuanto más cerca este de un domicilio, mejor será la heurística
                dist = self.calcular_distancia_min(estado.ubicacion_vehiculo, estado.pacientes_por_recoger['C'][i], tablero) * 2
                dist_domicilio_contagiosos += dist
        dist_domicilio = dist_domicilio_no_contagiosos + dist_domicilio_contagiosos  
        h_domicilios = dist_domicilio * 5 

        # Cuantos más pacientes le queden por recoger, mayor sera la heurística. Con esto queremos favorecer que primero recoga a todos los pacientes y despues vaya a los centros 
        # Si se han recogido todos, solo será la distancia al centro, si no se aumentara la heurística en función de los pacientes que quedan por recoger 
        dist_centro_no_contagioso = self.calcular_distancia_min(estado.ubicacion_vehiculo, self.centros[1], tablero) + len(estado.pacientes_por_recoger['N']) * 5
        dist_centro_contagioso = self.calcular_distancia_min(estado.ubicacion_vehiculo, self.centros[0], tablero) + len(estado.pacientes_por_recoger['C']) * 5
        # En el caso de que lleve pacientes contagiosos ira antes a un CC
        if estado.pacientes_a_bordo[1] != 0:
            dist_centro_contagioso == dist_centro_contagioso * 3
        h_centro = (dist_centro_no_contagioso + dist_centro_contagioso) 

        if estado.pacientes_a_bordo[0] == 0 and estado.pacientes_a_bordo[1] == 0 and len(estado.pacientes_por_recoger['C']) ==0 and len(estado.pacientes_por_recoger['N']) == 0:
            # Ya ha llevado a todos los pacientes a los centros, se procede a dirigirse al parking, la h_centro = 0
            dist_parking = self.calcular_distancia_min(estado.ubicacion_vehiculo, self.parking, tablero)
            h_parking = dist_parking 
            h_centro = 0
        elif estado.pacientes_a_bordo[0]!= 0 or estado.pacientes_a_bordo[1] !=0 or len(estado.pacientes_por_recoger['C']) !=0 or len(estado.pacientes_por_recoger['N']) != 0:
            # Todavía quedan pacientes por llevar, pero hay que darle valor a la h_parking, la distancia maxima entre dos puntos cada uno en una esquina  
            dist_parking = (len(tablero) - 1) + (len(tablero[0]) - 1)
            h_parking = dist_parking *3 

        heuristica = h_domicilios + h_centro + h_parking 
        estado.h = heuristica
        return estado

    ############# Heurística 4 ##################
    def heuristica_4(self, estado:Estado):
        """Relajamos la restricción de la capacidad """
        tablero = self.cargar_tablero_desde_csv()
        dist_domicilio_no_contagiosos = 0
        dist_domicilio_contagiosos = 0
        self.no_contagiosos_max = inf 
        self.contagiosos_max = inf

        # Si esta a tope de pacientes no contagiosos, no hay que calcular su valor heurístico 
        if estado.pacientes_a_bordo[0] < self.no_contagiosos_max or (estado.pacientes_a_bordo[1] == 0 and (estado.pacientes_a_bordo[0] < self.no_contagiosos_max + self.contagiosos_max)): 
                if len(estado.pacientes_por_recoger['N']) != 0 :
                    for i in range(0, len(estado.pacientes_por_recoger['N'])):
                        # Cuantos más domicilios tenga que recoger, más alta será la heurística. Por otro lado, cuanto más cerca este de un domicilio, mejor será la heurística
                        dist = self.calcular_energia_min(estado.ubicacion_vehiculo, estado.pacientes_por_recoger['N'][i], tablero)
                        dist_domicilio_no_contagiosos += dist

        if estado.pacientes_a_bordo[1] < self.contagiosos_max:
            if len(estado.pacientes_por_recoger['C']) !=0 :
                # Voy a penalizar que recoja contagiosos mientras que queden no contagiosos por recoger 
                for i in range(0, len(estado.pacientes_por_recoger['C'])):
                    # Cuantos más domicilios tenga que recoger, más alta será la heurística. Por otro lado, cuanto más cerca este de un domicilio, mejor será la heurística
                    dist = self.calcular_energia_min(estado.ubicacion_vehiculo, estado.pacientes_por_recoger['C'][i], tablero) 
                    dist_domicilio_contagiosos += dist
        dist_domicilio = dist_domicilio_no_contagiosos + dist_domicilio_contagiosos  
        h_domicilios = dist_domicilio 

        # Cuantos más pacientes le queden por recoger, mayor sera la heurística. Con esto queremos favorecer que primero recoga a todos los pacientes y despues vaya a los centros 
        # Si la ambulancia va a tope no se suma el recargo de tener pacientes pendientes por recoger
        dist_centro_no_contagioso = self.calcular_energia_min(estado.ubicacion_vehiculo, self.centros[1], tablero) 
        dist_centro_contagioso = self.calcular_energia_min(estado.ubicacion_vehiculo, self.centros[0], tablero) 
        # En el caso de que lleve pacientes contagiosos ira antes a un CC
        
        h_centro = (dist_centro_no_contagioso + dist_centro_contagioso) 

        if estado.pacientes_a_bordo[0] == 0 and estado.pacientes_a_bordo[1] == 0 and len(estado.pacientes_por_recoger['C']) ==0 and len(estado.pacientes_por_recoger['N']) == 0:
             # Ya ha llevado a todos los pacientes a los centros, se procede a dirigirse al parking. la h_centro = 0
            dist_parking = self.calcular_energia_min(estado.ubicacion_vehiculo, self.parking, tablero)
            h_parking = dist_parking 
            h_centro = 0
        elif estado.pacientes_a_bordo[0]!= 0 or estado.pacientes_a_bordo[1] !=0 or len(estado.pacientes_por_recoger['C']) !=0 or len(estado.pacientes_por_recoger['N']) != 0:
            # Todavía quedan pacientes por llevar, pero hay que darle valor a la h_parking, la distancia maxima entre dos puntos cada uno en una esquina  
            dist_parking = self.calcular_distancia_min((len(tablero) , len(tablero[0]) ), (1,1), tablero) 
            h_parking = dist_parking  

        heuristica = h_domicilios + h_centro + h_parking 
        estado.h = heuristica
        return estado

    ################# Algoritmo A estrella y metodos asociados #################
    def algoritmo_A_estrella(self, heuristica):
        """Implementación del algoritmo A*"""
        # sacar de problema.estado inicial la fn, para usarlo como key en el diccionario open , las keys tienen que estar ordenadas según su valor heuristico
        open = {self.estado_actual.h + self.estado_actual.g: [self.estado_actual]}
        # En la lista open iran segun su valor de fn, que sera la key 
        exito = False
        close = []
        k = 0

        while not exito: 
            estado = self.obtener_primer_elemento(open)
            self.estado_actual = estado
            if estado.h == 0:
                exito = True
            else: 
                hash_estado_actual = self.hash_estado(self.estado_actual)
                close.append(hash_estado_actual) # Lo metemos en la cerrada
                open[self.estado_actual.h + self.estado_actual.g].remove(self.estado_actual) # Lo sacamos de abierta
                if not open[self.estado_actual.h + self.estado_actual.g]: # Borramos la clave y la lista si estan vacias, ahorra tiempo de ejecución
                    del open[self.estado_actual.h + self.estado_actual.g]

                sucesores = self.estado_actual.sucesores
                for key, value in sucesores.items():
                    # Si hay valores en esa key entramos dentro a recorrer los nodos, si esta vacia pasamos a la siguiente key
                    if len(value)!= 0:
                        for i in range(len(value)): 
                            k +=1
                            if heuristica == '1':
                                nuevo_estado, f = self.generar_sucesores_h1(key,value, i)
                            if heuristica == '2'or heuristica == '3' or heuristica == '4':
                                nuevo_estado, f = self.generar_sucesores_h2(key,value, i, heuristica)
                            if nuevo_estado:
                                hash_nuevo_estado = self.hash_estado(nuevo_estado)
                                intro = True
                                for j in range(0,len(close)):
                                    if close[j] == hash_nuevo_estado: # Esta en la lista cerrada, no hay que meterlo
                                        intro = False
                                clave = self.buscar_estado(open, nuevo_estado)
                                if clave == None:
                                    intro = True 
                                elif f < clave:
                                    self.eliminar_open(clave, open, nuevo_estado)
                                    intro = True
                                elif f == clave:
                                    intro = False
                                elif f > clave: 
                                    intro = False 
                                if intro:
                                    open = self.ordenar_abierta(open, f, nuevo_estado)
                  
        return self.estado_actual, k # Será el estado final 

    def obtener_primer_elemento(self, open):
        for key in open:
            if open[key]:
                return open[key][0]
            
    def hash_estado(self, estado):
        mini_estado = (tuple(estado.ubicacion_vehiculo), tuple(estado.pacientes_a_bordo),tuple(estado.pacientes_por_recoger), estado.energia, estado.tipo)
        return hash(mini_estado)
    
    def eliminar_open(self, clave, open, estado):
        if clave in open:
            lista_estados = open[clave]
            if estado in lista_estados:
                lista_estados.remove(estado)
            if not open[clave]:
                del open[clave]
      
    def ordenar_abierta(self, open, f, estado):
        # Introduce el estado en la lista abierta segun su función f y si ya esta no lo introduce 
        if f in open.keys():
            for i in open[f]:
                if i == estado:
                    return open
            open[f].append(estado)
        else:
            open[f] = [estado]
            open = OrderedDict(sorted(open.items()))
            open = dict(open)
        
        return open 
    
    def buscar_estado(self, diccionario, estado_buscado):
        for key, lista_estados in diccionario.items():
            for estado in lista_estados:
                if estado == estado_buscado:
                    return key  # Devuelve la clave donde se encontró el estado
        return None  # Devuelve None si el estado no se encuentra en el diccionario

    ############ Métodos para la representación de la solución ###########
    def reconstruir_camino(self, estado_final):
        camino = [estado_final.ubicacion_vehiculo] # Sigue el enlace del padre hasta llegar al estado inicial
        while estado_final.padre is not None:
            estado_final = estado_final.padre
            camino.append(estado_final.ubicacion_vehiculo)
        camino.reverse()  # Invierte la lista para que esté en el orden correcto (estado inicial al estado final)
        return camino
    
    def reconstruir_camino_estados(self, estado_final):
        camino = [estado_final] # Sigue el enlace del padre hasta llegar al estado inicial
        while estado_final.padre is not None:
            estado_final = estado_final.padre
            camino.append(estado_final)
        camino.reverse() # Invierte la lista para que esté en el orden correcto (estado inicial al estado final)
        return camino
    
    def escribir_solucion(self, estados, nombre_archivo, heuristica):
        nombre_archivo = f"{nombre_archivo}-{heuristica}.output"
        with open(nombre_archivo, 'w') as archivo:
            for estado in estados:
                coordenadas = estado.ubicacion_vehiculo
                valor_celda = estado.tipo
                carga_vehiculo = estado.energia
                linea = f"({coordenadas[0]},{coordenadas[1]}):{valor_celda}:{carga_vehiculo}\n"
                archivo.write(linea)


    def escribir_stats(self, tiempo, nombre_archivo, camino, heuristica, nodos_expandidos):
        nombre_archivo = f"{nombre_archivo}-{heuristica}.stat"
        with open(nombre_archivo, 'w') as archivo:
            archivo.write(f'Tiempo total: {tiempo}\n')
            archivo.write(f'Coste total: {self.estado_actual.g}\n')
            archivo.write(f'Longitud del plan: {len(camino)}\n')
            archivo.write(f'Nodos expandidos: {nodos_expandidos}\n')

    def obtener_tipo(self,tablero, fila, columna):
            if 0 <= (fila -1) < len(tablero) and 0 <= (columna -1) < len(tablero[0]):
                valor = tablero[fila - 1][columna -1]
                try:
                    return int(valor)  # Intentar convertir a entero
                except ValueError:
                    return 1  # Si no se puede convertir, devolver el valor original (cadena)
                
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python ASTARTraslados.py <path mapa.csv> <num-h>")
        sys.exit(1)
    tiempo_inicio = time.time()
    file_path = sys.argv[1]
    heuristica = sys.argv[2]
    
    problema = Problema(file_path)

    estado_solucion, nodos_expandidos = problema.algoritmo_A_estrella(heuristica)
    camino = problema.reconstruir_camino(estado_solucion)
    estados = problema.reconstruir_camino_estados(estado_solucion)
    problema.escribir_solucion(estados, file_path, heuristica)

    tiempo_final = time.time()
    tiempo= tiempo_final - tiempo_inicio
    problema.escribir_stats(tiempo, file_path, camino, heuristica, nodos_expandidos)
    