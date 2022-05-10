__author__ = 'Jana Lasser'
__copyright__ = 'Copyright 2021, Patient Dynamics Simulation'
__credits__ = ['Jana Lasser', 'Ruggiero LoSardo','Michaela Kaleta']
__license__ = 'MIT'
__status__ = 'Dev'

# std imports
import warnings
from importlib import reload
from os.path import join
import argparse

# third party imports
import pandas as pd
import numpy as np
from scipy import sparse

# custom libraries
import Dynamics_Final as dyn    

warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser(description='Simulation of a primary care network '\
     + '\nCopyright (C) 2021 Jana Lasser & Ruggiero LoSardo & Michaela Kaleta')


parser.add_argument('-keep_dis','--keep_disconnected',type=int,\
                help='Set 1 or 0 if initially disconnected doctors should be\n'+\
                    'kept in the simulation or excluded in the beginning.',\
                default=1)    
    
parser.add_argument('-sep','--separator',type=str,\
                help='Separator used in the doctor .csv file',
                default=',')

parser.add_argument('-src','--data_src',type=str,\
                help='Path to the doctor information table and adjacency matrix.',
                default='data')

parser.add_argument('-dst','--results_dst',type=str,\
                help='Path to the directory in which results will be saved.',
                default='results')

parser.add_argument('-iter','--number_of_iterations', type=int,\
                help='Number of times every unique simulation configuration\n'+\
                    'will be run to gather statistics.',
                default=100)

parser.add_argument('-shocks','--number_of_shocks', type=int,\
                help="Number of times the system will be 'shocked', i.e. doctors\n"+\
                    "will be removed.",
                default=5000)

parser.add_argument('-remove','--number_of_removed_doctors', type=int,\
                help='Number of doctors that are removed in each shock.',
                default=1)

parser.add_argument('-alpha','--teleport_probability', type=float,\
                help='Probability of a patient to teleport to a random doctor\n'+\
                'instead of going to the most likely doctor based on shared\n'+\
                'patients, when displaced',
                default=0.15)

parser.add_argument('-ms','--max_steps', type=int,\
                help='Number of doctors a patient will visit after being\n'+\
                'displaced to try and find a new doctor. After max_steps\n'+\
                'is exceeded, the patient will give up and become "lost".',
                default=10)
    
parser.add_argument('-th','--threshold', type=float,\
                help='Threshold used for hour-based capacity calculation.',\
                default=0.9)


parser.add_argument('-seed','--seed',type=str,\
                help='Seed of the random number generator.',
                default=None)
    
parser.add_argument('-max_dist','--max_distance',type=int,\
                help='Maximal distance for patients to travel in the \n'+\
                'network (in km).',
                default=100)
    
parser.add_argument('-max_dist_trials','--max_distance_trials',type=int,\
                help='Simulation trials to reach doc within maximal distance of patients.',
                default=10)
    
parser.add_argument('-min_pats','--min_pats',type=int,\
                help='Minimum number of shared patients in adjacency matrix, \n'+\
                'otherwise entries are set to zero (filter weakest connections).',
                default=2)
    
parser.add_argument('-covid_shock','--covid_shock',type=bool,\
                help='Test larger shock with simultaneous removals.',
                default=False)
    
parser.add_argument('-shock_size','--shock_size',type=int,\
                help='Set shock size as percentage of physicians that is removed simultaneously.',
                default=10)
    
parser.add_argument('-save_locations','--save_locations',type=bool,\
                help='Save starting patient location and location \n'+\
                'after x% of doctor removals.',
                default=False)
    
parser.add_argument('-simadd','--simulation_information',type=str,\
                help='String containing additional simulation information (parallelisation)\n'+\
                     'appended to the results file.',
                default='')
    


# parse command line arguments supplied by the user
args = parser.parse_args()
data_src = args.data_src
results_dst = args.results_dst
sep = args.separator
iterations = args.number_of_iterations
shocks = args.number_of_shocks
N_remove = args.number_of_removed_doctors
alpha = args.teleport_probability
max_steps = args.max_steps
seed = args.seed
threshold = args.threshold
keep_dis = args.keep_disconnected
max_distance = args.max_distance
min_pats = args.min_pats
simadd = args.simulation_information
max_dist_trials = args.max_distance_trials
save_locs = args.save_locations
covid_shock = args.covid_shock
shock_size = args.shock_size

#seed = 42
# initialize random number generator
rng = np.random.default_rng(seed)


### list of all doctors to simulate over 
doctors = list(['AM', 'KI', 'PSY', 'ORTR', 'URO', 'HNO', 'CH', 'NEU', 'RAD', 'DER', 'GGH', 'AU', 'IM'])



### pick patient type, capacity type and timeframe
ptype = 'total'
ctype = 'hour-based'
tf = 'quarterly'
network = 'Österreich'


### lower num of iterations for covid shock
if covid_shock==True:
    iterations = 10

### loop over all medical specialties 
for doc in doctors:
    
    # load doctor info file and define siminfo for result-filename
    doc_file = 'doctor_info_bez={}_spec={}_ptype={}_ctype={}_tf={}_th={}.csv'\
        .format(network, doc, ptype, ctype, tf, threshold)  
    siminfo = '{}_{}'.format(doc,'Final')

    
    ### define results DF to save into
    results = pd.DataFrame(columns=['state','run', 'shock', 'avg_displacement',\
                                    'N_lost_patients', 'free_capacity_state',\
                                    'free_capacity_country','disconnected_capacity',\
                                    'N_lost_patients_summed','N_lost_patients_state_summed',\
                                    'avg_distance','incorrect_displacements'])

    reload(dyn)
    
    # load distance matrix between all docs that will never be changed
    origin_distances = sparse.load_npz(join(data_src, 'DistanceMatrixDocs.npz'))
    origin_distances = origin_distances.todense()
    
    ### initialize for checking covid shock
    searching_pats = []
    
    # number of times the simulation will be run to create statistics
    for i in range(0, iterations):
        
        # need to create docs and adj again for every iteration since
        # these objects are modified by the simulation
        docs, adj, disc_docs, dist_docs, patmat, patloc_state = dyn.DataSetup(doc_file, data_src, sep, keep_dis, max_distance, min_pats)

        
        ### total number of patients
        totalNumOfPats = sum([d.NumOfPatients for d in docs])
        
        
        ### total number of docs in SIM + 10% of them
        numofdocs = len(docs)
        percdocs = np.round(numofdocs/100*10,0)
        
        
        # number of times the system will be shocked in a single simulation
        # set initial free/removed capacity to NaN, in case NW is disconnected
        free_capacity_state = np.nan
        free_capacity_country = np.nan
        disc_capacity = np.nan
        lost_pats_state = np.nan
        if len(disc_docs)>0:
            disc_capacity = np.sum([d.capacity - d.NumOfPatients for d in disc_docs])
        
        lost_summed = 0    # can count lost patients overall, one value for country
        
        for shock in range(0, shocks):
            if len(docs)<=1:
                print(lost_summed + docs[0].NumOfPatients)
                break
            
            ### built-in covid-shock - remove 10% of docs simultaneously
            if covid_shock == True:
                N_remove = int(np.ceil(len(adj)*(0.01*shock_size)))
                print(N_remove)
            
            rem_indices = dyn.pick_doctors_to_remove(docs, N_remove, rng)
            
            if len(rem_indices)==0:
                break
            
            ### perform patient displacements and doctor removal 
            docs, adj, avg_displacement, lost, distance_mean, dist_docs, patmat, incorrect_summed, CS = \
                dyn.equilibrate(docs,adj,dist_docs,rem_indices,alpha,max_steps,rng,shock,patmat,\
                                totalNumOfPats,lost_summed,origin_distances,max_distance,max_dist_trials,covid_shock)
                        
            lost_summed += lost  ### update number of lost patients in country
                        
            
            ### loop over states to get info in each to create results file
            for st in np.arange(1,10,1):
                free_capacity_state = np.sum([d.capacity - d.NumOfPatients for d in docs if d.state == st])
                free_capacity_country = np.sum([d.capacity - d.NumOfPatients for d in docs])  
                lost_pats_state = len(patmat[(patloc_state[:,0]==st)&(patmat[:,1]==99999)])
                results = results.append({'state':st,'run':i + 1,
                                          'shock':shock + 1,
                                          'avg_displacement':avg_displacement,
                                          'N_lost_patients':lost,
                                          'free_capacity_state':free_capacity_state,
                                          'free_capacity_country':free_capacity_country,
                                          'disconnected_capacity':disc_capacity,
                                          'N_lost_patients_summed':lost_summed,
                                          'N_lost_patients_state_summed':lost_pats_state,
                                          'avg_distance':distance_mean,
                                          'incorrect_displacements':incorrect_summed},
                                        ignore_index = True)
            
            ### if patient locations should be saved up to some % of removed docs:
            if (shock == percdocs) and (save_locs==True):
                np.savetxt(join('locations', 'patient_locations_iter{}_shocks{}_remove{}_alpha{}_maxs{}_th{}_kd{}_maxdist{}_maxdisttrials{}_minpats{}_{}_itnr{}.csv'\
                       .format(iterations, shocks, N_remove, alpha, max_steps,
                               threshold, keep_dis, max_distance, max_dist_trials,
                               min_pats, doc, i)), patmat,delimiter = ',')
                    
            if covid_shock == True:
                if len(CS) < max_steps:
                    CS = CS + list((np.zeros(max_steps-len(CS)).astype(int)))
                searching_pats.append(CS)
                print(CS)
                break
            

        print(doc, 'removed_docs:', shock, 'iter:', i, 'free_cap_country',
              free_capacity_country,'disconnected_cap:', disc_capacity)
    
    if covid_shock == False:
        ### save results for every medical specialty
        results = results.reset_index(drop=True)
        results.to_csv(join(results_dst, 'patient_dynamics_iter{}_shocks{}_remove{}_alpha{}_maxs{}_th{}_kd{}_maxdist{}_maxdisttrials{}_minpats{}_{}_{}.csv'\
                           .format(iterations, shocks, N_remove, alpha, max_steps,
                                   threshold, keep_dis, max_distance, max_dist_trials,
                                   min_pats, siminfo, simadd)), index=False)
    elif covid_shock == True:
        np.savetxt(join(results_dst,'searching_pats_{}_iter{}_shocksize{}.csv'.format(doc,iterations,shock_size)),searching_pats,delimiter=',')
        results = results.reset_index(drop=True)
        results.to_csv(join(results_dst, 'patient_dynamics_iter{}_shocks{}_remove{}_alpha{}_maxs{}_th{}_kd{}_maxdist{}_maxdisttrials{}_minpats{}_{}_{}_covidshock.csv'\
                           .format(iterations, shocks, N_remove, alpha, max_steps,
                                   threshold, keep_dis, max_distance, max_dist_trials,
                                   min_pats, siminfo, simadd)), index=False)
        
        