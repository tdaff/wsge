#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
qstat.py -- Helpers to serialise qstat output.

Reads SGE output as XML and parses into python dictionaries.

"""

from collections import OrderedDict
from subprocess import Popen, PIPE

try:
    from lxml.etree import fromstring
except ImportError:
    from xml.etree.ElementTree import fromstring


def qstat():
    """Return qstat output (job list) as a dictionary."""

    # output of jobs in xml
    qstat_str = Popen(['qstat', '-u', '*', '-xml'], stdout=PIPE).stdout.read()
    qtree = fromstring(qstat_str)

    jobs = []

    # queue info
    for job_lists in qtree:  # queue_info and job_info
        for job in job_lists:
            job_dict = {}
            for jitem in job:
                job_dict[jitem.tag] = jitem.text
            job_dict['slots'] = int(job_dict['slots'])
            jobs.append(job_dict)

    return jobs


def qstatf():
    """Return qstat -f output as a dictionary."""

    # full output of everything in xml
    qstat_args = ['qstat', '-u', '*', '-F', '-xml']
    qstat_str = Popen(qstat_args, stdout=PIPE).stdout.read()
    qtree = fromstring(qstat_str)

    all_queues = OrderedDict()
    users = OrderedDict()
    jobs = []

    # queue info
    for queue in qtree[0]:
        # queue info
        this_node = {'job_list': [],
                     'resource': {}}
        for qitem in queue:
            if qitem.tag == 'job_list':
                job_dict = {}
                for jitem in qitem:
                    job_dict[jitem.tag] = jitem.text
                job_dict['slots'] = int(job_dict['slots'])
                job_dict['JB_queue'] = this_node['name']
                job_dict['node'] = this_node['name'].split('@')[1].split('.')[0]
                if job_dict['JB_owner'] not in users:
                    users[job_dict['JB_owner']] = []
                users[job_dict['JB_owner']].append(job_dict)
                this_node['job_list'].append(job_dict)
                jobs.append(job_dict)
            elif qitem.tag == 'resource':
                this_node['resource'][qitem.attrib['name']] = qitem.text
            else:
                this_node[qitem.tag] = qitem.text

        # remove "all.q@' and '.local'
        node = this_node['name'].split('@')[1].split('.')[0]
        this_node['name'] = node
        this_node['slots_total'] = int(this_node['slots_total'])
        if node in all_queues:
            all_queues[node]['job_list'].extend(this_node['job_list'])
        else:
            all_queues[node] = this_node

    # rest of the job info
    for wait_job in qtree[1]:
        job_dict = {}
        for jitem in wait_job:
            job_dict[jitem.tag] = jitem.text
        job_dict['slots'] = int(job_dict['slots'])
        if job_dict['JB_owner'] not in users:
            users[job_dict['JB_owner']] = []
        users[job_dict['JB_owner']].append(job_dict)
        jobs.append(job_dict)

    return all_queues, users, jobs
