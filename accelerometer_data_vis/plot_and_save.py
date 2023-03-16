import serial
import numpy as np
import threading
from queue import Queue
import pygame
import datetime

class Animate():


    def __init__(self) -> None:
        
        # check serial port of ESP32 device on your computer:
        self.serial_port = 'COM6'

        self.data_queue = Queue()
        self.data_arr = []
        # setup pygame window:
        pygame.init()
        self.width, self.height = 600,400
        self.padding = 20
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.running = True   

        # setup serial port:     
        self.port = serial.Serial(self.serial_port, baudrate=115200, timeout=1 )
        self.port_thread = threading.Thread(target=self.background_thread, args=(self.port,self.data_queue,))
        self.port_thread.start()
        print("serial port started")

        # open output data file:
        self.file = open('/data/'+ datetime.now.strftime("%y-%m-%d_%H-%M-%S")+'_accel_log.csv','a')
        self.file.write('timestamp x_mean x_std y_mean y_std x_mean z_std dT_mean dT_std')
        # begin animation loop:
        self.run_loop()
        


    def draw_background(self):
        num_vert_lines =  10
        num_hori_lines = 10
    
        for i in range(num_vert_lines+1): 
            y_val = i * self.height/num_vert_lines
            pygame.draw.line(self.screen,'0x9ea3a3',(0,y_val),(self.width,y_val ))
        for i in range(num_hori_lines+1):
            x_val = i * self.width/num_hori_lines
            pygame.draw.line(self.screen,'0x9ea3a3',(x_val,0),(x_val,self.height))

    def end_animation(self):
        self.port_thread.join()
        self.file.close()

    def background_thread(self, port, data_queue):
        print('inside background thread')
        while(self.running):
            data_queue.put(port.readline())

    def process_and_save(self):
        #arr = np.array(self.data_arr)

        x_trace = np.array(self.data_arr[:][0])
        y_trace = np.array(self.data_arr[:][1])
        z_trace = np.array(self.data_arr[:][2])
        t_trace = np.array(self.data_arr[:][3])

        x_max = np.max(x_trace)
        y_max = np.max(y_trace)
        x_min = np.min(x_trace)
        y_min = np.min(y_trace)
        x_trig = (x_max + x_min)/2 # cut data trace into cycles at rising edge crossing
        y_trig = (y_max + y_min)/2 # the average of heighest and lowest values

        x_cycle_count = 0
        x_cycles = [[]] # empty list of lists, with list [0] initialized
        y_cycle_count = 0
        y_cycles = [[]]

        # find avg and std for raw z and raw dT data:
        

        # iterate through data and cut into a list of cycles stored in {x/y}_cycles[]
        for i in range(len(x_trace-1)):
            x_cycles[x_cycle_count].append(x_trace[i])
            y_cycles[x_cycle_count].append(y_trace[i])
            if x_trace[i] < x_trig and x_trace[i+1] > x_trig:
                x_cycle_count += 1
            
            if y_trace[i] < y_trig and y_trace[i+1] > y_trig:
                y_cycle_count += 1
        
        # find the mean and std of peak-peak values for both x and y:
        x_pkpk = []
        y_pkpk = []
        for cycle in x_cycles:
            x_pkpk.append(max(cycle) - min(cycle))
        for cycle in y_cycles:
            y_pkpk.append(max(cycle) - min(cycle))

        x_mean = np.mean(x_pkpk)
        x_std = np.std(x_pkpk)
        y_mean = np.mean(y_pkpk)
        y_std = np.std(y_pkpk)
        z_mean = np.mean(z_trace)
        z_std = np.std(z_trace)
        t_mean = np.mean(t_trace)
        t_std = np.std(t_trace)
        timestamp = datetime.now.strftime("%y-%m-%d_%H-%M-%S")
        self.file.write(timestamp+' '+x_mean+' '+x_std+' '+y_mean+' '+y_std+' '+z_mean+' '+z_std+' '+t_mean+' '+t_std)
        
        
        #TODO:
        # simplify things so you are just dealing with x and y traces independently( outside of arrays)
        # find pk-pk for each cycle for x and y, and save avg and std to file
        # for z, save max, min, std of all samples to file
        # for dT, save max, min, std of all samples to file
        # try using Pandas csv write to save out with nice headings? or just init the heading when you open the file...
        # get this done quickly! remove plotting code until further notice. 
            
                


        # reset data array:
        self.data_arr = []

    def run_loop(self):
        while self.running:
            # poll for events
            # pygame.QUIT event means the user clicked X to close your window
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # fill the screen with a color to wipe away anything from last frame
            self.screen.fill('0xaae6e0')
            # RENDER YOUR GAME HERE
            self.draw_background()
            
            # get data from background thread:
            while(self.data_queue.empty() == False):
                raw_data = (self.data_queue.get().decode('utf-8')) # decode binary string from serial port
                data = list(map(int, raw_data.strip("\r\n").split(" "))) # turn string into array of integers
                
                # convert data from uV to g based on accelerometer specs
                g_data = list(map(lambda x: round(((x/1000000) - 1.65)/.3 , 3),data))
                g_data[3] = data[3] # reset last element to microseconds between samples
                self.data_arr.append(g_data)
                if(len(self.data_arr) == 1000):
                    print(g_data)
                    self.process_and_save()

            # flip() the display to put your work on screen
            pygame.display.flip()
            self.clock.tick(120)  # limits FPS to 120

        pygame.quit()
        self.end_animation()


if __name__=='__main__':
    my_animation = Animate()