'''!
@brief This file is the main() function which should be run to get the simulation results.
'''
import simpy
import configparser
import matplotlib.pyplot as plt                                                 
import random                                                                  
import numpy as np
import sys
import os
import networkx as nx
import pickle
import csv
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)


import env.multiagent_ds3.job_generator as job_generator
import env.multiagent_ds3.common as common
import env.multiagent_ds3.DASH_SoC_parser as DASH_SoC_parser
import env.multiagent_ds3.job_parser as job_parser
import env.multiagent_ds3.processing_element as processing_element
import env.multiagent_ds3.DASH_Sim_core as DASH_Sim_core
import env.multiagent_ds3.scheduler as scheduler
import env.multiagent_ds3.DASH_Sim_utils as DASH_Sim_utils


from env.multiagentenv import MultiAgentEnv



