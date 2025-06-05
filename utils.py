# Created by Yossy on 2025/02/23

import os 
import json
from datetime import datetime
from pathlib import Path
from PIL import Image
import csv
import pandas as pd
from collections import namedtuple
import numpy as np



RESOURCES = Path("resources")

class OBSItems(dict):

    # Load json file for OBS reference file path
    _data = json.load(open('obsfilepaths.json', 'r'))

    IMAGE_STAR_EMPTY = RESOURCES / "images" / "star_empty.png" 
    IMAGE_STAR_FILLED = RESOURCES / "images" / "star_filled_yellow.png"
    IMAGE_BLANK = RESOURCES / "images" / "blank.png"
    IMAGE_MAP_UNDEFINED = RESOURCES / "images" / "map_undefined.png"

    def __getitem__(self, key):
        "Override dict method"
        return self._data[key]
    
    def keys(self):
        "Override dict method"
        return self._data.keys()

    def values(self):
        "Override dict method"
        return self._data.values()
    
    def filter_by_type(self, _type):
        return {key:self[key] for key in self.keys() if self[key]["type"]==_type}
    
    def map_name_items(self):
        "Return map name objects"
        return [self[key] for key in ["Map1Name", "Map2Name", "Map3Name", "Map4Name", "Map5Name"]]
    
    def map_image_items(self):
        "Return map image objects"
        return [self[key] for key in ["Map1Image", "Map2Image", "Map3Image", "Map4Image", "Map5Image"]]
    
    def player1_star_items(self):
        "Return player1 star items"
        return [self[key] for key in ["Player1Star1", "Player1Star2", "Player1Star3"]]
    
    def player2_star_items(self):
        "Return player2 star items"
        return [self[key] for key in ["Player2Star1", "Player2Star2", "Player2Star3"]]

    def key_to_item(self, item_key):
        "Return item searched by item key"
        hits = [x for x in self.values() if x["key"] == item_key]
        if len(hits) == 1:
            return hits[0]
        elif len(hits) == 0:
            raise ValueError("Key {} doesn't exist in the OBS items.".format(item_key))
        else:
            raise ValueError("Multiple items found with the key {}: {}".format(item_key, hits))


class MatchInfoWriter:
    """
    This class updates Match Info by editing files linked to OBS objects. 
    """
    obsitems = OBSItems()

    # Number of game(s) a player should win to win a match. (1 for BO1, 2 for BO3, etc.)    
    games_to_win = 1 

    def set_games_to_win(self, number):
        "Set the number of games to take to win the match"
        self.games_to_win = number
        self.reset_score()

    
    def get_best_of(self):
        return "Best Of {}".format(self.games_to_win * 2 - 1)

    def reset_score(self):
        "Reset score by setting all star images empty"

        empty_star = Image.open(self.obsitems.IMAGE_STAR_EMPTY)
        blank = Image.open(self.obsitems.IMAGE_BLANK)
        player1_stars = [x['relative_path'] for x in self.obsitems.player1_star_items()]
        player2_stars = [x['relative_path'] for x in self.obsitems.player2_star_items()]

        # Initialize score by setting up empty stars
        for stars in [player1_stars, player2_stars]:
            for i, star in enumerate(stars):
                if i < self.games_to_win:
                    empty_star.save(star)
                else:
                    blank.save(star)

    def set_score(self, score_player1, score_player2):
        self.reset_score()
        filled_star = Image.open(self.obsitems.IMAGE_STAR_FILLED)
        if (score_player1 > self.games_to_win) or (score_player2 > self.games_to_win):
            raise ValueError("Invalid socer input: Score must be less than {}".format(self.games_to_win))
        for score1 in [x['relative_path'] for x in self.obsitems.player1_star_items()][:score_player1]:
            filled_star.save(score1)
        for score2 in [x['relative_path'] for x in self.obsitems.player2_star_items()][:score_player2]:
            filled_star.save(score2)
    
    def reset_maps(self):
        map_image_paths = [x['relative_path'] for x in self.obsitems.map_image_items()]
        map_name_paths = [x['relative_path'] for x in self.obsitems.map_name_items()]

        for i, map_image in enumerate(map_image_paths):
            map_undefined = Image.open(self.obsitems.IMAGE_MAP_UNDEFINED)
            map_undefined.save(map_image)
            # Update map name text
            with open(map_name_paths[i], encoding='utf-8') as txtfile:
                txtfile.write('---')
    
    def update_text(self, key, text):
        "Update text on the OBS scene by updating the text file linked to the OBS object"
        fpath = self.obsitems.key_to_item(key)['relative_path']
        with open(fpath, 'w', encoding='utf-8') as txtfile:
            txtfile.write(text)
        
    def update_image(self, key, image_path, size=None):
        "Update an image on the OBS scene by updating the linked image file"

        size = 1275, 713
        fpath = self.obsitems.key_to_item(key)['relative_path']
        new_image = Image.open(image_path)
        if size:
            new_image.thumbnail(size, Image.Resampling.LANCZOS)
        new_image.save(fpath)


class Entry:
    number : int
    checkin: bool
    name: str
    en_name: str
    region: str
    comment: str
    image_path: str

    def __init__(self, **params):
        self.number = None 
        self.checkin = True
        self.name = 'undefined'
        self.en_name = '' 
        self.region = '' 
        self.comment = 'undefined'
        self.image_path = 'undefined'
        self.update(**params)
        
    def update(self, **params):
        for key in params.keys():
            if key in self.__dict__:
                self.__setattr__(key, params[key])
            

    def get_label(self):
        label = '{}: {}'.format(self.number, self.name)
        if (self.name != self.en_name) and (self.en_name.strip() != ''):
            label += '/{}'.format(self.en_name)
        if self.region.strip() != '':
            label += ' @{}'.format(self.region)
        return label
    
    def __repr__(self):
        return 'Entry({})'.format(self.get_label())
    
    def __eq__(self, other):
        "override"
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False
    
    def __hash__(self):
        return hash(tuple(self.__dict__.values()))

class Match:
    entry1: Entry
    entry2: Entry
    score1: int
    score2: int
    timestamp: datetime

    def __init__(self, entry1: Entry, entry2: Entry, score1: int, score2: int, timestamp=None):
        if entry1 == entry2:
            raise ValueError('2 identical entries were given: {} & {}'.format(entry1, entry2))
        self.entry1 = entry1
        self.entry2 = entry2
        self.score1 = score1
        self.score2 = score2
        if timestamp is None:
            self.timestamp = datetime.now().replace(microsecond=0)
        else: 
            self.timestamp = timestamp
    
    def matchup(self):
        return {self.entry1, self.entry2}

def parse_entries(dirpath: str):

    dirpath = Path(dirpath)
    entryfile = dirpath / 'entries.csv'
    entries = []
    image_files = sorted(os.listdir(dirpath / 'AC'))
    image_numbers = [int(os.path.splitext(f)[0]) for f in image_files]

    with open(entryfile, encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)

        for row in reader:
            entry = Entry(number=int(row[0]),
                          checkin=(row[1].strip()=='1'),
                          name=row[2],
                          en_name=row[3],
                          region=row[4],
                          comment=row[5])
            # Find image
            try:
                idx = image_numbers.index(entry.number)
                entry.image_path = dirpath / 'AC' / image_files[idx]
            except ValueError:
                entry.image_path = 'not found'
            entries.append(entry)
    return entries


class MatchCoordinator:

    matches: list[Match]
    entries: list[Entry]
    matchups: list[set]
    max_wait: int
    max_matchup_count: int
    max_consecutive_match = 3

    def __init__(self, entries: list[Entry]):
        self.matches = []
        self.max_wait = 0
        self.max_matchup_count = 0
        self.update_entries(entries)
    
    def update_entries(self, entries: list[Entry]):
        self.entries = entries
        # Setup the matchups
        self.matchups = []
        for i, e1 in enumerate(entries):
            for j, e2 in enumerate(entries[i+1:]):
                self.matchups.append({e1, e2})
        self._update_max_values()

    def update_matches(self, matches: list[Match]):
        self.matches = matches
        self._update_max_values()
        
    def log_match(self, match: Match):
        "Log match info"
        self.matches.append(match)
        self._update_max_values()

    def _update_max_values(self):
        # Update max wait
        valid_wait_counts = [self.wait_count(e) for e in self.entries if self.wait_count(e) != np.inf]

        self.max_wait = max(valid_wait_counts) if len(valid_wait_counts)!=0 else 0
        # Update max matchup count
        matchup_counts = [self.matchup_count(m) for m in self.matchups]
        self.max_matchup_count = max(matchup_counts) if len(matchup_counts) != 0 else 0

    def suggest_matchup(self):
        "Suggest the next matchup based on previous matches"
        def _keyfunc(matchup):
            number_sum = sum([x.number for x in matchup])
            return (self.matchup_score(matchup), -number_sum)

        if len(self.matchups) != 0:
            return sorted(self.matchups, key=_keyfunc)[-1]
        else:
            return None
    
    def matchup_count(self, matchup):
        "Return # of matches of the given matchup"
        return len([m for m in self.matches if m.matchup() == matchup])
    
    def matchup_counts(self):
        "Retern # of matches per the matchup as a dict"
        return {mu: self.matchup_count(mu) for mu in self.matchups}
    
    def wait_count(self, entry: Entry):
        "Return # of matches the entry waited since last played"
        try:
            return [entry in m.matchup() for m in reversed(self.matches)].index(True)
        except ValueError:
            # The entry player has never played a match yet. 
            return np.inf
    
    def wait_score(self, entry, new_player_offset = 1):
        score = self.wait_count(entry)
        return score if score is not np.inf else self.max_wait + new_player_offset
    
    def consecutive_match_count(self, entry: Entry):
        try:
            return [entry in m.matchup() for m in reversed(self.matches)].index(False)
        except ValueError:
            return len(self.matches)
    
    def matchup_score(self, matchup):
        "Return the priority score for the matchup"
        total_wait_score = sum([self.wait_score(e) for e in matchup])
        matchup_count_score = (self.max_matchup_count - self.matchup_count(matchup))
        never_played = 2 if self.matchup_count(matchup) == 0 else 0
        previously_played = 0 
        for entry in list(matchup):
            if (len(self.matches) != 0) and (entry in self.matches[-1].matchup()):
                previously_played += 1
        if max([self.consecutive_match_count(x) for x in list(matchup)]) >= self.max_consecutive_match:
            return 0
        else:
            return total_wait_score + matchup_count_score + never_played - previously_played
    
    def generate_table(self):
        "Return matchup table as a DataFrame object"
        size = len(self.entries)
        table = np.empty((size, size), dtype=str)
        for i, e1 in enumerate(self.entries):
            for j, e2 in enumerate(self.entries):
                if i == j: 
                    table[i][j] = '--'
                else:
                    table[i][j] = '{} / {})'.format(self.matchup_count({e1, e2}),
                                                            self.matchup_score({e1, e2}))
        waits = np.array([[self.wait_count(x) if self.wait_count(x) is not np.inf else '--' for x in self.entries]]).T
        table = np.hstack([waits, table])

        entry_labels = ["{}: {}".format(x.number, x.name) for x in self.entries]
        df = pd.DataFrame(table,
                          columns=['Wait'] + entry_labels,
                          index=entry_labels
                          )
        return df
    
    def label_to_entry(self, label: str):
        "Return Entry instance from the player label in the platyer selection box"
        entry_num = int(label.split(':')[0])
        entry_nums = [x.number for x in self.entries]
        return self.entries[entry_nums.index(entry_num)]

    def write_match_logfile(self, match: Match, fpath: str):
        with open(fpath, 'a', encoding='utf-8') as logfile:
            logfile.write('{} vs. {}, {}-{}, {}\n'.format(match.entry1.get_label(), 
                                                          match.entry2.get_label(), 
                                                          match.score1,
                                                          match.score2,
                                                          match.timestamp))
    
    def load_match_logfile(self, fpath):
        "Load match info from the match logfile."
        def _line_to_match(line: str):
            label1, label2 = [x.strip() for x in line.split(',')[0].split('vs.')]
            entry1, entry2 = [self.label_to_entry(l) for l in [label1, label2]]
            score1, score2 = [int(x.strip()) for x in line.split(',')[1].split('-')] 
            timestamp = datetime.fromisoformat(line.split(',')[2].strip())
            return Match(entry1, entry2, score1, score2, timestamp)

        with open(fpath) as logfile:
            matches = [_line_to_match(line) for line in logfile]
            self.update_matches(matches)
            

Comment = namedtuple('Comment', ['user', 'comment'])

def parse_comments(txtfile):
    "Parse live comments and extract the entry info"
    comments = []
    with open(txtfile, encoding='utf-8') as f:
        i = 0
        while i < 1000:
            user = f.readline().strip()
            if user == '': break
            comment = f.readline().strip()
            comment = comment.lstrip('\u200b\u200b')
            comments.append(Comment(user, comment))
            emptyline = f.readline()
            i += 1
    return comments    

def comments_to_entries(comments, outfile):
    key_attr = {'-r': 'region', '-c': 'comment'}
    entries = []
    i = 1
    for c in comments:
        if c.comment.startswith('!join '):
            print(c)
            entry = Entry(number=i)
            i += 1
            sep = c.comment.split(' ')
            name = ''
            for word in sep[1:]:
                if word.startswith('-'): break
                name += ' ' + word
            entry.name = name.lstrip() 
            entry.en_name = name.lstrip()
            for j, arg in enumerate(sep[1:]):
                if arg in key_attr.keys():
                    value = ''
                    for word in sep[1:][j+1:]:
                        if word.startswith('-'): break
                        value += ' ' + word
                    setattr(entry, key_attr[arg], value.lstrip())
            entries.append(entry)
    
    with open(outfile, 'w', encoding='utf-8-sig', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Number', 'Name', 'EN Name', 'Region', 'Comment'])
        for entry in entries:
            writer.writerow([entry.number, entry.name, entry.name, entry.region, entry.comment])


if __name__ == "__main__":
    matchinfo = MatchInfoWriter()
    matchinfo.reset_score()
    matchinfo.set_games_to_win(2)
    matchinfo.set_score(0, 0)
    matchinfo.update_text("player1", "Yossy")
    matchinfo.update_text("player2", "Someone")
    matchinfo.update_text("match_info", "Test\n{}".format(matchinfo.get_best_of()))
