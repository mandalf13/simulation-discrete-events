import math
import queue
import sys
import numpy as np

class KojoSimulator:
    def __init__(self):
        self.end_time=660 # minuto en el que cierra el restaurante
        self.current_time=0 # tiempo actual de la simulación
        self.next_arrival=0 # tiempo del próximo arribo de un cliente
        self.clients_count=0 # cantidad de clientes que han llegado (se usa como índice)
        self.arrivals=[] # la posición i contiene el tiempo de arribo del cliente i+1
        self.departures=[] # la posición i contiene el tiempo de salida de la cola del cliente i+1
        self.current_state=[] # [N, c1, c2, c3] donde N es la cantidad de clientes siendo atendidos y c_i denota el cliente siendo atendido por el empleado i 
        self.employees_state=[] # esta lista lleva los tiempos actuales de preparación de comida para cada empleado
        self.clients=queue.Queue() # cola de los clientes que no han sido atendidos

    def start_simulation(self, arrival_rate, peak_hours_rate, helper=False, showlog = False):
        if peak_hours_rate <= arrival_rate:
            raise Exception("La frecuencia en horario pico debe ser mayor que en horario regular")
        max_value = sys.maxsize
        self.next_arrival = self.generate_exponential(arrival_rate)
        if helper:
            self.employees_state=[max_value,max_value,max_value]
            self.current_state=[0,0,0,0]
        else:
            self.employees_state=[max_value,max_value]
            self.current_state=[0,0,0]
        while True:
            min_value = min(self.next_arrival,min(self.employees_state)) # tiempo del próximo evento 
            # el próximo evento es la llegada de un cliente
            if self.next_arrival == min_value:
                self.current_time = self.next_arrival
                if self.is_final_state():
                    break
                elif self.current_time >= self.end_time:
                    if showlog:
                        print("!! Horario de cierre. No se pueden atender más clientes")
                        print("Clientes en cola: " + str(self.clients.qsize()))     
                        print("Clientes siendo atendidos: " + str(self.current_state[0]))   
                    self.next_arrival = max_value                                         
                    continue
                else:
                    self.clients_count += 1
                    self.arrivals.append(self.current_time)
                    #standard_time = self.convert_to_hours()
                    if showlog:
                        print("... Cliente " + str(self.clients_count) + " llega en " + str(self.current_time))
                        #print("... Cliente "+ str(self.clients_count) + " llega a las  " +  str(standard_time[0]) + ":" + str(standard_time[1]))
                    if self.is_peak_time: # en horario pico
                        self.next_arrival = self.current_time + self.generate_exponential(peak_hours_rate)
                        if helper and self.current_state[0] < 3:
                            self.departures.append(self.current_time)
                            self.generate_order(self.clients_count, 3)
                        elif not helper and self.current_state[0] < 2:
                            self.departures.append(self.current_time)
                            self.generate_order(self.clients_count, 2)
                        else:
                            self.departures.append(0)
                            self.clients.put(self.clients_count)                                 
                    else: # fuera de horario pico
                        self.next_arrival = self.current_time + self.generate_exponential(arrival_rate)
                        if self.current_state[0] < 2:
                            self.departures.append(self.current_time)
                            self.generate_order(self.clients_count, 2)
                        else:
                            if self.current_state[1] == 0 or self.current_state[2] == 0:
                                self.departures.append(self.current_time)
                                self.generate_order(self.clients_count, 2)
                            else:    
                                self.departures.append(0)
                                self.clients.put(self.clients_count)        
            # el próximo evento es la salida de un cliente      
            else:  
                employee_index = self.employees_state.index(min_value) # índice del empleado que terminó el pedido
                self.current_time = min_value
                self.current_state[0] -= 1
                self.current_state[employee_index + 1] = 0
                self.employees_state[employee_index] = max_value
                #standard_time = self.convert_to_hours()
                if showlog:
                    print("... Cliente " + str(client_index+1) + " sale en " + str(self.current_time))
                    #print("... Cliente "+ str(client_index+1) + " sale a las  " +  str(standard_time[0]) + ":" + str(standard_time[1]))
                if self.is_final_state():
                    break
                elif not self.clients.empty() and self.current_time < self.end_time: # hay clientes en la cola y no es horario de cierre
                    if self.is_peak_time() and helper: # si es horario pico y tenemos ayudante
                        new_client = self.clients.get()
                        self.departures[new_client-1] = self.current_time
                        self.generate_order(new_client, 3)
                    else: # si solamente podemos asignar pedidos a los dos primeros empleados
                        if self.current_state[0] < 2:
                            new_client = self.clients.get()
                            self.departures[new_client-1] = self.current_time
                            self.generate_order(new_client, 2)  
                        else:
                            if self.current_state[1] == 0 or self.current_state[2] == 0: # si quedó un empleado principal libre
                                new_client = self.clients.get()
                                self.departures[new_client-1] = self.current_time
                                self.generate_order(new_client, 2)    
                else:
                    continue          
            
    def reset(self):
        self.current_time=0
        self.next_arrival=0
        self.clients_count=0
        self.arrivals=[]
        self.departures=[]
        self.current_state=[]
        self.employees_state=[]
        self.clients=queue.Queue()

    # función que devuelve True si es horario pico y False en caso contrario
    def is_peak_time(self):
        return (self.current_time >= 90 and self.current_time <= 210) or (self.current_time >= 420 and self.current_time <= 540)
    
    # la simulación se encuentra en estado final si no hay clientes siendo atendidos y el tiempo de arribo del próximo cliente sobrepasa el tiempo de cierre  
    def is_final_state(self):
        return self.current_time >= self.end_time and self.current_state[0]==0 #and self.clients.empty()
    
    # convierte el tiempo actual al formato estándar de horas 
    def convert_to_hours(self):
        time = round(self.current_time, 2)
        h = 10 + math.floor(time/60)
        m1 = (time * 100) % 100
        m = math.floor((m1 * 60) / 100)
        return (h,m)

    def generate_exponential(self, rate):
        u = np.random.uniform()
        return -(1/rate)*math.log(u) 

    # genera la orden de un cliente para un empleado desocupado
    # el parámetro index se usa para especificar la disponibilidad del tercer empleado
    def generate_order(self, client, index):
        order =  np.random.randint(0,2) # 0 para sandwiches y 1 para sushi
        t = 0
        for i in range(1, index+1):
            if self.current_state[i] == 0:
                if order == 0:
                    t = np.random.uniform(3, 5)
                else:
                    t = np.random.uniform(5, 8)
                self.employees_state[i-1]=self.current_time + t
                self.current_state[i]=client
                self.current_state[0] += 1
                break           

    # imprime el porcentaje de clientes q demoraron más de 5 minutos en el local
    def get_stats(self):
        total_clients = 0
        dissatisfied_clients = 0
        l = len(self.arrivals)
        for i in range(l):
            if self.departures[i] != 0:
                total_clients += 1
                if self.departures[i] - self.arrivals[i] > 5:
                    dissatisfied_clients += 1
        return round((dissatisfied_clients * 100) / total_clients, 1)

if __name__ == "__main__":
    inputs = [(0.5, 1), (0.333, 0.5), (0.25, 0.333), (0.2, 0.25), (0.125, 0.2)]
    simulator = KojoSimulator()
    output = open("docs/output.txt", 'w')
    output.write('        Inputs         |          Results         \n')
    output.write('lambda | lambda (peak) | 2 employees | 3 employees\n\n')
    for i in range(len(inputs)):
        p1 = 0 # Suma de los porcentajes calculados para simulaciones sin tercer empleado
        p2 = 0 # Suma de los porcentajes calculados para simulaciones con ayudante
        for j in range(50):        
            simulator.start_simulation(inputs[i][0], inputs[i][1])
            stat = simulator.get_stats()
            p1 += stat
            simulator.reset()
            simulator.start_simulation(inputs[i][0], inputs[i][1], helper=True)
            stat = simulator.get_stats()
            p2 += stat
            simulator.reset()
        r1 = round(p1 / 50, 2)
        r2 = round(p2 / 50, 2)
        output.write("{0}   |   {1}   |   {2}%   |   {3}%\n".format(str(inputs[i][0]), str(inputs[i][1]), str(r1), str(r2)))
    output.close()    

