import sys
import constraint as c
from itertools import combinations
import csv
import os

def leer_archivo(path):
    with open(path, 'r') as archivo:
        # Lee la primera línea para obtener filas y columnas, que las declaramos globales
        global filas
        global columnas
        dimensiones = archivo.readline().strip().split('x')
        filas = int(dimensiones[0])
        columnas = int(dimensiones[1])
         
        # Lee la segunda línea y obtiene las tuplas
        linea_tuplas = archivo.readline().strip()[3:]  # Ignora "PE:"
        tuplas = [tuple(map(int, tupla.split(','))) for tupla in linea_tuplas.strip('()').split(')(') if tupla]

        lista_tnu_tcu = []
        lista_c_x = []

        # TSU = 1 // Eléctricas = 1
        for linea in archivo:
            # Dividir la línea en partes usando '-' como separador
            partes = linea.strip().split('-')

            # Verificar si es TNU o TSU y agregar el valor correspondiente a la primera lista
            if partes[1] == 'TNU':
                lista_tnu_tcu.append(0)
            elif partes[1] == 'TSU':
                lista_tnu_tcu.append(1)

            # Verificar si es C o X y agregar el valor correspondiente a la segunda lista
            if partes[2] == 'C':
                lista_c_x.append(1)
            elif partes[2] == 'X':
                lista_c_x.append(0)

        if len(lista_tnu_tcu) > filas *columnas:
            raise Exception("Hay más ambulancias que plazas disponibles")
    return tuplas, lista_tnu_tcu, lista_c_x

def crear_dominios(filas, columnas):
    lista = []
    for i in range(1, filas+1):
        for j in range(1, columnas+1):
            lista.append((i,j))
        
    return lista

def comprobar_distribucion(var1, var2):
    # var1 TSU, var2 TNU
    if var1[0] != var2[0]:
        return True
    else:
        return var1[1] > var2[1]

def comprobar_adyacentes(*lista):
    for i in range(0, len(lista)):
        variable = lista[i] # var = (x,y)
        for j in range (0, len(lista)):
            if variable != lista[j] and variable[0] == 1 and ((variable[0] + 1)  == lista[j][0]) and (variable[1] == lista[j][1]): # Caso limite de la fila 1
                return False 
            if variable != lista[j] and variable[0] == filas and ((variable[0] - 1)  == lista[j][0]) and (variable[1] == lista[j][1]): # Caso limite de la última fila
                return False 
            if variable != lista[j] and (((variable[0]-1) == lista[j][0]) or ((variable[0] + 1)  == lista[j][0])) and variable[1] == lista[j][1]: # Comprueba que dos ambulancias son adyacentes
                for k in range(0, len(lista)):
                    if variable != lista[k] and lista[k] != lista[j] and (((variable[0]-1) == lista[k][0]) or ((variable[0] + 1)  == lista[k][0])) and variable[1] == lista[k][1]:
                        return False                # Comprueba si la tercera ambulancia es adyacente para invalidar esas posiciones para las ambulancias
    return True



def solve_parking_csp(tuplas, lista_tnu_tcu, lista_c_x):
    # Iniciamos el problema a resolver
    problema = c.Problem()
   
    for j in tuplas:
        if j[0] < 0 or j[0] > filas or j[1] < 0 or j[1] > columnas:
            raise Exception(" Las plazas electricas están fuera de rango")
        
    # Add variables, teniendo en cuenta las estaciones eléctricas disponibles
    total_ambulancias = len(lista_tnu_tcu)
    lista_dom = crear_dominios(filas, columnas)
    dicc = {}

    for i in range(1, total_ambulancias+1):
        if lista_c_x[i-1] == 1:
            problema.addVariable(i, tuplas)
            dicc[i] = tuplas
        else:
            problema.addVariable(i, lista_dom)
            dicc[i] = lista_dom
    
    indices = dicc.keys()

    for j in range(1, total_ambulancias+1):
        for k in range(1, total_ambulancias+1):
            if j != k and lista_tnu_tcu[j-1] == 1 and lista_tnu_tcu[k-1] == 0:
                    problema.addConstraint(comprobar_distribucion, (j, k))
    
    problema.addConstraint(c.AllDifferentConstraint())                                  # Ninguna ambulancia tiene asignada la misma plaza de parking que otra

    problema.addConstraint(comprobar_adyacentes,indices)                                # Comprueba si las ambulancias tienen espacios adyacentes para poder maniobrar

    solucion = problema.getSolutions()
    

    return solucion

def read_and_solve_input(file_path):
    tuplas, lista1, lista2 = leer_archivo(file_path)
    solucion= solve_parking_csp(tuplas, lista1, lista2)

    generar_salida(file_path, solucion, lista1, lista2)

    return solucion

def generar_salida(file_path, soluciones, lista1, lista2):
    # Obtener el nombre del archivo sin la extensión
    nombre_base, _ = os.path.splitext(file_path)

    # Crear el nombre del archivo de salida con la extensión .csv
    archivo_salida = f"{nombre_base}.csv"
    with open(archivo_salida, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        
        # Escribir el número de soluciones encontradas
        writer.writerow(['N. Sol:', len(soluciones)])
        if len(soluciones) == 0:
            print("No hay soluciones")
        else:
            # Escribir las soluciones
            solucion = soluciones[0]
            tablero = [['−'] * columnas for _ in range(filas)]
            for vehiculo, coordenadas in solucion.items():
                tipo = lista1[vehiculo - 1]
                if tipo == 1:
                    tipo = 'TSU'
                else:
                    tipo = 'TNU'
                estado = lista2[vehiculo - 1]
                if estado == 1:
                    estado = 'C'
                else:
                    estado = 'X'

                fila = coordenadas[0] - 1
                columna = coordenadas[1] - 1  # Restar 1 para ajustar al índice base 0
                tablero[fila][columna] = f"{vehiculo}-{tipo}-{estado}"

            for fila in tablero:
                writer.writerow(fila)



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python CSPParking.py <nombre_del_archivo>")
        sys.exit(1)

    file_path = sys.argv[1]

    sol= read_and_solve_input(file_path)
    
   