# Stress-testing the resilience of the Austrian healthcare system using agent-based simulation

We use an agent-based model to simulate shocks to the healthcare system by randomly removing doctors from the underlying network. The repository contains the codes used for the paper below.

Reference:

_Kaleta, M., Lasser, J., Dervic, E., Yang, L., Sorger, J., Lo Sardo, R., Thurner, S., Klimek, P. (2022). Stress-testing the resilience of the Austrian healthcare system using agent-based simulation.(adress)_

Note the simulation results data is available in the following repository: https://doi.org/10.17605/OSF.IO/H5E9A.

## Contents
The repository contains the ```Code``` folder that contains necessary scripts to run the simulations and analyze and visualize the results. Within this folder you will find the additional folders ```data```and ```figures``` containing sample data and the figures expected to be prodiced from sample data. An additional ```README``` in this folder gives detailed information about how to run the scripts to recreate the results of the paper. 

The ```figures``` folder does not contain Figure 1 since it was created using screenshots of a visualisation webpage of an accompanying project.

## Requirements
To download and install the libraries necessary to run the code in this repository, run

`pip install -r requirements.txt`
