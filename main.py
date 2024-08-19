import requests
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, StringVar, Toplevel
import threading
import time
import json
import os

# Constants
API_KEY = "ddbb90ca26c73e1f68bf7cf7e5c3ba43"
USER_DATA_FILE = "user_data.json"
LEAGUES = [
    {"key": "americanfootball_cfl", "title": "CFL"},
    {"key": "americanfootball_ncaaf", "title": "NCAAF"},
    {"key": "americanfootball_nfl", "title": "NFL"},
    {"key": "basketball_nba", "title": "NBA"},
    {"key": "baseball_mlb", "title": "MLB"},
    {"key": "icehockey_nhl", "title": "NHL"},
    {"key": "soccer_uefa_champs_league_qualification", "title": "UEFA Champions League"},
    {"key": "soccer_usa_mls", "title": "MLS"},
]
LEAGUES.insert(0, {"key": "all", "title": "All"})  # Add "All" option to the list of leagues

# Color scheme
PRIMARY_COLOR = "#ADD8E6"
SECONDARY_COLOR = "#ADD8E6"
BACKGROUND_COLOR = "#ADD8E6"
TEXT_COLOR = "#2F4F4F"
HIGHLIGHT_COLOR = "#ADD8E6"
FONT_SIZES = [12, 14, 16]
FONT = "Helvetica"


class SportsOddsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Live Sports Odds")
        self.root.geometry("800x600")
        self.root.config(bg=BACKGROUND_COLOR)

        self.logged_in_user = None
        self.user_data = self.load_user_data()
        self.sort_column = None
        self.sort_reverse = False
        self.sidebar_expanded = True
        self.current_api_url = ""
        self.current_font_size = 12

        # UI Elements
        self.header_label = None
        self.login_label = None
        self.team_listbox = None
        self.show_favorites_var = tk.BooleanVar()
        self.notify_var = tk.BooleanVar()
        self.league_var = StringVar(value="All")
        self.filter_var = StringVar()
        self.odds_tree = None
        self.loading_label = None
        self.progress_bar = None
        self.sidebar_frame = None
        self.expand_button = None

        self.create_styles()
        self.create_widgets()

        # Configure the grid for resizing
        self.root.grid_rowconfigure(2, weight=10)
        self.root.grid_columnconfigure(1, weight=10)

    # Utility Functions
    def load_user_data(self):
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, "r") as file:
                return json.load(file)
        return {}

    def save_user_data(self):
        with open(USER_DATA_FILE, "w") as file:
            json.dump(self.user_data, file, indent=4)

    def fetch_odds(self, api_url):
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Failed to fetch odds data: {e}")
            return None

    # UI Setup
    def create_styles(self):
        style = ttk.Style()
        style.configure("TLabel", font=(FONT, self.current_font_size), background=PRIMARY_COLOR, foreground=TEXT_COLOR)
        style.configure("TButton", font=(FONT, self.current_font_size), background=PRIMARY_COLOR, foreground=TEXT_COLOR)
        style.configure("Treeview.Heading", font=(FONT, self.current_font_size, "bold"), background=PRIMARY_COLOR, foreground=TEXT_COLOR)
        style.configure("Treeview", font=(FONT, self.current_font_size), rowheight=25, background=PRIMARY_COLOR, foreground=TEXT_COLOR)
        style.configure("Favorite.Treeview", background=HIGHLIGHT_COLOR)

    def create_widgets(self):
        self.create_header_frame()
        self.create_sidebar()
        self.create_odds_frame()
        self.create_text_size_toggle()
        self.create_save_settings_button()
        self.create_resize_grip()

    def create_header_frame(self):
        header_frame = ttk.Frame(self.root, padding="10", style="TFrame")
        header_frame.grid(row=0, column=0, columnspan=2, sticky=tk.EW, pady=(0, 0))  # Moved down

        # Header Labels
        self.header_label = ttk.Label(header_frame, text="Live Sports Odds", font=(FONT, 18, "bold"))
        self.header_label.grid(row=0, column=0, sticky=tk.NW)

        self.login_label = ttk.Label(header_frame, text="Not logged in", font=(FONT, self.current_font_size))
        self.login_label.grid(row=0, column=16, sticky=tk.E)

        self.login_label = ttk.Label(header_frame, text="Login", font=(FONT, self.current_font_size))
        self.login_label.grid(row=0, column=17, sticky=tk.E)


    def create_sidebar(self):
        self.sidebar_frame = ttk.LabelFrame(self.root, text="User Account Interface", padding="10")
        self.sidebar_frame.grid(row=2, column=0, sticky=tk.NSEW, pady=(10, 10))


        self.team_listbox = tk.Listbox(self.sidebar_frame, height=4, width=25, bg=BACKGROUND_COLOR, fg=TEXT_COLOR)
        self.team_listbox.grid(row=10, column=0, pady=5)
        ttk.Button(self.sidebar_frame, text="Add Favorite", command=self.add_favorite_team).grid(row=7, column=0, pady=5)
        ttk.Button(self.sidebar_frame, text="Remove Favorite", command=self.remove_favorite_team).grid(row=8, column=0, pady=5)
        ttk.Button(self.sidebar_frame, text="Show Analytics", command=self.show_analytics).grid(row=17, column=0, padx=10)

        self.expand_button = ttk.Button(self.sidebar_frame, text="Collapse account interface", command=self.toggle_sidebar)
        self.expand_button.grid(row=0, column=0, padx=10)

        # Header Controls
        ttk.Checkbutton(self.sidebar_frame, text="Show Only Favorites", variable=self.show_favorites_var, command=self.toggle_favorites_view).grid(row=16, column=0, padx=10)
        ttk.Checkbutton(self.sidebar_frame, text="Enable Notifications", variable=self.notify_var).grid(row=15, column=0, padx=0)


    def create_odds_frame(self):
        odds_frame = ttk.Frame(self.root, padding="10", style="TFrame")
        odds_frame.grid(row=2, column=1, sticky=tk.NSEW, pady=(10, 10))

        self.loading_label = ttk.Label(odds_frame, text="", font=(FONT, self.current_font_size), style="TLabel")
        self.loading_label.grid(row=0, column=1, columnspan=2)

        # Filter Section
        filter_frame = ttk.Frame(odds_frame, padding="10", style="TFrame")
        filter_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W)

        ttk.Button(filter_frame, text="Show Upcoming Games", command=self.show_upcoming_games).grid(row=0, column=0, pady=0)
        ttk.Button(filter_frame, text="Show Live Sports", command=self.show_live_sports).grid(row=1, column=0, pady=5)

        ttk.Label(filter_frame, text="Search:", font=(FONT, self.current_font_size)).grid(row=0, column=5, padx=0)
        ttk.Entry(filter_frame, textvariable=self.filter_var, width=20).grid(row=1, column=5, padx=0)
        ttk.Button(filter_frame, text="Filter", command=self.apply_filters).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(filter_frame, text="Select League:", font=(FONT, self.current_font_size)).grid(row=0, column=2, padx=5)
        league_dropdown = ttk.Combobox(filter_frame, textvariable=self.league_var, state="readonly", values=[league["title"] for league in LEAGUES], width=20)
        league_dropdown.grid(row=1, column=2, padx=5)

        self.progress_bar = ttk.Progressbar(filter_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=1, columnspan=1, pady=5)

        # Odds Display with Scrollbars
        odds_frame.grid_rowconfigure(3, weight=1)
        odds_frame.grid_columnconfigure(0, weight=1)

        odds_canvas = tk.Canvas(odds_frame, bg=PRIMARY_COLOR)
        odds_canvas.grid(row=3, column=0, sticky="nsew")

        # Vertical and Horizontal Scrollbars
        odds_scrollbar_y = ttk.Scrollbar(odds_frame, orient="vertical", command=odds_canvas.yview)
        odds_scrollbar_y.grid(row=3, column=1, sticky="ns")
        odds_scrollbar_x = ttk.Scrollbar(odds_frame, orient="horizontal", command=odds_canvas.xview)
        odds_scrollbar_x.grid(row=4, column=0, sticky="ew")

        odds_canvas.configure(yscrollcommand=odds_scrollbar_y.set, xscrollcommand=odds_scrollbar_x.set)

        # Create Frame inside Canvas to hold Treeview
        treeview_frame = ttk.Frame(odds_canvas)
        odds_canvas.create_window((0, 0), window=treeview_frame, anchor="nw")

        self.odds_tree = ttk.Treeview(treeview_frame, columns=("League", "Home Team", "Away Team", "Odds", "Sportsbook"), show='headings', height=10)
        self.odds_tree.grid(row=0, column=0, sticky="nsew")

        # Set column widths
        for col in ("League", "Home Team", "Away Team", "Odds", "Sportsbook"):
            self.odds_tree.heading(col, text=col, command=lambda _col=col: self.sort_treeview_column(_col))
            self.odds_tree.column(col, width=150, minwidth=100, stretch=True)

        treeview_frame.grid_rowconfigure(0, weight=1)
        treeview_frame.grid_columnconfigure(0, weight=1)

        self.odds_tree.bind("<Configure>", lambda e: odds_canvas.configure(scrollregion=odds_canvas.bbox("all")))
        self.odds_tree.tag_configure('favorite', background=HIGHLIGHT_COLOR)
        self.odds_tree.tag_configure('interesting', background=PRIMARY_COLOR, foreground=TEXT_COLOR)

        # Enable dragging and dropping of columns
        self.odds_tree.bind("<Button-1>", self.on_column_drag_start)

    def create_resize_grip(self):
        # Add a size grip to indicate the window is resizable
        size_grip = ttk.Sizegrip(self.root)
        size_grip.grid(row=3, column=1, sticky=tk.SE)

    def on_column_drag_start(self, event):
        """Initiate column dragging"""
        col = self.odds_tree.identify_column(event.x)
        self.start_column_drag(col)

    def start_column_drag(self, col):
        """Placeholder function for column dragging logic."""
        # Implement the logic for swapping columns here.
        pass

    def create_text_size_toggle(self):
        def toggle_font_size():
            self.current_font_size = FONT_SIZES[(FONT_SIZES.index(self.current_font_size) + 1) % len(FONT_SIZES)]
            self.create_styles()
            self.update_ui_fonts()

        toggle_button = ttk.Button(self.sidebar_frame, text="Toggle Text Size", command=toggle_font_size)
        toggle_button.grid(row=11, column=0, pady=(10, 10))  # Positioned under Show Analytics

    def create_save_settings_button(self):
        save_button = ttk.Button(self.sidebar_frame, text="Save Default Settings", command=self.save_default_settings)
        save_button.grid(row=12, column=0, pady=(10, 10))  # Positioned under Toggle Text Size

    def save_default_settings(self):
        """Save the default settings like column order, text size, etc."""
        settings = {
            "column_order": [self.odds_tree.heading(col, option="text") for col in self.odds_tree["columns"]],
            "font_size": self.current_font_size,
            # Add more settings as needed
        }
        with open("default_settings.json", "w") as file:
            json.dump(settings, file)
        messagebox.showinfo("Settings Saved", "Your default settings have been saved.")

    def update_ui_fonts(self):
        # This function dynamically updates the font sizes of all major widgets.
        self.create_styles()
        self.header_label.config(font=(FONT, 18, "bold"))
        self.login_label.config(font=(FONT, self.current_font_size))
        for widget in [self.header_label, self.login_label, self.team_listbox]:
            widget.update()

    # Event Handlers and Other Methods
    def login(self):
        username = simpledialog.askstring("Login", "Enter your username:")
        if username:
            if username not in self.user_data:
                create_account = messagebox.askyesno("Account not found", f"No account found for {username}. Would you like to create one?")
                if create_account:
                    self.user_data[username] = {"favorites": {"teams": [], "leagues": []}}
                    self.save_user_data()
            self.logged_in_user = username
            self.login_label.config(text=f"Logged in as: {self.logged_in_user}")
            self.update_favorites_display()

    def add_favorite_team(self):
        if self.logged_in_user:
            team = simpledialog.askstring("Add Favorite Team", "Enter the team name:")
            if team and team not in self.user_data[self.logged_in_user]["favorites"]["teams"]:
                self.user_data[self.logged_in_user]["favorites"]["teams"].append(team)
                self.save_user_data()
                self.update_favorites_display()
                messagebox.showinfo("Success", f"{team} added to favorites.")
            else:
                messagebox.showinfo("Info", "Team is already in favorites.")
        else:
            messagebox.showerror("Error", "You need to log in first.")

    def remove_favorite_team(self):
        if self.logged_in_user:
            selected_team = self.team_listbox.get(tk.ACTIVE)
            if selected_team:
                self.user_data[self.logged_in_user]["favorites"]["teams"].remove(selected_team)
                self.save_user_data()
                self.update_favorites_display()
                messagebox.showinfo("Success", f"{selected_team} removed from favorites.")

    def toggle_favorites_view(self):
        self.apply_filters()

    def toggle_sidebar(self):
        if self.sidebar_expanded:
            self.sidebar_frame.grid_remove()
            self.expand_button = ttk.Button(self.root, text="Show account interface", command=self.toggle_sidebar)
            self.expand_button.grid(row=2, column=0, pady=10)  # Add the expand button to the main grid
            self.root.grid_columnconfigure(1, weight=1)  # Expand odds table to fill the space
        else:
            self.sidebar_frame.grid()
            self.expand_button.grid_remove()  # Remove the expand button
            self.root.grid_columnconfigure(0, weight=1)  # Reset column expansion
        self.sidebar_expanded = not self.sidebar_expanded

    def notify_user(self, home_team, away_team):
        messagebox.showinfo("Game Notification", f"A new game featuring your favorite team(s): {home_team} vs {away_team}")

    def show_analytics(self):
        analytics_window = Toplevel(self.root)
        analytics_window.title("Analytics")
        analytics_window.geometry("300x200")

        league_counts = {}
        for child in self.odds_tree.get_children():
            league = self.odds_tree.item(child)["values"][0]
            league_counts[league] = league_counts.get(league, 0) + 1

        ttk.Label(analytics_window, text="Games per League", font=(FONT, 14, "bold")).pack(pady=10)

        for league, count in league_counts.items():
            ttk.Label(analytics_window, text=f"{league}: {count} games").pack(anchor="w", padx=20)

    def apply_filters(self):
        self.update_odds(self.current_api_url, filtered_league=self.league_var.get(), filtered_team=self.filter_var.get(), show_favorites_only=self.show_favorites_var.get())

    def show_upcoming_games(self):
        self.current_api_url = f"https://api.the-odds-api.com/v4/sports/upcoming/odds/?regions=us&markets=h2h&oddsFormat=american&apiKey={API_KEY}"
        self.start_fetch_data()

    def show_live_sports(self):
        self.current_api_url = f"https://api.the-odds-api.com/v4/sports/upcoming/odds/?regions=us&markets=h2h&oddsFormat=american&apiKey={API_KEY}"
        self.start_fetch_data()

    def update_favorites_display(self):
        if self.logged_in_user:
            self.team_listbox.delete(0, tk.END)
            for team in self.user_data[self.logged_in_user]["favorites"]["teams"]:
                self.team_listbox.insert(tk.END, team)

    def update_odds(self, api_url, filtered_league=None, filtered_team=None, show_favorites_only=False):
        odds_data = self.fetch_odds(api_url)
        if odds_data:
            self.odds_tree.delete(*self.odds_tree.get_children())  # Clear the tree view
            rows = []
            for game in odds_data:
                league = game.get('sport_title', 'N/A')
                home_team = game.get('home_team', 'N/A')
                away_team = game.get('away_team', 'N/A')
                bookmakers = game.get('bookmakers', [])

                # Apply filter: skip filtering by league if "All" is selected
                if (filtered_league and filtered_league != "All" and league != filtered_league) or (
                        filtered_team and filtered_team not in [home_team, away_team]):
                    continue

                is_favorite = (
                    self.logged_in_user and (
                        league in self.user_data[self.logged_in_user]["favorites"]["leagues"] or
                        any(team in self.user_data[self.logged_in_user]["favorites"]["teams"] for team in [home_team, away_team])
                    )
                )

                if show_favorites_only and not is_favorite:
                    continue

                if bookmakers:
                    sportsbook = bookmakers[0]['title']
                    odds = ", ".join([f"{outcome['name']} @ {outcome['price']}" for outcome in bookmakers[0]['markets'][0]['outcomes']])
                else:
                    sportsbook = "No bookmakers available"
                    odds = "N/A"

                tag = 'favorite' if is_favorite else ''
                rows.append((league, home_team, away_team, odds, sportsbook, tag))

                # Check for favorite team notifications
                if self.logged_in_user and is_favorite and self.notify_var.get():
                    self.notify_user(home_team, away_team)

            # Sort the rows before displaying
            if self.sort_column:
                if self.sort_column == "Home Team":
                    rows.sort(key=lambda x: (x[1], x[2]), reverse=self.sort_reverse)
                elif self.sort_column == "Away Team":
                    rows.sort(key=lambda x: (x[2], x[1]), reverse=self.sort_reverse)
                else:
                    rows.sort(key=lambda x: x[self.odds_tree["columns"].index(self.sort_column)], reverse=self.sort_reverse)

            for row in rows:
                self.odds_tree.insert('', 'end', values=row[:5], tags=(row[5],))

    def sort_treeview_column(self, col):
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
            self.sort_reverse = False
        self.apply_filters()

    def fetch_data_in_background(self):
        self.loading_label.config(text="Fetching live data...")
        self.progress_bar.start()
        time.sleep(1)  # Simulating delay for loading indicator
        self.apply_filters()
        self.loading_label.config(text="")
        self.progress_bar.stop()

    def start_fetch_data(self):
        threading.Thread(target=self.fetch_data_in_background, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = SportsOddsApp(root)
    root.mainloop()
