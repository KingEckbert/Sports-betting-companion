import requests
import tkinter as tk
from tkinter import ttk

# Hardcoded API Key
API_KEY = "ddbb90ca26c73e1f68bf7cf7e5c3ba43"

# Function to fetch live sports odds from the API
def fetch_odds():
    url = f"https://api.the-odds-api.com/v4/sports/upcoming/odds/?regions=us&markets=h2h&oddsFormat=american&apiKey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to update the odds displayed in the UI
def update_odds():
    odds_data = fetch_odds()
    if odds_data:
        # Clear the text box
        odds_text.delete(1.0, tk.END)

        for game in odds_data:
            league = game.get('sport_title', 'N/A')
            teams = f"{game.get('home_team', 'N/A')} vs {game.get('away_team', 'N/A')}"
            bookmakers = game.get('bookmakers', [])

            if bookmakers:
                odds = ", ".join([
                    f"{book['title']}: " +
                    ", ".join([f"{outcome['name']} @ {outcome['price']}" for outcome in book['markets'][0]['outcomes']])
                    for book in bookmakers
                ])
            else:
                odds = "No bookmakers available"

            odds_text.insert(tk.END, f"League: {league}\nTeams: {teams}\nOdds: {odds}\n\n")
    else:
        odds_text.delete(1.0, tk.END)
        odds_text.insert(tk.END, "Failed to fetch odds. Please check your connection or the API response.")

# Create the main window
root = tk.Tk()
root.title("Live Sports Odds")
root.geometry("600x400")

# Fetch Odds button
fetch_button = ttk.Button(root, text="Fetch Live Odds", command=update_odds)
fetch_button.pack(pady=10)

# Text box to display odds
odds_text = tk.Text(root, height=15, width=70)
odds_text.pack(pady=10)

# Start the GUI main loop
root.mainloop()
