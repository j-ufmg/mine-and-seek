from __future__ import print_function
# -*- coding: utf-8 -

from builtins import range
import MalmoPython
import os
import random
import sys
import time
import json
import random
import re
import math
import uuid
from collections import namedtuple

EntityInfo = namedtuple('EntityInfo', 'x, y, z, name')

# Create one agent host for parsing:
agent_hosts = [MalmoPython.AgentHost()]

# Parse the command-line options:
agent_hosts[0].addOptionalFlag("debug,d", "Display debug information.")
agent_hosts[0].addOptionalIntArgument("agents,n", "Number of agents to use.", 1)

try:
    agent_hosts[0].parse(sys.argv)
except RuntimeError as e:
    print('ERROR:', e)
    print(agent_hosts[0].getUsage())
    exit(1)
if agent_hosts[0].receivedArgument("help"):
    print(agent_hosts[0].getUsage())
    exit(0)

DEBUG = agent_hosts[0].receivedArgument("debug")
NUM_AGENTS = agent_hosts[0].getIntArgument("agents")

# For a bit more fun, set MOB_TYPE = "Creeper"...
MOB_TYPE = "Villager"

agent_hosts += [MalmoPython.AgentHost() for x in range(1, NUM_AGENTS)]

# Set up debug output:
for ah in agent_hosts:
    ah.setDebugOutput(DEBUG) # Turn client-pool connection messages on/off.

if sys.version_info[0] == 2:
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0) # flush print output immediately
else:
    import functools
    print = functools.partial(print, flush = True)

def safeStartMission(agent_host, mission, client_pool, mission_record, role, expId):
    used_attempts = 0
    max_attempts = 5
    print("Calling startMission for role", role)
    while True:
        try:
            # Attempt start:
            agent_host.startMission(mission, client_pool, mission_record, role, expId)
            break
        except MalmoPython.MissionException as e:
            errorCode = e.details.errorCode
            if errorCode == MalmoPython.MissionErrorCode.MISSION_SERVER_WARMING_UP:
                print("Server not quite ready yet - waiting...")
                time.sleep(2)
            elif errorCode == MalmoPython.MissionErrorCode.MISSION_INSUFFICIENT_CLIENTS_AVAILABLE:
                print("Not enough available Minecraft instances running.")
                used_attempts += 1
                if used_attempts < max_attempts:
                    print("Will wait in case they are starting up.", max_attempts - used_attempts, "attempts left.")
                    time.sleep(2)
            elif errorCode == MalmoPython.MissionErrorCode.MISSION_SERVER_NOT_FOUND:
                print("Server not found - has the mission with role 0 been started yet?")
                used_attempts += 1
                if used_attempts < max_attempts:
                    print("Will wait and retry.", max_attempts - used_attempts, "attempts left.")
                    time.sleep(2)
            else:
                print("Other error:", e.message)
                print("Waiting will not help here - bailing immediately.")
                exit(1)
        if used_attempts == max_attempts:
            print("All chances used up - bailing now.")
            exit(1)
    print("startMission called okay.")

def safeWaitForStart(agent_hosts):
    print("Waiting for the mission to start", end=' ')
    start_flags = [False for a in agent_hosts]
    start_time = time.time()
    time_out = 120  # Allow a two minute timeout.
    while not all(start_flags) and time.time() - start_time < time_out:
        states = [a.peekWorldState() for a in agent_hosts]
        start_flags = [w.has_mission_begun for w in states]
        errors = [e for w in states for e in w.errors]
        if len(errors) > 0:
            print("Errors waiting for mission start:")
            for e in errors:
                print(e.text)
            print("Bailing now.")
            exit(1)
        time.sleep(0.1)
        print(".", end=' ')
    if time.time() - start_time >= time_out:
        print("Timed out while waiting for mission to start - bailing.")
        exit(1)
    print()
    print("Mission has started.")

def getXML():
    xml = '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
            <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            
              <About>
                <Summary>Simple chasing agent</Summary>
              </About>

              <ModSettings>
                <MsPerTick>50</MsPerTick>
              </ModSettings>
              
              <ServerSection>
                <ServerInitialConditions>
                  <Time>
                    <StartTime>12000</StartTime>
                    <AllowPassageOfTime>false</AllowPassageOfTime>
                  </Time>
                  <Weather>clear</Weather>
                </ServerInitialConditions>
                <ServerHandlers>
                  <FlatWorldGenerator destroyAfterUse="true" forceReset="true"/>
                  <DrawingDecorator>
                    <DrawCuboid x1="0" y1="4" z1="0" x2="30" y2="7" z2="40" type="brick_block"/>
                    <DrawCuboid x1="1" y1="4" z1="1" x2="29" y2="7" z2="39" type="air"/>

                    <!-- 1 -->
                    <DrawCuboid x1="10" y1="4" z1="10" x2="20" y2="6" z2="15" type="stone"/>
                    <DrawCuboid x1="13" y1="4" z1="13" x2="17" y2="6" z2="15" type="air"/>

                    <!-- 2 -->
                    <DrawCuboid x1="1" y1="4" z1="10" x2="5" y2="6" z2="15" type="stone"/>
                    <DrawLine x1="5" y1="4" z1="15" x2="1" y2="4" z2="19" type="stone"/>
                    <DrawLine x1="5" y1="5" z1="15" x2="1" y2="5" z2="19" type="stone"/>
                    <DrawLine x1="5" y1="6" z1="15" x2="1" y2="6" z2="19" type="stone"/>

                    <!-- 3 -->
                    <DrawCuboid x1="29" y1="4" z1="10" x2="25" y2="6" z2="15" type="stone"/>
                    <DrawLine x1="25" y1="4" z1="15" x2="29" y2="4" z2="19" type="stone"/>
                    <DrawLine x1="25" y1="5" z1="15" x2="29" y2="5" z2="19" type="stone"/>
                    <DrawLine x1="25" y1="6" z1="15" x2="29" y2="6" z2="19" type="stone"/>

                    <!-- 4 -->
                    <DrawCuboid x1="20" y1="4" z1="20" x2="18" y2="6" z2="35" type="stone"/>
                    <DrawLine x1="20" y1="4" z1="20" x2="25" y2="4" z2="25" type="stone"/>
                    <DrawLine x1="20" y1="5" z1="20" x2="25" y2="5" z2="25" type="stone"/>
                    <DrawLine x1="20" y1="6" z1="20" x2="25" y2="6" z2="25" type="stone"/>
                    <DrawLine x1="25" y1="4" z1="25" x2="20" y2="4" z2="25" type="stone"/>
                    <DrawLine x1="25" y1="5" z1="25" x2="20" y2="5" z2="25" type="stone"/>
                    <DrawLine x1="25" y1="6" z1="25" x2="20" y2="6" z2="25" type="stone"/>

                    <!-- 5 -->
                    <DrawCuboid x1="10" y1="4" z1="20" x2="13" y2="6" z2="30" type="stone"/>
                    <DrawLine x1="10" y1="4" z1="20" x2="5" y2="4" z2="25" type="stone"/>
                    <DrawLine x1="10" y1="5" z1="20" x2="5" y2="5" z2="25" type="stone"/>
                    <DrawLine x1="10" y1="6" z1="20" x2="5" y2="6" z2="25" type="stone"/>
                    <DrawLine x1="5" y1="4" z1="25" x2="10" y2="4" z2="25" type="stone"/>
                    <DrawLine x1="5" y1="5" z1="25" x2="10" y2="5" z2="25" type="stone"/>
                    <DrawLine x1="5" y1="6" z1="25" x2="10" y2="6" z2="25" type="stone"/>

                    <!-- 6 -->
                    <DrawCuboid x1="29" y1="4" z1="30" x2="25" y2="6" z2="35" type="stone"/>

                    <!-- 7 -->
                    <DrawCuboid x1="13" y1="4" z1="35" x2="13" y2="6" z2="40" type="stone"/>
                    <DrawCuboid x1="13" y1="4" z1="35" x2="5" y2="6" z2="35" type="stone"/>
                    <DrawCuboid x1="5" y1="4" z1="30" x2="1" y2="6" z2="30" type="stone"/>

                    <DrawBlock x="15" y="3" z="1" type="diamond_block"/>
                  </DrawingDecorator>
                  <!--ServerQuitFromTimeUp description="DIDNT_CATCH" timeLimitMs="30000"/-->
                  <ServerQuitWhenAnyAgentFinishes/>
                </ServerHandlers>
              </ServerSection>
              
              <AgentSection mode="Survival">
                <Name>Seeker</Name>
                <AgentStart>
                  <Placement x="15.5" y="5.0" z="1.5" yaw="0"/>
                </AgentStart>
                <AgentHandlers>
                  <ObservationFromFullStats/>
                  <ObservationFromNearbyEntities>
                    <Range name="entities" xrange="40" yrange="40" zrange="40"/>
                  </ObservationFromNearbyEntities>
                  <RewardForCollectingItem>
                    <Item type="diamond" reward="50"/>
                  </RewardForCollectingItem>
                  <AgentQuitFromCollectingItem>
                    <Item type="diamond" description="CATCH" />
                  </AgentQuitFromCollectingItem>
                  <ContinuousMovementCommands/>
                  <InventoryCommands/>
                </AgentHandlers>
              </AgentSection>

              <!--AgentSection mode="Survival">
                <Name>Runner</Name>
                <AgentStart>
                  <Placement x="0" y="5.0" z="10" yaw="0"/>
                    <Inventory>
                        <InventoryItem slot="0" type="diamond"/>
                    </Inventory>
                </AgentStart>
                <AgentHandlers>
                  <ObservationFromFullStats/>
                  <ObservationFromNearbyEntities>
                    <Range name="entities" xrange="40" yrange="40" zrange="40"/>
                  </ObservationFromNearbyEntities>
                  <RewardForDiscardingItem>
                    <Item type="diamond" reward="-50"/>
                  </RewardForDiscardingItem>
                  <ContinuousMovementCommands/>
                  <InventoryCommands/>
                </AgentHandlers>
              </AgentSection-->
            </Mission>'''

    return xml

# Set up a client pool
client_pool = MalmoPython.ClientPool()
for x in range(10000, 10000 + NUM_AGENTS):
    client_pool.add(MalmoPython.ClientInfo('127.0.0.1', x))

my_mission = MalmoPython.MissionSpec(getXML(), True)
my_mission_record = MalmoPython.MissionRecordSpec()

expID = str(uuid.uuid4())

for i in range(len(agent_hosts)):
    agent_hosts[i].setRewardsPolicy(MalmoPython.RewardsPolicy.KEEP_ALL_REWARDS)
    safeStartMission(agent_hosts[i], my_mission, client_pool, my_mission_record, i, expID)

safeWaitForStart(agent_hosts)

time.sleep(1)

def calcYawTo(entity_name, entities, x, y, z):
    ''' Find the mob we are following, and calculate the yaw we need in order to face it '''
    for ent in entities:
        if ent['name'] == entity_name:
            dx = ent['x'] - x
            dz = ent['z'] - z
            yaw = -180 * math.atan2(dx, dz) / math.pi
            return yaw
    return 0

def distance(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)

def runner(agent, obs, yaw, pos, life):
    agent.sendCommand("move 0.9")

    if "entities" in obs:
        for entity in obs['entities']:
            if entity['name'] == 'Seeker':
                xm, ym = entity['x'], entity['z']

        dist = distance(pos[0], pos[2], xm, ym)

        if dist < 3:
            agent.sendCommand("discardCurrentItem")

def seeker(agent, obs, yaw, pos, life):
    # Try to look somewhere interesting:
    if "entities" in obs:
        yaw_to_mob = calcYawTo('Runner', obs['entities'], *pos)

        for entity in obs['entities']:
            if entity['name'] == 'Runner':
                xm, ym = entity['x'], entity['z']

    pitch = obs.get(u'Pitch')

    if pitch < 0:
        agent.sendCommand("pitch 0") # stop looking up

    # Find shortest angular distance between the two yaws, preserving sign:
    deltaYaw = yaw_to_mob - yaw
    while deltaYaw < -180:
        deltaYaw += 360;
    while deltaYaw > 180:
        deltaYaw -= 360;
    deltaYaw /= 180.0;
    # And turn:
    agent.sendCommand("turn " + str(deltaYaw))

    dist = distance(pos[0], pos[2], xm, ym)

    if dist > 3:
        agent.sendCommand("move 1")
    else:
        agent.sendCommand("move 0")

running = True
current_obs = [{} for x in range(NUM_AGENTS)]
current_yaw = [0 for x in range(NUM_AGENTS)]
current_pos = [(0, 0, 0) for x in range(NUM_AGENTS)]
current_life = [20 for x in range(NUM_AGENTS)]
unresponsive_count = [10 for x in range(NUM_AGENTS)]
num_responsive_agents = lambda: sum([urc > 0 for urc in unresponsive_count])

timed_out = False

yaw_to_mob = 0

while num_responsive_agents() > 0 and not timed_out:
    for i in range(NUM_AGENTS):
        agent = agent_hosts[i]

        world_state = agent.getWorldState()

        if world_state.is_mission_running == False:
            timed_out = True
        elif world_state.number_of_observations_since_last_state > 0:
            unresponsive_count[i] = 10

            obvsText = world_state.observations[-1].text
            data = json.loads(obvsText)
            current_obs[i] = data

            current_yaw[i] = data.get(u'Yaw', current_yaw[i])
            current_life[i] = data.get(u'Life', current_life[i])

            if 'XPos' in data and 'YPos' in data and 'ZPos' in data:
                current_pos[i] = (data.get(u'XPos'), data.get(u'YPos'), data.get(u'ZPos'))

    #runner(agent_hosts[1], current_obs[1], current_yaw[1], current_pos[1], current_life[1])
    #seeker(agent_hosts[0], current_obs[0], current_yaw[0], current_pos[0], current_life[0])

# mission has ended.
print("Mission over")
reward = list(map(lambda r: r.getValue(), world_state.rewards))
print("Result: " + str(reward))
exit(0)
