import random
from collections import defaultdict
from agent import Agent  

class MyAgent(Agent):

    def __init__(self, name):
        #Intializes the agent
        super().__init__(name)
        self.name = name                            # Agent Name
        self.spy = False                            # Whether the agent is a spy
        self.player_number = None                   # Player Number
        self.num_players = None                     # Number of total players in the game
        self.spy_count = None                       # No: of spies
        self.suspicion = {}                         # A suspicion dictionary that will keep track of "how likely the player is a spy"
        self.mission_history = []                   # Will record mission details -- Can be useful in detecting spies
        self.vote_history = defaultdict(list)       # Will record voting details -- Can be useful in detecting spies
        self.proposal_history = defaultdict(list)   # Will record team proposals details - Can be useful in detecting spies
        self.spies = []                             # List of spies

    def new_game(self, number_of_players, player_number, spy_list):
        self.num_players = number_of_players
        self.player_number = player_number
        self.spy = player_number in spy_list

        if self.spy:                                   
            self.spy_count = len(spy_list)  
        else:
            self.spy_count = number_of_players // 3

        self.suspicion = {}                             # Initiating the suspicion list with 0.0 for both spies and resistance members
        for i in range(number_of_players):              # Suspicion list will help resistance members deciding who are spies
            self.suspicion[i] = 0.0                     # Suspicion list will help spies to keep track of their own suspicion levels and deciding whether to betray or not

        self.mission_history = []                       # Starting with clear empty lists 
        self.vote_history.clear()
        self.proposal_history.clear()

        if self.spy:                                    # Spies have a complete list of spies
            self.spies = spy_list                       # Resistance members have an empty list of spies
        else:
            self.spies = []

    def propose_mission(self, team_size, betrayals_required):
        team = [] 
        if self.spy:                                                     # If team leader is a spy
            team.append(self.player_number)                              # Adds itself to the team 
            remaining_spies = []
            for s in self.spies:
                if s != self.player_number:
                    remaining_spies.append(s)
        # Ensures that the the team has only enough spies to pass the mission
            sorted_spies = sorted(remaining_spies, key=lambda p: self.suspicion[p])     # Adds the spy with the lowest suspicion level to the team
            for spy in sorted_spies:
                if len(team) < betrayals_required:
                    team.append(spy)
            non_spies = []                                                                             # Adds resistance members to the team
            for p in range(self.num_players):                                                           # to keep the suspicion level low
                if p not in team and p not in self.spies:
                    non_spies.append(p)  
            sorted_non_spies = sorted(non_spies, key=lambda p: self.suspicion[p])                       
            for resistance in sorted_non_spies:
                if len(team) < team_size:
                    team.append(resistance)
        else:                                                                            # If team leader is a resistance member
            team = [self.player_number]                                                  # Adds itself to the team  
            sorted_players = sorted(self.suspicion.items(), key=lambda x: x[1])          # Adds the players with the lowest suspicion levels to the team
            for player, i in sorted_players:                                             # as they are more likely to be resistance members 
                if player != self.player_number and player not in team:
                    team.append(player)
                    if len(team) == team_size:
                        break
        return team

    def vote(self, mission, proposer, betrayals_required):                 
        if self.spy:                                                                        # If spy,
            spies_on_mission = 0                                                            # Count how many spies are on the proposed mission
            for player in mission:
                if player in self.spies:
                    spies_on_mission += 1            
            if spies_on_mission >= betrayals_required:                                      # If there are enough spies to sabotage the mission, vote
                return True
            return False
        else:                                                                               # If resistance member,
            team_suspicion = 0
            for p in mission:
                if p != self.player_number:
                    team_suspicion += self.suspicion[p]
            max_suspicion = 0.0                                                             # Calculate the average and maximum suspicion levels of the team                       
            for p in mission:
                if p != self.player_number:
                    if self.suspicion[p] > max_suspicion:
                        max_suspicion = self.suspicion[p]
            if len(mission) > 1:
                average_suspicion = team_suspicion / (len(mission) - 1) 
            else:
                average_suspicion = 0.0
            threshold = 0.4 + (0.1 * (len(self.mission_history) / 5))  
            if max_suspicion > 0.8:                                                          # Consider both average and maximum suspicion for voting
                return False
            return average_suspicion < threshold


    def betray(self, mission, proposer, betrayals_required):
        if self.spy and self.player_number in mission:      # Most likely, only spies on the mission are using this method but
            #Decide if the mission is critical to fail
            missions_failed = 0
            for m in self.mission_history:
                if not m['success']:
                    missions_failed += 1
            missions_remaining = 5 - len(self.mission_history)
            spies_need_failures = 3 - missions_failed
            mission_critical = spies_need_failures >= missions_remaining

            #Decide how suspicious you are
            suspicion_level = self.suspicion[self.player_number]
            risk_of_detection = suspicion_level + 0.2  # Potential increase in suspicion after betrayal

            # If they are not enough spies to fail the mission, no point betraying
            spies_on_mission = 0
            for player in mission:
                if player in self.spies:
                    spies_on_mission += 1
            if spies_on_mission < betrayals_required: 
                return  False
            else:
                # Betray if failing this mission is critical or you are considered safe
                if mission_critical or risk_of_detection < 0.7:
                    return True
                else:
                    return False     # Avoid betraying when risky or unneccessary 
        else: 
            return False

    def mission_outcome(self, mission, proposer, num_betrayals, mission_success):
        '''Updates suspicion levels based on mission outcomes and player behaviors.'''

        # Update mission record
        self.mission_history.append({
            'mission': mission,
            'proposer': proposer,
            'num_betrayals': num_betrayals,
            'success': mission_success
        })

        # Update suspicion levels based on mission outcome
        if not mission_success:
            betrayal_factor = num_betrayals / len(mission)
            for player in mission:
                if player != self.player_number:
                    increment = betrayal_factor * (1 + self.suspicion[player])
                    self.suspicion[player] += increment
            # Increase suspicion for the proposer
            if proposer != self.player_number:
                self.suspicion[proposer] += 0.3 * betrayal_factor
        else:
            # Decrease suspicion for mission members, but limit decrease
            for player in mission:
                if player != self.player_number:
                    decrement = 0.1 / len(mission)
                    self.suspicion[player] = max(0.0, self.suspicion[player] - decrement)

        # Suspicion based on voting patterns
        self.suspicion_from_votess()

        # Suspicion based on proposal patterns
        self.suspicion_from_proposals()

        for player in self.suspicion:
            self.suspicion[player] = min(max(self.suspicion[player], 0.0), 1.0)

    def suspicion_from_votess(self):
        '''Adjust suspicion based on voting history.'''
        last_mission = self.mission_history[-1]
        last_votes = {}
        for player, votes in self.vote_history.items():
            if votes:
                last_votes[player] = votes[-1]


    # If last mission failed, increase suspicion for approvers and decrease for rejectors
        if not last_mission['success']:
            for player, vote in last_votes.items():
                    if vote:
                        self.suspicion[player] += 0.1
                    else:
                        self.suspicion[player] -= 0.05
    # If last mission succeeded, decrease suspicion for approvers and increase for rejectors
        else:
            for player, vote in last_votes.items():
                    if not vote:
                        self.suspicion[player] += 0.05

    def suspicion_from_proposals(self):
        '''Adjust suspicion based on proposal history.'''
        for proposer, teams in self.proposal_history.items():
            total_suspicion = 0.0
            total_teams = len(teams)
            for team in teams:
                team_suspicion = 0
                for p in team:
                    if p != self.player_number:
                        team_suspicion += self.suspicion[p]
                if len(team) > 1:
                    average_team_suspicion = team_suspicion / (len(team) - 1) 
                else:
                    average_team_suspicion = 0.0
                total_suspicion += average_team_suspicion
                high_suspicion_players = []
                for p in team:
                    if self.suspicion[p] > 0.7 and p != self.player_number:
                        high_suspicion_players.append(p)
                if high_suspicion_players:
                    self.suspicion[proposer] += 0.05 * len(high_suspicion_players)
            if total_teams > 0:
                average_suspicion = total_suspicion / total_teams
            else:
                average_suspicion=  0.0
            if average_suspicion > 0.6:
                self.suspicion[proposer] += 0.05
            elif average_suspicion < 0.3:
                self.suspicion[proposer] -= 0.02

    def record_vote(self, player, vote):
        '''Record voting history for each player.'''
        self.vote_history[player].append(vote)

    def record_proposal(self, proposer, team):
        '''Record proposal history for each proposer.'''
        self.proposal_history[proposer].append(team)
