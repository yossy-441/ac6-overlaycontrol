# Created by Yossy on 2025/03/21

import os
from pathlib import Path
import random
from datetime import datetime
import shutil
import streamlit as st
from utils import MatchInfoWriter, MatchCoordinator, Match
from utils import parse_entries, parse_comments, comments_to_entries

_g = globals()

ROUNDS = ['Round {}'.format(i) for i in range(1, 6)] + [
   "Semi-Final", "3rd Place Playoff", "Final", "Ground Final"
] 
BEST_OF = ['Best Of {}'.format(i) for i in [1, 3, 5]]

DEFAULT_SCORE = 0

TOURNAMENT_DIR = Path('.') / 'main'
UNDEFINED_MAP = Path('.') / 'resources' / 'allmaps' / 'Undefined.jpg'
UNDEFINED_AC = Path('.') / 'resources' / 'images' / 'ac_undefined.png'
MATCH_LOG_FILE = TOURNAMENT_DIR / 'matchlog.txt'


# Initialize MatchCoordinator instance
if 'match_coordinator' not in st.session_state:
    st.session_state.match_coordinator = MatchCoordinator([])

def load_entries():
    entries = [e for e in parse_entries(TOURNAMENT_DIR) if e.checkin]
    st.session_state.entries = entries
    st.session_state.entries_nums = [e.number for e in entries]
    st.session_state.match_coordinator.update_entries(entries)

def load_maps():
    "Load map pool"
    st.session_state.map_names = [os.path.splitext(m)[0] for m in os.listdir(TOURNAMENT_DIR / 'maps')]

# Load tournament entries
if 'entries' not in st.session_state:
    load_entries()

if 'map_names' not in st.session_state:
    load_maps()
    
if 'player1_score' not in st.session_state:
    st.session_state.player1_score = DEFAULT_SCORE

if 'player2_score' not in st.session_state:
    st.session_state.player2_score = DEFAULT_SCORE

def player_label_to_entry(label: str):
    "Return Entry instance from the player label in the platyer selection box"
    entry_num = int(label.split(':')[0])
    return st.session_state.entries[st.session_state.entries_nums.index(entry_num)]


st.title("AC6 Overlay Contol")

btn_col1, btn_col2 = st.columns([1, 1])

with btn_col1:
    # Reload Entry information
    if st.button('Reload Config'):
        # Reload entry information
        load_entries()

with btn_col2:
    if st.button('Suggest Match'):
        #TODO
        matchup = st.session_state.match_coordinator.suggest_matchup()
        if matchup != None:
            print('Suggested: {}'.format(matchup))
            entry1, entry2 = list(matchup)
            st.session_state.player1 = entry1.get_label()
            st.session_state.player2 = entry2.get_label()


player_options = [x.get_label() for x in st.session_state.entries]

player1_selection = st.selectbox('Player 1', player_options, key='player1')
p1name = player1_selection.split(':')[1].strip() if player1_selection else 'Undefined'
player1_name = st.text_input('Player 1 Name', p1name)

player2_selection = st.selectbox('Player 2', player_options, key='player2')
p2name = player2_selection.split(':')[1].strip() if player2_selection else 'Undefined'
player2_name = st.text_input('Player 2 Name', p2name)

round = st.selectbox('Round', ROUNDS)

best_of = st.selectbox("Best Of", BEST_OF)
game_num = int(best_of[-1])
games_to_win = int((int(best_of[-1]) + 1) / 2)

match_info = "{}\n{}".format(round, best_of)


col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button('Reset Score'):
        st.session_state.player1_score = DEFAULT_SCORE
        st.session_state.player2_score = DEFAULT_SCORE

with col2:
    placeholder1 = st.empty()
    player1_score = placeholder1.number_input(
        'Player 1 Score', min_value=0, max_value=games_to_win, step=1, key='player1_score')

with col3:
    placeholder2 = st.empty()
    player2_score = placeholder2.number_input(
        'Player 2 Score', min_value=0, max_value=games_to_win, step=1, key='player2_score')


# Random map selection from the map pool
if st.button('Random Selection'):
    if st.session_state.map_names is None or len(st.session_state.map_names) == 0:
        raise ValueError('Map Pool is empty.')
    else:
        map_pool = []
        while len(map_pool) < game_num:
            maps = st.session_state.map_names.copy()
            random.shuffle(maps)
            map_pool += maps
            
        for i in range(game_num):
            st.session_state['map{}'.format(i+1)] = map_pool[i]

# Show selected maps 
map_options = ['Undefined'] + st.session_state.map_names
for i in range(game_num):
    map_var = 'map{}'.format(i+1)
    _g[map_var] = st.selectbox('Map {}'.format(i+1), map_options, key=map_var) 

writer = MatchInfoWriter()

col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    if st.button('Update OBS View'):
        writer.update_text('player1_text', player1_name)
        writer.update_text('player2_text', player2_name)
        writer.update_text('match_info_text', match_info)

        writer.set_games_to_win(games_to_win)
        writer.set_score(player1_score, player2_score)
        entry_player1 = player_label_to_entry(player1_selection)
        entry_player2 = player_label_to_entry(player2_selection)

        # Update AC images & commnets of Card View
        for i, entry in enumerate([entry_player1, entry_player2]):
            if os.path.isfile(entry.image_path):
                ipath = entry.image_path
            else:
                ipath = UNDEFINED_AC
            writer.update_image('ac_player{}_image'.format(i+1), ipath, (1275, 713))
            writer.update_text('comment_player{}_text'.format(i+1), entry.comment)

        # Update map images    
        for i in range(5):
            map_var = 'map{}'.format(i+1)
            map_path = UNDEFINED_MAP
            map_name = 'Undefined'
            if i < game_num and _g[map_var] != 'Undefined':
                map_path = TOURNAMENT_DIR / 'maps' / (_g[map_var] +'.jpg')
                map_name = _g[map_var]
            writer.update_image(map_var + '_image', map_path)
            writer.update_text(map_var + '_text', map_name)

with col2:
    if st.button('Log Match'):
        entry1 = player_label_to_entry(player1_selection)
        entry2 = player_label_to_entry(player2_selection)
        match = Match(entry1, entry2, player1_score, player2_score)
        st.session_state.match_coordinator.log_match(match)

        # Add to log file
        st.session_state.match_coordinator.write_match_logfile(match, MATCH_LOG_FILE)

with col3:
    if st.button('Load Match Log'):
        st.session_state.match_coordinator.load_match_logfile(MATCH_LOG_FILE)

with col4:
    if st.button('Reset Match Log'):
        strdt = str(datetime.now().replace(microsecond=0)).replace(':', '-').replace(' ', '_')
        backup = os.path.splitext(MATCH_LOG_FILE)[0] + '_backup-{}.txt'.format(strdt)
        # backup the match log file
        shutil.move(MATCH_LOG_FILE, backup)
        # reset matches
        st.session_state.match_coordinator.update_matches([])
    
if st.button('Parse Live Comments File'):
    comments_file = TOURNAMENT_DIR / 'livecomments.txt'
    outfile = TOURNAMENT_DIR / 'signups.csv'
    comments = parse_comments(comments_file)
    comments_to_entries(comments, outfile)


maps = 'Map Pool:\n'
for m in st.session_state.map_names:
    maps += '- ' + m + '\n'
st.markdown(maps)


if st.toggle("Match Log Table"):
    st.table(st.session_state.match_coordinator.generate_table())