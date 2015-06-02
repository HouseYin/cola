#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2015-6-1

@author: chine
'''

import os
import tempfile

from cola.commands import Command
from cola.context import Context
from cola.core.utils import get_ip, import_job_desc
from cola.core.zip import ZipHandler
from cola.core.rpc import FileTransportClient, client_call

class JobCommand(Command):
    def add_arguments(self, parser):
        ip = get_ip()
        
        self.job_parser = parser.add_parser('master', help='job commands')
        self.job_parser.add_argument('-m', '--master', metavar='master address', nargs='?', default=ip,
                                     help='master connected to(in the former of `ip:port` or `ip`)')
        self.job_parser.add_argument('-l', '--list', metavar='list all jobs', action='store_true',
                                     help='list all jobs including <id> <name> and <status>' )
        self.job_parser.add_argument('-k', '--kill', metavar='kill some job', nargs='?', 
                                     help='kill job by job name')
        self.job_parser.add_argument('-u', '--upload', metavar='upload a job', nargs='?', 
                                     help='upload a job directory to the cluster')
        self.job_parser.add_argument('-r', '--run', metavar='run a job', nargs='?', const='U',
                                     help='run a job by the job id or with the `upload` command')
        self.job_parser.add_argument('-t', '--status', metavar='get the status of a job', nargs='?',
                                     help='show the status of a job, and the counters if it\'s running')
        self.job_parser.add_argument('-p', '--package', metavar='package a job running info', nargs='?',
                                     help='package the running info of a job including log and errors infos')
        
    def run(self, args):
        master_addr = args.master
        ctx = Context(is_client=True, master_addr=master_addr)
        
        if args.list is True:
            jobs = ctx.list_jobs()
            print 'list jobs at master:', ctx.master_addr
            for job_id, info in jobs.iteritems():
                print '====> job id:', job_id, ', job_name:', info['name'], ', status:', info['status']
        elif args.kill is not None:
            ctx.kill_job(args.kill)
            print 'killed job:', args.kill
        elif args.upload is not None:
            if not os.path.exists(args.upload):
                print 'upload path does not exist'
                return
            job_id = None
            try:
                job_id = import_job_desc(args.upload).uniq_name
            except:
                print 'job to upload is illegal'
                return
            
            temp_filename = tempfile.mktemp(suffix='.zip')
            ZipHandler.compress(temp_filename, args.upload, type_filters=('pyc', ))
            try:
                FileTransportClient(ctx.master_addr, temp_filename).send_file()
            finally:
                os.remove(temp_filename)
            print 'upload job finished'
            
            if args.run == 'U':
                client_call(ctx.master_addr, 'run_job', job_id, unzip=True)
        elif args.run is not None and args.run != 'U':
            client_call(ctx.master_addr, 'run_job', args.run)
        