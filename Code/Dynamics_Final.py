import pandas as pd
from scipy import sparse
import numpy as np
from os.path import join


class doctor:
    '''
    Class of all doctors of one speciality. Contains info on number of
    patients, maximum capacity, municipality, district and federal state,
    and during the patient displacements also number of incoming patients,
    the still available places and the excess.
    '''
    def __init__(self, ID, N_patients, capacity, gemeinde):
        self.originalID = ID
        self.NumOfPatients = N_patients
        self.capacity = capacity
        self.gemeinde = gemeinde

        self.incoming = 0
        self.availability = 0
        self.excess = 0
        
        # add infos on location
        self.bezirk = int(str(self.gemeinde)[0:3])
        self.state = int(str(self.gemeinde)[0])



def DataSetup(doc_file, data_src, sep, keep_dis, max_distance, min_pats):

    '''
    Define class of doctors and their characteristics, find the correct the 
    adjacency matrix and distance matrix entries based on parameter setting.
    Additionally, keep track of patients starting location to be able to 
    check lost patients on federal state level.
    '''
    
    # get relevant doctor information to construct the doctors
    doctor_info = pd.read_csv(join(data_src, doc_file), delimiter=sep)
    print('total # of patients: ',doctor_info['number_of_patients'].sum())
    
    # stop if file is empty, otherwise error
    if len(doctor_info)<=1:
        docs = []
        adj = []
        docs_removed = []
        return docs, adj, docs_removed
    
    doc_IDs = doctor_info['adj_index']


    # load distance matrix between all docs and select only the connections 
    # below the max_distance
    dist_docs = sparse.load_npz(join(data_src, 'DistanceMatrixDocs.npz'))
    dist_docs = dist_docs.todense()


    # load adjacency matrix and filter for relevant doctors with correct distances
    adj = sparse.load_npz(join(data_src, 'adj_all_doctors.npz'))
    adj = adj.todense()
    
    # set connections with less than min_pats to zero
    adj[adj<min_pats] = 0
    
    # set connections further than max distance to zero
    adj[dist_docs>max_distance] = 0
    adj = adj[np.ix_(doc_IDs, doc_IDs)]
    
    # select also correct docs in the docs-distance matrix
    dist_docs = dist_docs[np.ix_(doc_IDs, doc_IDs)]
    dist_docs = np.asarray(dist_docs)
    

    

    # NOTE: 
    # "number_of_patients" can either be the number of total patients seen by
    # the doctor within a time frame (yearly, quarterly, ...) or the number of 
    # unique patients seen within a time frame.
    # "capacity" can be estimated in different ways, for example a flat capacity
    # increase over the recorded number of patient visits, an opening-hour based
    # estimation or an estimation based on the highest capacities seen in the
    # data for a given speciality.
    
    # track disconnected docs for removed_capacity
    if keep_dis == 0:
        # remove disconnected, set diagonal to zero
        adj_check = adj.copy()                 # create copy for checking connections
        np.fill_diagonal(adj_check, 0)         # fill copy diagonal with 0
        
        #Checks whether the doctors are connected to any other throught the 
        #patient-sharing network. If not they are removed since they will not 
        #participate in the simulation (ignoring teleporation)
    
        hasOutDegree = np.any(adj_check, axis=0).transpose()
        hasInDegree = np.any(adj_check, axis=1)
        
        # network should be symmetrical and logical_and == logical_or
        not_disconnected = np.asarray(np.logical_and(hasOutDegree, 
                                                    hasInDegree)).squeeze()
        
        doctor_info_removed = doctor_info[~not_disconnected]
        doc_IDs_removed = doctor_info_removed['adj_index']
        capacities_removed = doctor_info_removed['capacity'].values
        N_patients_removed = doctor_info_removed['number_of_patients'].values
        doc_gemeinde_removed = doctor_info_removed['gemeinde'].values # location values
        
        # construct removed doctors
        docs_removed = [doctor(ID, N_pat, capacity, gemeinde) for ID, N_pat, capacity, gemeinde in \
            zip(doc_IDs_removed, N_patients_removed, capacities_removed, doc_gemeinde_removed)]
            
        # remove entries of disconnected doctors from adjacency matrix and data
        adj = adj[np.ix_(not_disconnected, not_disconnected)]
        dist_docs = dist_docs[np.ix_(not_disconnected, not_disconnected)]
        doctor_info = doctor_info[not_disconnected]
        doc_IDs = doctor_info['adj_index']
        capacities = doctor_info['capacity'].values
        N_patients = doctor_info['number_of_patients'].values
        doc_gemeinde = doctor_info['gemeinde'].values # location values
        
        # construct doctors
        docs = [doctor(ID, N_pat, capacity, gemeinde) for ID, N_pat, capacity, gemeinde in \
                zip(doc_IDs, N_patients, capacities, doc_gemeinde)]
            
        
          
        ### save patient location for certain % of removals
        patmat = np.zeros((doctor_info.number_of_patients.sum(),2))
        x = doctor_info.adj_index[0]*np.ones(doctor_info.number_of_patients[0])
        for i in range(1,len(doctor_info.adj_index)):
            y = doctor_info.adj_index[i]*np.ones(doctor_info.number_of_patients[i])
            x = np.concatenate((x,y))
        patmat[:,0] = x
        patmat[:,1] = x
        
        ### save patient federal state location to track lost patients per state
        patloc_state = np.zeros((doctor_info.number_of_patients.sum(),1))
        x = doctor_info.gemeinde[0]*np.ones(doctor_info.number_of_patients[0])
        for i in range(1,len(doctor_info.gemeinde)):
            y = doctor_info.gemeinde[i]*np.ones(doctor_info.number_of_patients[i])
            x = np.concatenate((x,y))
        x = [int(str(g)[0]) for g in x]
        patloc_state[:,0] = x
        
    
    else:
        # no removed docs if keep_dis=True, set empty
        docs_removed = []
    
        doc_IDs = doctor_info['adj_index']
        capacities = doctor_info['capacity'].values
        N_patients = doctor_info['number_of_patients'].values
        doc_gemeinde = doctor_info['gemeinde'].values # location values

        # construct doctors
        docs = [doctor(ID, N_pat, capacity, gemeinde) for ID, N_pat, capacity, gemeinde in \
                zip(doc_IDs, N_patients, capacities, doc_gemeinde)]
            
        ### save patient location for certain % of removals
        patmat = np.zeros((doctor_info.number_of_patients.sum(),2))
        x = doctor_info.adj_index[0]*np.ones(doctor_info.number_of_patients[0])
        for i in range(1,len(doctor_info.adj_index)):
            y = doctor_info.adj_index[i]*np.ones(doctor_info.number_of_patients[i])
            x = np.concatenate((x,y))
        patmat[:,0] = x 
        patmat[:,1] = x
        
        ### save patient federal state location to track lost patients per state
        patloc_state = np.zeros((doctor_info.number_of_patients.sum(),1))
        x = doctor_info.gemeinde[0]*np.ones(doctor_info.number_of_patients[0])
        for i in range(1,len(doctor_info.gemeinde)):
            y = doctor_info.gemeinde[i]*np.ones(doctor_info.number_of_patients[i])
            x = np.concatenate((x,y))
        x = [int(str(g)[0]) for g in x]
        patloc_state[:,0] = x
        
        
    return docs, adj, docs_removed, dist_docs, patmat, patloc_state




def equilibrate(docs,adj,dist_docs,rem_indices,alpha,maxSteps,rng,shock,patmat,totalNumOfPats,\
                lost_summed,origin_distances,max_distance,max_dist_trials):
    
    '''
    Function for the doctor removal step and the patient re-location.
    Create dictionary of all patients to keep track of number of displacement
    step, starting location, location of new doctor and distance moved.
    '''

    N_patients = np.asarray([d.NumOfPatients for d in docs])


    ### original IDs of the removed doc
    Origin_ID = np.asarray([d.originalID for d in docs])


    # patients from the failed doctor(s) that are now on the lookout for new
    # doctors to treat them. 
    displaced_pats = {}
    displaced_pats['locations'] = np.hstack([np.asarray([i] * int(NPats)) for \
            i, NPats in zip(rem_indices, N_patients[rem_indices])]).astype(int)
        
        
    ### add info on starting doctor Gemeinde ID to check if they've moved too far 
    displaced_pats['start_docID'] = patmat[patmat[:,1]==int(Origin_ID[rem_indices]),0]
        
        
    ### write info on original ID of removed doc indisplaced_pats (would need to change
    ### that if more docs are removed)
    displaced_pats['origin_ID'] = np.asarray([int(Origin_ID[rem_indices])] * \
        len(displaced_pats['locations']))
        
        

    # True: looking for a doctor, False: not looking for a doctor
    displaced_pats['searching'] = np.asarray([True] * \
        len(displaced_pats['locations']))
    # initialize the number of patient displacements with zero
    displaced_pats['displacements'] = np.asarray([0] * \
        len(displaced_pats['locations']))
        
    # initialize the distance of patient displacements with zero
    displaced_pats['distance'] = np.asarray([0] * \
        len(displaced_pats['locations']))

    adj[:, rem_indices] = 0
    t = 0
    lost = 0                # num of lost patients per doctor removal step
    incorrect_summed = 0    # num of "incorrectly" displaced patients (moved >max_dist [km])


    # write original location (removed doc) in column
    displaced_pats['origin_locations'] = np.asarray(displaced_pats['locations'].copy())
    
    ### add variable for loop in step()
    displaced_pats['correct'] = np.asarray([0] * len(displaced_pats['locations']))

    while True:

        displaced_pats, lost, incorrect_summed = step(displaced_pats, adj, docs, lost, rng, 
            alpha, maxSteps, dist_docs, origin_distances,max_distance,max_dist_trials,incorrect_summed)
 
        
        # if there are no more patients looking for a doctor: break 
        if not np.any(displaced_pats['searching']):
            break

        
        # set location of patients who are still looking for a new doc to original
        displaced_pats['locations'][displaced_pats['searching']] =  \
            np.asarray(displaced_pats['origin_locations'][displaced_pats['searching']].copy())
        displaced_pats['distance'][displaced_pats['searching']] = \
            np.asarray([0] * len(displaced_pats['distance'][displaced_pats['searching']]))
        
        t+=1



    ### update the new ID of docs where patients went to
    displaced_pats['new_ID'] = np.asarray([docs[i].originalID for i in displaced_pats['locations']])
    ### set new ID to 99999 for patients who moved more than max_steps
    displaced_pats['new_ID'][displaced_pats['displacements'] > maxSteps] = 99999
    
  

    ### update patient location: for all patients who where at rem_doc before get an update
    ### if no patients displaced, skip this
    if len(displaced_pats['new_ID'])>0:
        updatedlocs = np.asarray(displaced_pats['new_ID'])
        patmat[patmat[:,1]==np.unique(displaced_pats['origin_ID'])[0],1] = updatedlocs
    

    # calculate average distance using DistanceMatrix over all patients that
    # have actually moved from one doc to another but below maxSteps
    avg_distance = np.asarray(displaced_pats['distance'])[displaced_pats['displacements'] <= maxSteps]
    
        
    if len(avg_distance)<1:
        avg_distance_mean = np.nan
    else:
        avg_distance_mean = np.mean(avg_distance)
        
    
    ### need to remove only the failed doc, but not the disconnected ones!
    not_failed = np.setdiff1d(np.arange(0,len(adj)),rem_indices)
    
    adj = adj[np.ix_(not_failed, not_failed)]
    dist_docs = dist_docs[np.ix_(not_failed, not_failed)]

    for i in rem_indices:
        del docs[i]
                    
    return docs, adj, displaced_pats['displacements'].mean(), lost, avg_distance_mean, dist_docs, patmat, int(Origin_ID[rem_indices]),incorrect_summed




def pick_doctors_to_remove(doctors, N, rng):
    '''
    Pick N random doctors to be removed. 
    '''
    rem_index = rng.choice(range(len(doctors)), N)
    
    return rem_index




def find_targets(prob_matrix, rng):
    ''''
    Given a matrix with the absolute number of shared patients between doctors
    and a list of items it selects an item based on 
    the column of probability matrix.
    '''
    
    prob_matrix = prob_matrix.transpose() # doctors X patients matrix
    s = prob_matrix.cumsum(axis=0) 
    s = s / s.max(axis=0)
    r = rng.random(prob_matrix.shape[1])
    k = (s < r).sum(axis=0) # indices of target doctors
        
    return np.asarray(k)



def step(displaced_pats, adj, docs, lost, rng, alpha, maxSteps, dist_docs, origin_distances,max_distance,max_dist_trials,incorrect_summed):
    '''
    Function to displace patients and check whether they have been accepted
    or not. Also updates the number of patients at doctors who accept new
    patients. After MAX_STEPS, patients stop looking for a new doctor and
    become lost.
    '''
    
    # there are doctors with 0 patients but nonzero capacity in the data. To
    # keep these doctors, we have to check whether there are any displaced
    # patients if a doctor is removed first.
    
    if any(displaced_pats['searching']) == True:
        # Update number of displacements: all initially displaced patients have
        # made at least one step to look for a new doctor
        displaced_pats['displacements'][displaced_pats['searching']] += 1 
        
        ### need to exclude all patients who have already reached their max_steps
        lost += len(displaced_pats['searching'][displaced_pats['displacements'] > maxSteps])
        displaced_pats['searching'][displaced_pats['displacements'] > maxSteps] = False  
            
        
        
    ### only displace if there are still patients who are searching!
    if any(displaced_pats['searching']) == True:
        ### start by setting all patients as not 'correct' = 0
        displaced_pats['correct'] = np.asarray([0] * len(displaced_pats['locations']))
        

        incorrect = len(displaced_pats['correct'][(displaced_pats['searching']==True)&(displaced_pats['correct']==0)])
        counter = 0  # counter for max dist trias
        
        while (incorrect > 0) & (counter <= max_dist_trials):
            ### determine target locations of displaced patients
            # creates a patients X doctors matrix where every row is the number
            # of patients the patient's original doctor shared with other doctors
            # (not normalized yet)
            prob_weights = adj[displaced_pats['locations'][(displaced_pats['searching']==True)&(displaced_pats['correct']==0)]] 
    
            
            # Assign target nodes (doctors) to each displaced patient, based on a
            # probability given by the number of shared patients of each possible 
            # target doctor with the failed doctor
            targets = find_targets(prob_weights, rng)
            
     
            # Choose whether to teleport
            teleport = rng.random(targets.shape) < alpha 
            targets[teleport] = rng.choice(range(len(docs)))
    
            
            ### Update locations of patients
            displaced_pats['locations'][(displaced_pats['searching']==True)&(displaced_pats['correct']==0)] \
                        = targets.squeeze()
                        
            ### Update distance for now. If patients dont stay, reset to zero
            rem_doc_location = np.unique(displaced_pats['origin_locations'][(displaced_pats['searching']==True)&(displaced_pats['correct']==0)])
            new_dist = np.asarray([dist_docs[rem_doc_location,j].item() for j in displaced_pats['locations'][(displaced_pats['searching']==True)&(displaced_pats['correct']==0)]])
            displaced_pats['distance'][(displaced_pats['searching']==True)&(displaced_pats['correct']==0)] = new_dist.squeeze()
                        
                        
            ### get distance between new doctor and the starting location of patients
            current_docID = np.asarray([docs[cur].originalID for cur in np.asarray(displaced_pats['locations'])]) 
            start_end_dist = np.asarray([origin_distances[int(st),int(en)].item() for st,en in \
                                         zip(np.asarray(displaced_pats['start_docID']),current_docID)])
            
                
            ### those who are within distance limit, are relocated correctly
            displaced_pats['correct'][(displaced_pats['searching']==True)&(start_end_dist<=max_distance)] = np.asarray([1] * len(displaced_pats['correct'][(displaced_pats['searching']==True)&(start_end_dist<=max_distance)]))
           
            ### if counter gets to high, break while loop. Patients can 
            ### now be relocated to doctors further than MAX_DIST
            if counter < max_dist_trials:
                ### the others are sent back to their original location
                displaced_pats['locations'][(displaced_pats['searching']==True)&(start_end_dist>max_distance)] = np.asarray(displaced_pats['origin_locations'][(displaced_pats['searching']==True)&(start_end_dist>max_distance)].copy())
                displaced_pats['distance'][(displaced_pats['searching']==True)&(start_end_dist>max_distance)] = np.asarray([0] * len(displaced_pats['distance'][(displaced_pats['searching']==True)&(start_end_dist>max_distance)]))
                    
                ### update the number of incorrect patients
                incorrect = len(displaced_pats['correct'][(displaced_pats['searching']==True)&(displaced_pats['correct']==0)])
            
                counter += 1
                
            else:
                ### update the number of incorrect patients
                incorrect = len(displaced_pats['correct'][(displaced_pats['searching']==True)&(displaced_pats['correct']==0)])
                
                counter += 1
    
        incorrect_summed += incorrect  # update number of incorrectly displaced patients


        ### empty dict to fill in patients that are looking to get accepted
        at_doc = {}

        # distribute incoming patients to doctors with free capacity
        for i, doc in enumerate(docs):
            # Determine indices of patients at location
            at_doc[i] = np.asarray(displaced_pats['locations'][displaced_pats['searching']] == i).nonzero()[0]
            
            
            
            # incoming patients
            incoming = np.asarray(displaced_pats['locations'][displaced_pats['searching']] == i).nonzero()[0]

            doc.incoming = len(incoming)

            # calculate the current availability and excess number of patients
            doc.availability = doc.capacity - doc.NumOfPatients
            doc.excess = doc.incoming - doc.availability 

            # docs that have absorbed all incoming patients have
            # zero excess (would be negative patients otherwise)
            if doc.excess <= 0 and doc.incoming > 0:

                doc.excess = 0
                doc.NumOfPatients += doc.incoming

                # patients that have been absorbed can stop looking for a new doctor
                displaced_pats['searching'][np.in1d(displaced_pats['locations'], i)] = False 

            # Skip doctors with no incoming patients and doctors that have
            # absorbed all patients and doctors that are already completely filled
            elif doc.incoming and doc.availability != 0:
                incoming = np.asarray(displaced_pats['locations'][displaced_pats['searching']] == i)  

                # fill doc up to capacity
                doc.NumOfPatients += doc.availability
                
   
                # displace patients to doctors who have free capacity (beware indexing errors)
                temp_searching = np.asarray(displaced_pats['searching'].copy())
                temp_locations = np.asarray(displaced_pats['locations'].copy())
                temp_locations_doc = temp_locations==i
                temp_searching_and_atdoc = np.logical_and(temp_searching,temp_locations_doc)
                temptrue = temp_searching_and_atdoc.nonzero()[0]
                kept2 = rng.choice(temptrue,size=doc.availability, replace=False)
                temp_searching[kept2] = False
                displaced_pats['searching'] = temp_searching

            else:
                pass

    return displaced_pats, lost, incorrect_summed
