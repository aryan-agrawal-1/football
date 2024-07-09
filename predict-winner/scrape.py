import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Choosing the years that you want to scrape
years = list(range(2024, 2022, -1))

all_matches = []
# The URL of the standings of the premier league, this is so we can get the link for each teams page
standings_url = "https://fbref.com/en/comps/9/premier-league-stats"

for year in years:
    data = requests.get(standings_url)
    # Data.text is the HTML of the page
    soup = BeautifulSoup(data.text, features="lxml")
    # Find the class or id of the element you want to select, in this case the premier league table
    # This line selects all the table elements on the page with the stats_table class, we only want the first one
    standings_table = soup.select("table.stats_table")[0]
    # Now we need to find all the links in the table so we do this:
    links = standings_table.find_all('a')
    # This goes through each anchor element and finds the value of the href
    links = [l.get("href") for l in links]
    # This just filters to make sure we only get the squad links
    links = [l for l in links if '/squads/' in l]
    full_urls = [f"https://fbref.com{l}" for l in links]

    # Get url of previous season page
    prev_season = soup.select("a.prev")[0].get("href")
    standings_url = f"https://fbref.com{prev_season}"

    for team_url in full_urls:
        print(team_url)
        # We take the url, split it by / and then remove the -stats and replace - with a space to get the name
        team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")
        team_data = requests.get(team_url)
        # The match attribute will look for that string inside a table and read_html finds all the tables
        team_matches = pd.read_html(team_data.text, match="Scores & Fixtures")[0]

        # Now we find the shooting stats

        # First we find the link for the shooting page
        team_soup = BeautifulSoup(team_data.text, features="lxml")
        team_links = team_soup.find_all('a')
        team_links = [l.get("href") for l in team_links]
        # The shooting link appears 4 times on the page so we will have a list of 4 of the same link
        shooting_links = [l for l in team_links if l and 'all_comps/shooting/' in l]

        # Now we get the html of the shooting page
        shooting_data = requests.get(f"https://fbref.com{shooting_links[0]}")
        # Now we get our table
        shooting = pd.read_html(shooting_data.text, match="Shooting")[0]
        # This table has to heading rows, we dont need the first one so we can get rid of it
        shooting.columns = shooting.columns.droplevel()
        # Now we have a matches and shooting dataframe, we can just merge these together
        # We just do df1.merge(df2) and we can choose which rows we want, and what we want to merge by, in this case date
        # Any match that doesn't exist in both dfs just gets dropped
        # We put this in a try except in case the shooting stats for a team don't exist
        try:
            team_data = team_matches.merge(shooting[["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]], on="Date")
        except ValueError:
            continue
        # Now filter so we only get premier league matches
        team_data = team_data[team_data["Comp"] == "Premier League"]
        # Add season and team columns
        team_data["Season"] = year
        team_data["Team"] = team_name
        all_matches.append(team_data)
        time.sleep(10)
    time.sleep(60)

# put all the dataframes together
match_df = pd.concat(all_matches)
# Lowercase all column names for ease
match_df.columns = [c.lower() for c in match_df.columns]
# Write the dataframe to a csv
match_df.to_csv("matches.csv")

