import teams
import random
from MarchMadnessPoolSim import spread_win_rates
import scipy.stats as stats


class GameSim:
    def __init__(self, team1, team2):
        self.score_stdev = 8
        self.team1 = team1
        self.team2 = team2
        self.game_rand = random.random()
        self.team1_score_rand = random.random()
        self.team2_score_rand = random.random()
        self.team1_off = self.team1.off_rating()
        self.team1_def = self.team1.def_rating()
        self.team1_tempo = self.team1.tempo_rating()
        self.team2_off = self.team2.off_rating()
        self.team2_def = self.team2.def_rating()
        self.team2_tempo = self.team2.tempo_rating()
        self.avg_tempo = self.team1.league_avg_tempo()
        self.avg_off = self.team1.league_avg_off()
        self.avg_def = self.team1.league_avg_def()
        self.team1_net = self.team1_off - self.team1_def
        self.team2_net = self.team2_off - self.team2_def

    def team1_spread(self):
        pace_adj_prediction = ((self.team1_tempo * self.team2_tempo) / self.avg_tempo) * (
                (self.team2_net - self.team1_net) / 100)
        return (pace_adj_prediction)

    def team1_win_prob(self):
        spread = self.team1_spread()
        win_prob = [value for key, value in spread_win_rates().items() if round(spread * 2) / 2 == float(key)][0]
        return (win_prob)

    def winning_team(self):
        team1_win_prob = self.team1_win_prob()
        if self.game_rand <= team1_win_prob:
            return (self.team1)
        if self.game_rand > team1_win_prob:
            return (self.team2)

    def losing_team(self):
        team1_win_prob = self.team1_win_prob()
        if self.game_rand <= team1_win_prob:
            return (self.team2)
        if self.game_rand > team1_win_prob:
            return (self.team1)

    def projected_pace(self):
        return ((self.team1_tempo * self.team2_tempo) / self.avg_tempo)

    def team1_projected_points(self):
        team1_off_ratio = (self.team1_off - self.avg_off) / self.avg_off
        team2_def_ratio = (self.team2_def - self.avg_def) / self.avg_def
        game_pace_ratio = (self.projected_pace() / 100)
        return ((team1_off_ratio + team2_def_ratio + 1) * self.avg_off * game_pace_ratio)

    def team2_projected_points(self):
        team2_off_ratio = (self.team2_off - self.avg_off) / self.avg_off
        team1_def_ratio = (self.team1_def - self.avg_def) / self.avg_def
        game_pace_ratio = (self.projected_pace() / 100)
        return ((team2_off_ratio + team1_def_ratio + 1) * self.avg_off * game_pace_ratio)

    def team1_points(self):
        return (stats.norm.ppf(self.team1_score_rand, self.team1_projected_points(), self.score_stdev))

    def team2_points(self):
        return (stats.norm.ppf(self.team2_score_rand, self.team2_projected_points(), self.score_stdev))

    def score_delta(self):
        return (abs(self.team1_points() - self.team2_points()))
