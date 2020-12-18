'''!
@brief This file contains functions that are used by DASH_Sim.
'''

import os
import csv
import fnmatch
import sys

import env.multiagent_ds3.common as common

trace_list = [common.TRACE_FILE_SYSTEM, common.TRACE_FILE_TASKS, common.TRACE_FILE_FREQUENCY, common.TRACE_FILE_PES, common.TRACE_FILE_TEMPERATURE, common.TRACE_FILE_LOAD, common.TRACE_FILE_TEMPERATURE_WORKLOAD]

def update_PE_utilization_and_info(PE, current_timestamp):
    '''!
    Update the PE utilization.
    @param PE: PE to be evaluated
    @param current_timestamp: Current timestamp
    '''
    lower_bound = current_timestamp-common.sampling_rate             # Find the lower bound for the time window_list under consideration

    completed_info = []
    running_info = []
    for task in common.TaskQueues.completed.list:
        #print('Time %s:'%current_timestamp, task.start_time, task.finish_time, task.PE_ID)
        if task.PE_ID == PE.ID:
            if ((task.start_time < lower_bound) and (task.finish_time < lower_bound)):
                continue
            elif ((task.start_time < lower_bound) and (task.finish_time >= lower_bound)):
                completed_info.append(lower_bound)
                completed_info.append(task.finish_time)
            else:
                completed_info.append(task.start_time)
                completed_info.append(task.finish_time)
            #print('Time %s:'%current_timestamp,'completed',completed_info, 'Task', task.ID, 'PE', PE.ID)

    for task in common.TaskQueues.running.list:
        #print('Time %s:'%current_timestamp, task.start_time, task.PE_ID)
        if task.PE_ID == PE.ID:
            if (task.start_time < lower_bound):
                running_info.append(lower_bound)
            else:
                running_info.append(task.start_time)
                task_start_time = task.start_time
            running_info.append(current_timestamp)
            #print('Time %s:'%current_timestamp,'running',running_info, 'Task', task.ID, 'PE', PE.ID)
    merged_list = completed_info + running_info
    # get the utilization for the PE
    sum_of_active_times  = sum([merged_list[i*2+1] - merged_list[i*2] for i in range(int(len(merged_list)/2))])
    PE.utilization = (sum_of_active_times/common.sampling_rate) / PE.capacity
    # print(PE.ID, PE.utilization)

    full_list = [PE.ID, PE.utilization, current_timestamp]
    info_list = [0 if i > (len(merged_list)-1) else merged_list[i] for i in range(12)]
    full_list.extend(info_list)

    PE.info = info_list

    # if (common.DEBUG_SIM):
    #     print('Time %s: for PE-%d'%(current_timestamp,PE.ID),PE.info)


def trace_frequency(timestamp):
    '''!
    Trace method for saving the frequency variations.
    @param timestamp: Current timestamp
    '''
    if (common.TRACE_FREQUENCY):
        create_header = False
        if not (os.path.exists(common.TRACE_FILE_FREQUENCY)):
            # Create the CSV header
            create_header = True
        with open(common.TRACE_FILE_FREQUENCY, 'a', newline='') as csvfile:
            trace = csv.writer(csvfile, delimiter=',')
            if create_header == True:
                header_list = ['Timestamp']
                for idx, current_cluster in enumerate(common.ClusterManager.cluster_list):
                    if current_cluster.type != "MEM":
                        header_list.append('f_PE_' + str(idx))
                        header_list.append('N_PE_' + str(idx))
                trace.writerow(header_list)
            data = [timestamp]
            for idx, current_cluster in enumerate(common.ClusterManager.cluster_list):
                if current_cluster.type != "MEM":
                    data.append(current_cluster.current_frequency / 1000)
                    data.append(current_cluster.num_active_cores)
            trace.writerow(data)

def trace_tasks(task, PE, task_time, total_energy):
    '''!
    Trace method for saving statistics about the tasks.
    @param task: Task to be traced
    @param PE: Current PE
    @param task_time: Task's execution time
    @param total_energy: Task's total energy consumption
    '''
    if (common.TRACE_TASKS):
        create_header = False
        if not (os.path.exists(common.TRACE_FILE_TASKS.split(".")[0] + "__" + str(common.trace_file_num) + ".csv")):
            # Create the CSV header
            create_header = True
        with open(common.TRACE_FILE_TASKS.split(".")[0] + "__" + str(common.trace_file_num) + ".csv", 'a', newline='') as csvfile:
            trace = csv.writer(csvfile, delimiter=',')
            if create_header == True:
                trace.writerow(['DVFS policy', 'Task ID', 'PE', 'Exec. Time (us)', 'Energy (J)'])
            trace.writerow([common.ClusterManager.cluster_list[PE.cluster_ID].DVFS, task.ID, common.ClusterManager.cluster_list[PE.cluster_ID].name, task_time, total_energy])

def trace_system():
    '''!
    Trace method for saving statistics related to the system, i.e., the whole simulation.
    '''
    if (common.TRACE_SYSTEM):
        create_header = False
        if not (os.path.exists(common.TRACE_FILE_SYSTEM.split(".")[0] + "__" + str(common.trace_file_num) + ".csv")):
            # Create the CSV header
            create_header = True
        with open(common.TRACE_FILE_SYSTEM.split(".")[0] + "__" + str(common.trace_file_num) + ".csv", 'a', newline='') as csvfile:
            trace = csv.writer(csvfile, delimiter=',')
            if create_header == True:
                trace.writerow(['Job List', 'DVFS mode', 'N_little', 'N_big', 'Exec. Time (us)', 'Cumulative Exec. Time (us)', 'Energy (J)'])
            DVFS_mode_list = []
            for DVFS_config in common.DVFS_cfg_list:
                if DVFS_config == "performance":
                    DVFS_mode_list.append("P")
                elif DVFS_config == "powersave":
                    DVFS_mode_list.append("LP")
                elif DVFS_config == "ondemand":
                    DVFS_mode_list.append("OD")
                elif str(DVFS_config).startswith("constant"):
                    split = str(DVFS_config).split('-')
                    DVFS_mode_list.append("C" + split[1])
            if common.simulation_mode == "validation":
                trace.writerow([common.current_job_list, DVFS_mode_list, common.gen_trace_capacity_little, common.gen_trace_capacity_big,
                                common.results.execution_time, common.results.execution_time, common.results.energy_consumption])
            elif common.simulation_mode == "performance":
                if len(common.job_list) == 1:
                    job_list = common.current_job_list
                else:
                    job_list = common.job_list
                trace.writerow([job_list, DVFS_mode_list, common.gen_trace_capacity_little, common.gen_trace_capacity_big,
                                common.results.execution_time - common.warmup_period, common.results.cumulative_exe_time,
                                common.results.cumulative_energy_consumption])

def trace_PEs(timestamp, PE):
    '''!
    Trace method for saving statistics related to the PEs.
    @param timestamp: Current timestamp
    @param PE: PE to be traced
    '''
    if (common.TRACE_PES):
        create_header = False
        if not (os.path.exists(common.TRACE_FILE_PES)):
            # Create the CSV header
            create_header = True
        with open(common.TRACE_FILE_PES, 'a', newline='') as csvfile:
            dataset = csv.writer(csvfile, delimiter=',')
            if create_header == True:
                dataset.writerow(['Timestamp', 'PE', 'Info'])
            dataset.writerow([timestamp, PE.ID, PE.info])

def trace_temperature(timestamp):
    '''!
    Trace method for saving the temperature variations.
    @param timestamp: Current timestamp
    '''
    if (common.TRACE_TEMPERATURE):
        create_header = False
        if not (os.path.exists(common.TRACE_FILE_TEMPERATURE)):
            # Create the CSV header
            create_header = True
        with open(common.TRACE_FILE_TEMPERATURE, 'a', newline='') as csvfile:
            dataset = csv.writer(csvfile, delimiter=',')
            if create_header == True:
                dataset.writerow(['Timestamp', 'Snippet', 'Temperature', 'Throttling_state'])
            dataset.writerow([timestamp, common.current_job_list, max(common.current_temperature_vector), common.throttling_state])

def trace_load(timestamp, PEs):
    '''!
    Trace method for saving the load variations
    @param timestamp: Current timestamp
    @param PEs: List of PEs
    '''
    if (common.TRACE_LOAD):
        create_header = False
        if not (os.path.exists(common.TRACE_FILE_LOAD)):
            # Create the CSV header
            create_header = True
        with open(common.TRACE_FILE_LOAD, 'a', newline='') as csvfile:
            dataset = csv.writer(csvfile, delimiter=',')
            if create_header == True:
                header_list = ['Timestamp', 'Snippet']
                for idx, current_cluster in enumerate(common.ClusterManager.cluster_list):
                    if current_cluster.type != "MEM":
                        header_list.append('N_tasks_PE_' + str(idx))
                header_list.append('N_tasks_total')
                dataset.writerow(header_list)
            data = [timestamp, common.current_job_list]
            total_num_tasks = 0
            for idx, current_cluster in enumerate(common.ClusterManager.cluster_list):
                if current_cluster.type != "MEM":
                    num_tasks = get_num_tasks_being_executed(current_cluster, PEs)
                    data.append(num_tasks)
                    total_num_tasks += num_tasks
            data.append(total_num_tasks)
            dataset.writerow(data)

def get_current_job_list():
    '''!
    Get the current snippet.
    @return Current snippet
    '''
    # Get the current job list based on the snippet ID while injecting jobs
    if common.job_list != []:
        return common.job_list[common.snippet_ID_exec]
    else:
        return common.job_list

def get_num_tasks_being_executed(cluster, PEs):
    '''!
    Get the number of tasks that are being executed.
    @param cluster: Current cluster
    @param PEs: List of PEs
    @return Number of tasks being executed
    '''
    # Get the number of tasks currently being executed in the cluster
    num_tasks = 0
    for PE_ID in cluster.PE_list:
        if not PEs[PE_ID].idle:
            num_tasks += 1
    return num_tasks

def get_cluster_utilization(cluster, PEs):
    '''!
    Get the cluster utilization.
    @param cluster: Current cluster
    @param PEs: List of PEs
    @return Cluster utilization
    '''
    # Get the cluster utilization
    utilization = 0
    for PE_ID in cluster.PE_list:
        utilization += PEs[PE_ID].utilization
    return utilization / len(cluster.PE_list)

def clean_traces():
    '''!
    Remove old trace files.
    '''
    for trace_name in trace_list:
        if os.path.exists(trace_name):
            os.remove(trace_name)
    # Remove old traces generated in parallel
    for trace_name in trace_list:
        file_list = fnmatch.filter(os.listdir('.'), trace_name.split(".")[0] + '__*.csv')
        for f in file_list:
            os.remove(f)

def clean_policies():
    '''!
    Remove old policy files.
    '''
    file_list = fnmatch.filter(os.listdir('.'), '*.pkl')
    for f in file_list:
        os.remove(f)

def init_variables_at_sim_start() :
    '''!
    Initialize config variables.
    '''
    common.snippet_start_time = common.warmup_period
    common.snippet_ID_inj = -1
    common.snippet_ID_exec = 0
    common.snippet_throttle = -1
    common.snippet_temp_list = []
    common.snippet_initial_temp = [common.T_ambient,
                                   common.T_ambient,
                                   common.T_ambient,
                                   common.T_ambient,
                                   common.T_ambient]
    common.current_temperature_vector = [common.T_ambient,  # Indicate the current PE temperature for each hotspot
                                         common.T_ambient,
                                         common.T_ambient,
                                         common.T_ambient,
                                         common.T_ambient]
    common.B_model = []
    common.job_counter_list = [0]*len(common.current_job_list)
    common.throttling_state = -1
