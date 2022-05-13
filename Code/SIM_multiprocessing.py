# -*- coding: utf-8 -*-
"""
Created on Tue Apr  6 14:34:04 2021

@author: Michaela Kaleta
"""

# parallelisation packages
from multiprocessing import Pool
import psutil
import os



def run_command_line(param):
    '''
    Function that runs the simulation over command line.
    '''

    # simulation parameters
    iterations = 10  # beware here the total number of iteration you want to have
    shocks = 5000
    remove = 1
    alpha = 0
    max_steps = 10
    threshold = 0.9
    keep_disconnected = 1
    max_distance = 100
    max_distance_trials = 10
    min_patients = 2
    covid_shock =True
    ### in case you want a covid-shock, define shock size
    shock_size = 10
    
    print('Covid shock = ',covid_shock)
    # add batch number at end of filename
    batch = 'batch_{}'.format(param)
    
    
    # runs simulation from terminal
    os.system("python SimulatePatientDynamics_Final.py -iter {} -shocks {} -remove {} -ms {} -alpha {} -th {} -keep_dis {} -max_dist {} -max_dist_trials {} -min_pats {} -covid_shock {} -shock_size {} --simulation_information {}".format(iterations, shocks, remove, max_steps, alpha, threshold, keep_disconnected, max_distance, max_distance_trials, min_patients, covid_shock, shock_size, batch))
    
    

### how many iterations in total? total = iterations x n [batches]
n = 1  # for main sim results set n=10
if __name__ == '__main__':
    ### pick number of threads that should be used
    threads_to_use = psutil.cpu_count(logical=True) - 2
    pool = Pool(threads_to_use)
    
    ### run simulation on threads
    rel  = pool.map(run_command_line,range(1,n+1))

