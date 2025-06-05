
import numpy as np
from utils import Entry, Match, MatchCoordinator, MatchInfoWriter


def test_MatchCoordinator():
    entries = [Entry(number=i+1, name=name) for i, name in enumerate(['Yossy', 'P1', 'P2', 'P3', 'P4'])]
    mc = MatchCoordinator(entries)
    assert len(mc.matchups) == 10
    assert mc.max_matchup_count == 0
    assert mc.max_wait == 0

    for entry in entries:
        assert mc.wait_count(entry) == np.inf 
        assert mc.wait_score(entry) == 1
        
    match1 = Match(entries[0], entries[2], 0, 0) 
    mc.log_match(match1)

    assert mc.max_matchup_count == 1
    assert mc.max_wait == 0 
    assert mc.matchup_count(match1.matchup()) == 1
    assert mc.matchup_count({entries[0], entries[2]}) == 1
    assert mc.wait_count(entries[0]) == 0
    assert mc.wait_count(entries[1]) == np.inf 
    assert mc.wait_score(entries[0]) == 0
    assert mc.wait_score(entries[1]) == 1

    #match2 = Match(entries[1], entries[2], 0, 0)
    #mc.log_match(match2)
    print(mc.generate_table())

    for i in range(20):
        run_next_match(mc)

    print("Update entries") 
    new_entry = Entry(number=6, name='P5')
    updated_entries = mc.entries[:-1] + [new_entry]
    print(updated_entries)
    mc.update_entries(updated_entries)

    for i in range(10):
        run_next_match(mc)




def run_next_match(mc):
    mu = list(mc.suggest_matchup())
    print("Next Matchup: {}".format(mu))

    next_match = Match(mu[0], mu[1], 0, 0)
    mc.log_match(next_match)
    print(mc.generate_table())
   

    