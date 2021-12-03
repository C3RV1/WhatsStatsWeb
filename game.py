import json
import os
import re
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

plt.close("all")


START_DATE = datetime(2021, 12, 1, 00, 00, 00)


class Win:
    def __init__(self, time_):
        self.time: datetime = time_

    def __repr__(self):
        print(f"<Win time={self.time}>")

    def get_as_json(self):
        return self.time.strftime("%d/%m/%y %H:%M")


class Player:
    def __init__(self, name: str, joined_time):
        self.name = name
        self.first_appearance = joined_time
        self.wins = []
        self.color = [0xFF, 0x9A, 0x5C]
        if os.path.isfile(f"config/{name}.json"):
            with open(f"config/{name}.json", "rb") as config_file:
                config_json = config_file.read()
                config = json.loads(config_json)
            self.color = config["color"]

    def add_win(self, win: Win):
        self.wins.append(win)

    def __repr__(self):
        return f"<Player name={self.name}>"

    @property
    def win_count(self):
        return len(self.wins)

    def wins_per_day(self, start_date=None, end_date=None):
        wins = self.get_wins(start_date=start_date, end_date=end_date)
        if len(wins) == 0:
            return 0
        if start_date is None:
            start_date: datetime = self.first_appearance
        if end_date is None:
            end_date: datetime = self.wins[-1].time
        days = (end_date - start_date).days + 1
        return len(wins) / days

    def display_stats(self, start_date=None, end_date=None):
        print(f"Stats for player \"{self.name}\"")
        print(f"Wins: {self.win_count}")
        print(f"Wins per day: {self.wins_per_day(start_date, end_date):.2f}")
        print("-------------------------------------")

    def get_common_hour(self, start_date=None, end_date=None):
        per_hour_dict = {i: 0 for i in range(24)}
        for win in self.get_wins(start_date=start_date, end_date=end_date):
            per_hour_dict[win.time.hour] += 1
        return per_hour_dict

    def save_common_hour(self):
        per_hour_dict = {i: 0 for i in range(24)}
        for win in self.wins:
            per_hour_dict[win.time.hour] += 1
        plt.figure()
        ts = pd.Series(per_hour_dict, index=[i for i in range(24)], name=self.name)
        ts.plot(kind="bar")
        plt.savefig(f"results/player-{self.name}.png")

    def get_wins(self, start_date=None, end_date=None):
        if start_date is None:
            start_date: datetime = self.first_appearance
        if end_date is None:
            end_date: datetime = self.wins[-1].time
        wins = [win if start_date <= win.time <= end_date else None for win in self.wins]
        return list(filter(lambda x: x is not None, wins))

    def get_as_json(self, start_date=None, end_date=None):
        return {"wins": [win.get_as_json() for win in self.get_wins(start_date=start_date, end_date=end_date)],
                "wins_per_day": self.wins_per_day(start_date=start_date, end_date=end_date),
                "color": self.color}


class Game:
    PATTERN = re.compile("^(.+) - ([^:]+): (.+)$")

    def __init__(self):
        self.players_by_name = {}
        self.name = ""

    def process_line(self, line):
        if re_match := self.PATTERN.search(line):
            time = datetime.strptime(re_match.group(1), "%d/%m/%y %H:%M")
            player = re_match.group(2)
            msg = re_match.group(3)

            if player not in self.players_by_name:
                player_obj = Player(player, time)
                self.players_by_name[player] = player_obj
            else:
                player_obj = self.players_by_name[player]

            win_count = msg.count('✅')
            for _ in range(win_count):
                player_obj.add_win(Win(time))

    def ranking(self):
        players = list(self.players_by_name.values())
        players.sort(key=lambda x: len(x.wins), reverse=True)
        return players

    @property
    def total_wins(self):
        return sum([player.win_count for player in self.players_by_name.values()])

    def construct_counts(self, start_date=None, end_date=None):
        counts = {}
        for player_name, player_obj in self.players_by_name.items():
            player_obj: Player
            counts[player_name] = {"count": len(player_obj.get_wins(start_date=start_date, end_date=end_date)),
                                   "color": player_obj.color,
                                   "wins-per-day": player_obj.wins_per_day(start_date=start_date, end_date=end_date)}
        return counts

    def get_player_hour(self, player_name, start_date=None, end_date=None):
        if player_name not in self.players_by_name:
            return {}
        player_obj: Player = self.players_by_name[player_name]
        return player_obj.get_common_hour(start_date=start_date, end_date=end_date)

    def get_as_json(self, start_date=None, end_date=None):
        game_dict = {}
        for player_name, player_obj in self.players_by_name.items():
            player_obj: Player
            game_dict[player_name] = player_obj.get_as_json(start_date=start_date, end_date=end_date)
        return game_dict


def main():
    g = Game()
    with open("data.txt", "rb") as data_file:
        for line in data_file.readlines():
            g.process_line(line.decode("utf-8"))

    print(f"Total wins: {g.total_wins}")
    for player in g.ranking():
        player.display_stats()
        player.save_common_hour()


if __name__ == "__main__":
    main()
