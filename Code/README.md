# Healthcare resilience simulation


---
## Requirements
To run the code, some of the script requires 4 already existing data files out of which 2 (unfortunately) cannot be shared due to data protection regulations. The files "matched_and_imputed_doctors.csv" and "adj_all_doctors.npz" in the ```data``` folder contain (column_name:data_format):
* **matched_and_imputed_doctors.csv**: ("Leistungserbringer_ID":int-str-int, "gemeinde":int, "specialization":str, "N_total_yearly_patients":int, "N_unique_yearly_patients":int, "total_weekly_hours":float, "So_hours": float, "Mo_hours":float, "Di_hours":float, "Mi_hours":float, "Do_hours":float, "Fr_hours":float, "Sa_hours":float, "latitude":float, "longitude":float, "imputed":bool)   

* **adj_all_doctors.npz**: sparse adjacency matrix for N unique "Leistungserbringer_ID" with size N x N. Integer entries A_{ij} contain number of shared patients between doctors i and j within a 3 month time window. 

The other necessary files are:
* **gemliste_knz.xls**
* **municipality_geolocations.csv**

---
## Scripts order to run
To succesfully arrive at the results you need to run the script in the following order:
1. calculate_capacity_threshold.ipybn
2. municipality_distance_matrix.ipybn
3. doc_distance_matrix.ipybn
4. create_node_list.ipybn
5. prepare_doc_data_all.ipybn
6. SIM_multiprocessing.py that runs SimulatePatientDynamics_Final.py which uses the functions in Dynamics_Final.py
7. combine_batches_from_SIM.ipybn
8. benefit_risk_score.ipybn
9. analyze_results_dataframe_and_LPFC_limits.ipybn
10. final_plots_and_regression.ipybn


---
## Data preparation
In the first step, "calculate_capacity_threshold.ipybn" uses the original physicians' information to estimate capacity thresholds of different types that can be selected.
The resulting output file is stored as "matched_and_imputed_doctors_with_capacity_[].csv" with the specified threshold.

Next, we need to estimate the distances between municipalities using the script "municipality_distance_matrix.ipybn". Data for matching postal codes and municipality codes of Austrian municipalities (gemliste_knz.xls taken from Statistik Austria (http://www.statistik.at/web_de/klassifikationen/regionale_gliederungen/gemeinden/index.html)) and their geolocations (municipality_geolocations.csv, pre-existing data from different analysis) is contained in the ```data``` folder.
The output is a distance matrix between municipalities ("DistanceMatrix.csv" in ```data```). This matrix is then used in the script "doc_distance_matrix.ipybn" to calculate distances between physicians in the network. The result is another (sparse) distance matrix for the connections between doctors ("DistanceMatrixDocs.npz" in folder ```data```).

As we are using a network approach, we describe the nodes in the physicians' network with certain characteristics. A list of all nodes' descriptions is therefore created in "create_node_list.ipybn" in a file "PSNW_NodeList.csv". It will later be used to analyse the results.

In "prepare_doc_data_all.ipybn" we use "matched_and_imputed_doctors_with_capacity_[].csv" to create speciality-specific files "doctor_info_bez={}_spec={}_ptype={}_ctype={}_tf={}_th={}.csv" in the following form:

The resulting file has to contain these four columns:

| **adj_index** | **number_of_patients** | **capacity** | **municipality** |
|:--------------|:-----------------------|:-------------|:-----------------|
| int           | int                    | int          | int              |

* **adj_index**: is the index of a given doctor in the adjacency matrix (specified in the file ```adj_all_doctors.npz```, which will be subset automatically, according to the doctors you selected for your simulation. 
* **number_of_patients**: is the number of patients a given doctor treats. Here you have the choice between the unique number of patients (**N_unique** in the master data file), and the number of total patients (**N_total**). Moreover, you can choose at which time interval you want to calculate the patient number (**yearly_patients** or **quarterly_patients**).
* **capacity**: this is the maximum patient capacity of a given doctor. Here you have to specify again if you want total/unique patient numbers and pick one of the **capacity_total** or **capacity_unique** columns. Moreover you have several choices about how the capacity is estimated: **_flat** is a flat increase of the given capacity by a fraction (0.1). **hour_based** is a capacity estimation based on the opening hour data, **max** is a capacity estimation, that assigns all doctors that are not yet in the hightest 25th capacity percentile one random capacity from the highest 25%.
* **municipality**: This is the 5-digit municipality code of where that physician is located.



---
## Simulation
The main part of the agent-based model is contained in "SimulatePatientDynamics_Final.py" that runs the doctor removal simulation over all medical specialties. The necessary functions for the simulation are given in "Dynamics_Final.py", a package which is loaded within "SimulatePatientDynamics_Final.py".
To run the simulation more efficiently, we created another script that can be over command line and is able to use multiple cores/threads to speed up the many iterations of the simulations. Within this script, "SIM_multiprocessing.py", you can set the simulation parameters, the default parameters (as in the paper) are already pre-set. 
The following list shows the possible options/parameters of the simulation:

  * ```-sep SEPARATOR```: Separator used in the doctor .csv file. Default: ```;```
  * ```-src DATA_SRC```: Path to the doctor information table and adjacency matrix. Default: 'data'.
  * ```-dst RESULTS_DST```: Path to the directory in which results will be saved. Default: 'results'.
  * ```-iter NUMBER_OF_ITERATIONS```: Number of times every unique simulation configuration will be run to gather statistics. Default: 100 iterations.
  * ```-shocks NUMBER_OF_SHOCKS```: Number of times the system will be 'shocked', i.e. doctors will be removed. Default: 5000 shocks to always remove all doctors.
  * ```-remove NUMBER_OF_REMOVED_DOCTORS```: Number of doctors that are removed in each shock. Default: 1 removed doctor.
  * ```-alpha TELEPORT_PROBABILITY```: Probability of a patient to teleport to a random doctor instead of going to the most likely doctor based on shared patients, when displaced. Default: 0.15 (=15%).
  * ```-ms MAX_STEPS```: Number of doctors a patient will visit after being displaced, to try and find a new doctor. After ```MAX_STEPS``` is exceeded, the patient will give up and become "lost". Default: 10 steps.
  * ```-keep_dis KEEP_DISCONNECTED```: Set 1 or 0 if initially disconnected doctors should be kept in the simulation or excluded in the beginning. Default: 1 keep disconnected doctors.
  * ```-th THRESHOLD```: Threshold used for hour-based capacity calculation [0,1]. Default 0.9 means using top 10% of doctors used to estimate maximal capacity for remaining 90% of doctors.
  * ```-max_dist MAX_DISTANCE```: Maximal distance for patients to travel in the network from starting location (in [km] direct line connection). Default 100km.
  * ```-max_dist_trials MAX_DISTANCE_TRIALS```: Simulation trials to reach doctor within ```MAX_DISTANCE``` of patients before optionally choosing a doctor further away. Default 10.
  * ```-min_pats MIN_PATS```: Minimum number of shared patients in adjacency matrix, otherwise entries are set to zero (filter weakest connections). Default 2.
  * ```-save_locations SAVE_LOCATIONS```: Save starting patient location and location after x% of doctor removals. Default FALSE.
  * ```-verb VERBOSITY```: Verbosity level of the simulation (0, 1, 2). Default: 0, no debugging output.
  * ```-simadd SIMULATION_INFORMATION```: String containing simulation information (parallelisation) that will be appended to the results file. Default: ''.
  * ```-seed SEED```: Sets the random seed of the simulation. If the seed is set, runs with the same seed are repeatable. Default: None, i.e. every unique simulation is initialized with a new random seed.

You can run the multiprocessing simulation over the command line using the following command:
`python SIM_multiprocessing.py`

Results are saved in the specified directory (folder ```results```). The simulatio results are of the form "patient_dynamics_iter[]_shocks[]_remove[]_alpha[]_maxs[]_th[]_kd[]_maxdist[]_maxdisttrials[]_minpats[]_[]_Final_batch_[].csv" in separate batches for the multiprocessing.



---
## Analysing results
To further analyse the simulation results, we first combine the batches using "combine_batches_from_SIM.ipybn" in the ```results``` folder.

Next, we can estimate physician's risk and benefit scores with "benefit_risk_score.ipybn" that creates a table containing risk and benefit values for every doctor, saved as "Risk_Benefit_table.csv" in the ```results``` folder.

In "analyze_results_dataframe_and_LPFC_limits.ipybn" a dataframe with all simulation results (some evaluated to get the values of remaining free capacity, lost patients etc.) is created and saved as "DF_results_Final.csv". Additionally, the free capacity (FC) and lost patients (LP) results are further analysed and their state-level limits are measured and saved into another results file "FCLP_limits_[]_[].csv".

Finally, in "final_plots_and_regression.ipybn" we create figures 2, 3 and 4 of the paper using the risk and benefit score as well as the FC and LP limits on a federal state level. Figures are saved into the ```figures``` directory. 


