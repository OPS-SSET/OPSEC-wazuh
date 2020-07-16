#!/usr/bin/env python

# Copyright (C) 2015-2020, Wazuh Inc.
# Created by Wazuh, Inc. <info@wazuh.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

import argparse
import os
import re
import json
from sys import exit, path, argv, stdout
from os.path import dirname
from signal import signal, SIGINT
from time import sleep

# Set framework path
path.append(dirname(argv[0]) + '/../framework')  # It is necessary to import Wazuh package

# Import framework
try:
    from wazuh import Wazuh
    from wazuh.core.agent import Agent, send_task_upgrade_module
    from wazuh.core.exception import WazuhException
    from wazuh.core import common
    import wazuh.agent
except Exception as e:
    print("Error importing 'Wazuh' package.\n\n{0}\n".format(e))
    exit()


# Functions
def signal_handler(n_signal, frame):
    print("")
    exit(1)

def print_progress(value):
    stdout.write("Sending WPK: [%-25s] %d%%   \r" % ('=' * int(value / 4), value))
    stdout.flush()

def list_outdated():
    agents = wazuh.agent.get_outdated_agents()
    if agents.total_affected_items == 0:
        print("All agents are updated.")
    else:
        print("%-6s%-35s %-25s" % ("ID", "Name", "Version"))
        for agent in agents.affected_items:
            print("%-6s%-35s %-25s" % (agent['id'], agent['name'], agent['version']))
        print("\nTotal outdated agents: {0}".format(agents.total_affected_items))

def main():
    # Capture Ctrl + C
    signal(SIGINT, signal_handler)

    # Check arguments
    if args.list_outdated:
        list_outdated()
        exit(0)

    if not args.agent:
        arg_parser.print_help()
        exit(0)
    
    agent_list = args.agent.split(",")

    if args.silent:
        args.debug = False

    use_http = False
    if args.http:
        use_http = True

    # Evaluate if the version is correct
    if args.version is not None:
        pattern = re.compile("v[0-9]+\.[0-9]+\.[0-9]+")
        if not pattern.match(args.version):
            raise WazuhException(1733, "Version received: {0}".format(args.version))

    if args.chunk_size is not None:
        if args.chunk_size < 1 or args.chunk_size > 64000:
            raise WazuhException(1744, "Chunk defined: {0}".format(args.chunk_size))

    upgrade_command_result = ""
    # Custom WPK file
    if args.file:
        upgrade_command_result = send_task_upgrade_module(command='upgrade', file_path=args.file,
                                                            agent_list=agent_list,
                                                            installer=args.execute if args.execute else "upgrade.sh",
                                                            debug=args.debug,
                                                            show_progress=print_progress if not args.silent else None,
                                                            chunk_size=args.chunk_size,
                                                            rl_timeout=-1 if args.timeout == None else args.timeout)
    # WPK upgrade file
    else:
        #prev_ver = agent.version
        upgrade_command_result = send_task_upgrade_module(command='upgrade', 
                                                            agent_list=agent_list,
                                                            wpk_repo=args.repository,
                                                            debug=args.debug, 
                                                            version=args.version,
                                                            force_upgrade=args.force,
                                                            show_progress=print_progress if not args.silent else None,
                                                            chunk_size=args.chunk_size,
                                                            rl_timeout=-1 if args.timeout == None else args.timeout, 
                                                            use_http=use_http)

    counter = 0
    
    sleep(10)

    #check if any agent start the upgrade
    agents = json.loads(upgrade_command_result.replace("\'", "\""))

    id_agents_upgrading = []
    for agent in agents:
        if not args.silent:
            print("Agent id: {0} | Error code: {1} | Data: {2} | Task id: {3}".format(agent['agent'], agent['error'], agent['data'], agent['task_id']))
            
        if agent["error"] == 0:
            id_agents_upgrading.append(agent["agent"])
    
    if id_agents_upgrading:
        #waiting for upgrade task end
        while counter < common.agent_info_retries and id_agents_upgrading:
            sleep(common.agent_info_sleep)
            
            #request state of upgrading tasks
            upgrade_result = send_task_upgrade_module(command='upgrade_result', agent_list=id_agents_upgrading, debug=args.debug)

            agents_results = json.loads(upgrade_result.replace("\'", "\""))

            if not args.silent:
                print("Cheking upgrade status: retrie {}".format(counter))             
            
            for ag in agents_results:
                #check one by one if the agent end
                if ag["status"] == "Outdated":
                    if not args.silent:
                        print("Agent upgrade failed: id: {0} status: {1}.".format(ag["agent"], ag["status"]))
                    id_agents_upgrading.remove(int(ag["agent"]))
                if ag["status"] == "Upgraded":
                    if not args.silent:
                        print("Agent upgraded: id: {0} status: {1}.".format(ag["agent"], ag["status"]))
                    id_agents_upgrading.remove(int(ag["agent"]))
            
            counter = counter + 1

        if not args.silent:
            if id_agents_upgrading:
                for a in id_agents_upgrading:
                    print("Agent not finished id: {0}".format(a))
                raise WazuhException(1716, "Timeout waiting for agent reconnection.")
            else:
                print("Upgrade process finished")
        
    else:
        if not args.silent:
            print("Error: No agent upgrading")
    

if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-a", "--agent", type=str, help="Agent ID to upgrade.")
    arg_parser.add_argument("-r", "--repository", type=str, help="Specify a repository URL. [Default: {0}]".format(
        common.wpk_repo_url))
    arg_parser.add_argument("-v", "--version", type=str, help="Version to upgrade. [Default: latest Wazuh version]")
    arg_parser.add_argument("-F", "--force", action="store_true", help="Allows reinstall same version and downgrade version.")
    arg_parser.add_argument("-s", "--silent", action="store_true", help="Do not show output.")
    arg_parser.add_argument("-d", "--debug", action="store_true", help="Debug mode.")
    arg_parser.add_argument("-l", "--list_outdated", action="store_true", help="Generates a list with all outdated agents.")
    arg_parser.add_argument("-c", "--chunk_size", type=int, help="Chunk size sending WPK file. Allowed values: [1 - 64000]. [Default: {0}]".format(
        common.wpk_chunk_size))
    arg_parser.add_argument("-t", "--timeout", type=int, help="Timeout until agent restart is unlocked.")
    arg_parser.add_argument("-f", "--file", type=str, help="Custom WPK filename.")
    arg_parser.add_argument("-x", "--execute", type=str, help="Executable filename in the WPK custom file. [Default: upgrade.sh]")
    arg_parser.add_argument("--http", action="store_true", help="Uses http protocol instead of https.")
    args = arg_parser.parse_args()

    try:
        main()
    except WazuhException as e:
        print("Error {0}: {1}".format(e.code, e.message))
        if args.debug:
            raise
    except Exception as e:
        print("Internal error: {0}".format(str(e)))
        if args.debug:
            raise
