import requests
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, StringVar, Toplevel, Checkbutton, BooleanVar
import threading
import time
import json
import os
from datetime import datetime
import pytz

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
SECONDARY_COLOR = "#fcfafe"
BACKGROUND_COLOR = "#ADD8E6"
TEXT_COLOR = "#2F4F4F"
HIGHLIGHT_COLOR = "#ADD8E6"
FONT_SIZES = [12, 14, 16]
FONT = "Helvetica"

# Initial Wallet Amount
INITIAL_WALLET_AMOUNT = 10000

# Timezones list
TIMEZONES = pytz.all_timezones


class SportsOddsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Live Sports Odds")
        self.root.geometry("800x600")
        self.root.config(bg=PRIMARY_COLOR)

        self.logged_in_user = None
        self.user_data = self.load_user_data()
        self.sort_column = None
        self.sort_reverse = False
        self.sidebar_expanded = True
        self.current_api_url = ""
        self.current_font_size = 12
        self.placed_bets = []  # List to track placed bets
        self.odds_data = []  # Store odds data fetched from the API

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
        self.wallet_label = None  # Label to display the wallet balance

        self.create_styles()
        self.create_widgets()

        # Configure the grid for resizing
        self.root.grid_rowconfigure(2, weight=100)
        self.root.grid_columnconfigure(1, weight=100)

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

    def convert_to_local_time(self, utc_time_str, timezone_str):
        try:
            # Correct datetime format to include year, month, day, time, and Z for UTC
            utc_time = datetime.strptime(utc_time_str, "%M:%SZ")
            utc_time = pytz.utc.localize(utc_time)
            user_timezone = pytz.timezone(timezone_str)
            local_time = utc_time.astimezone(user_timezone)
            # Format without the year, showing only month, day, and time
            return local_time.strftime("%M:%S %Z")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to convert time: {str(e)}")
            return utc_time_str  # Return UTC time if conversion fails

    # UI Setup
    def create_styles(self):
        style = ttk.Style()
        style.configure("TLabel", font=(FONT, self.current_font_size), background=PRIMARY_COLOR, foreground=TEXT_COLOR)
        style.configure("TButton", font=(FONT, self.current_font_size), background=PRIMARY_COLOR, foreground=TEXT_COLOR)

        # Add this line to set the background color for the header frame
        style.configure("Header.TFrame", background=PRIMARY_COLOR)

        style.configure("Treeview.Heading", font=(FONT, self.current_font_size, "bold"), background=PRIMARY_COLOR,
                        foreground=TEXT_COLOR)
        style.configure("Treeview", font=(FONT, self.current_font_size), rowheight=25, background=PRIMARY_COLOR,
                        foreground=TEXT_COLOR)
        style.configure("Favorite.Treeview", background=HIGHLIGHT_COLOR)

    def create_widgets(self):
        self.create_header_frame()
        self.create_sidebar()
        self.create_odds_frame()
        self.create_text_size_toggle()
        self.create_save_settings_button()
        self.create_resize_grip()

    def create_header_frame(self):
        # Set the same background color to the header frame
        header_frame = ttk.Frame(self.root, padding="10", style="TFrame")
        header_frame.grid(row=0, column=0, columnspan=2, sticky=tk.EW, pady=(0, 0))

        # Ensure the frame has the desired background color
        header_frame.config(style="Header.TFrame")

        # Configure columns to allow proper positioning of widgets
        header_frame.grid_columnconfigure(0, weight=1)  # Left side column for expanding
        header_frame.grid_columnconfigure(1, weight=0)  # Column for the login button

        # Header Labels
        self.header_label = ttk.Label(header_frame, text="Live Sports Odds", font=(FONT, 18, "bold"),
                                      background=SECONDARY_COLOR)
        self.header_label.grid(row=0, column=0, sticky=tk.W)  # Align to the left

        # Move login button to the right above the search bar
        self.login_button = ttk.Button(header_frame, text="Login", command=self.toggle_login, style="TButton")
        self.login_button.grid(row=0, column=1, sticky=tk.E, padx=(0, 10))  # Align to the right with padding

    def toggle_login(self):
        if self.logged_in_user:
            # Perform logout action
            self.logged_in_user = None
            self.login_button.config(text="Login")
            self.wallet_label.config(text="Wallet: $0")  # Reset wallet label
            messagebox.showinfo("Logged Out", "You have been logged out.")
        else:
            # Perform login action
            self.login()

    def login(self):
        username = simpledialog.askstring("Login", "Enter your username:")
        if username:
            if username in self.user_data:
                self.logged_in_user = username
                self.login_button.config(text="Logout")

                # Ensure the user data has the 'bets', 'wins', 'losses', 'wallet', and 'timezone' keys
                if "bets" not in self.user_data[username]:
                    self.user_data[username]["bets"] = []
                if "wins" not in self.user_data[username]:
                    self.user_data[username]["wins"] = 0
                if "losses" not in self.user_data[username]:
                    self.user_data[username]["losses"] = 0
                if "wallet" not in self.user_data[username]:
                    self.user_data[username]["wallet"] = INITIAL_WALLET_AMOUNT
                if "timezone" not in self.user_data[username]:
                    self.user_data[username]["timezone"] = "UTC"  # Default to UTC if timezone is not set

                self.save_user_data()

                # Update wallet label
                self.update_wallet_display()
                messagebox.showinfo("Login Successful", f"Logged in as: {self.logged_in_user}")
                self.update_favorites_display()
            else:
                messagebox.showerror("Login Failed", "Username not found. Please create an account.")

    def create_account(self):
        username = simpledialog.askstring("Create Account", "Enter a new username:")
        if username:
            if username in self.user_data:
                messagebox.showerror("Account Creation Failed", "Username already exists.")
            else:
                # Prompt the user to select their timezone
                timezone = self.select_timezone()

                # Initialize user data with bets, wins, losses, wallet, and timezone
                self.user_data[username] = {
                    "favorites": {"teams": [], "leagues": []},
                    "bets": [],
                    "wins": 0,
                    "losses": 0,
                    "wallet": INITIAL_WALLET_AMOUNT,
                    "timezone": timezone
                }
                self.save_user_data()
                messagebox.showinfo("Account Created", f"Account created for {username}. Logging in now.")

                # Log the user in immediately after account creation
                self.logged_in_user = username
                self.login_button.config(text="Logout")
                self.update_wallet_display()
                self.update_favorites_display()
                messagebox.showinfo("Login Successful", f"Logged in as: {self.logged_in_user}")

    def select_timezone(self):
        timezone_window = Toplevel(self.root)
        timezone_window.title("Select Timezone")
        timezone_window.geometry("300x400")

        timezone_var = StringVar()
        timezone_listbox = tk.Listbox(timezone_window, listvariable=timezone_var, height=15, width=50)
        timezone_listbox.pack(pady=10)

        for tz in TIMEZONES:
            timezone_listbox.insert(tk.END, tz)

        selected_timezone = None

        def confirm_timezone():
            nonlocal selected_timezone
            selected_index = timezone_listbox.curselection()
            if selected_index:
                selected_timezone = timezone_listbox.get(selected_index)
                timezone_window.destroy()
            else:
                messagebox.showerror("Error", "Please select a timezone.")

        ttk.Button(timezone_window, text="Confirm", command=confirm_timezone).pack(pady=10)
        self.root.wait_window(timezone_window)

        # Return the selected timezone or default to UTC if no selection was made
        return selected_timezone or "UTC"


    def create_sidebar(self):
        self.sidebar_frame = ttk.LabelFrame(self.root, text="User Account Interface", padding="10")
        self.sidebar_frame.grid(row=2, column=0, sticky=tk.NSEW, pady=(10, 10))

        # Add Login and Create Account Buttons
        self.login_button = ttk.Button(self.sidebar_frame, text="Login", command=self.toggle_login, style="TButton")
        self.login_button.grid(row=1, column=0, padx=10, pady=5)

        self.create_account_button = ttk.Button(self.sidebar_frame, text="Create Account", command=self.create_account,
                                                style="TButton")
        self.create_account_button.grid(row=2, column=0, padx=10, pady=5)

        self.place_bet_button = ttk.Button(self.sidebar_frame, text="Place Bet", command=self.place_bet_window,
                                           style="TButton")
        self.place_bet_button.grid(row=3, column=0, padx=10, pady=5)

        # New "View Bets" button
        self.view_bets_button = ttk.Button(self.sidebar_frame, text="View Bets", command=self.open_bets_window,
                                           style="TButton")
        self.view_bets_button.grid(row=4, column=0, padx=10, pady=10)

        self.expand_button = ttk.Button(self.sidebar_frame, text="Collapse account interface",
                                        command=self.toggle_sidebar)
        self.expand_button.grid(row=0, column=0, padx=10)

        # Shift all components down by one row
        self.team_listbox = tk.Listbox(self.sidebar_frame, height=4, width=25, bg=PRIMARY_COLOR, fg=TEXT_COLOR)
        self.team_listbox.grid(row=11, column=0, pady=5)
        ttk.Button(self.sidebar_frame, text="Add Favorite", command=self.add_favorite_team).grid(row=8, column=0,
                                                                                                 pady=5)
        ttk.Button(self.sidebar_frame, text="Remove Favorite", command=self.remove_favorite_team).grid(row=9, column=0,
                                                                                                       pady=5)
        ttk.Button(self.sidebar_frame, text="Show Analytics", command=self.show_analytics).grid(row=18, column=0,
                                                                                                padx=10)

        # Header Controls
        ttk.Checkbutton(self.sidebar_frame, text="Show Only Favorites", variable=self.show_favorites_var,
                        command=self.toggle_favorites_view).grid(row=19, column=0, padx=10)
        ttk.Checkbutton(self.sidebar_frame, text="Enable Notifications", variable=self.notify_var).grid(row=18,
                                                                                                        column=0,
                                                                                                        padx=0)

        # Wallet Display
        self.wallet_label = ttk.Label(self.sidebar_frame, text="Wallet: $0", font=(FONT, self.current_font_size))
        self.wallet_label.grid(row=20, column=0, pady=5)

    def update_wallet_display(self):
        """Update the wallet display for the logged-in user."""
        if self.logged_in_user:
            wallet_amount = self.user_data[self.logged_in_user].get("wallet", 0)
            self.wallet_label.config(text=f"Wallet: ${wallet_amount}")

    def create_odds_frame(self):
        odds_frame = ttk.Frame(self.root, padding="10", style="TFrame")
        odds_frame.grid(row=2, column=1, sticky=tk.NSEW, pady=(10, 10))

        self.loading_label = ttk.Label(odds_frame, text="", font=(FONT, self.current_font_size), style="TLabel")
        self.loading_label.grid(row=0, column=1, columnspan=2)

        # Filter Section
        filter_frame = ttk.Frame(odds_frame, padding="10", style="TFrame")
        filter_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W)

        ttk.Button(filter_frame, text="Show Upcoming Games", command=self.show_upcoming_games).grid(row=0, column=0,
                                                                                                    pady=0)
        ttk.Button(filter_frame, text="Show Live Sports", command=self.show_live_sports).grid(row=1, column=0, pady=5)

        ttk.Label(filter_frame, text="Search:", font=(FONT, self.current_font_size)).grid(row=0, column=5, padx=0)
        ttk.Entry(filter_frame, textvariable=self.filter_var, width=20).grid(row=1, column=5, padx=0)
        ttk.Button(filter_frame, text="Filter", command=self.apply_filters).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(filter_frame, text="Select League:", font=(FONT, self.current_font_size)).grid(row=0, column=2,
                                                                                                 padx=5)
        league_dropdown = ttk.Combobox(filter_frame, textvariable=self.league_var, state="readonly",
                                       values=[league["title"] for league in LEAGUES], width=20)
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

        self.odds_tree = ttk.Treeview(treeview_frame,
                                      columns=("Odds", "Home Team", "Away Team", "League", "Sportsbook", "Commence Time"),
                                      show='headings', height=10)
        self.odds_tree.grid(row=0, column=0, sticky="nsew")

        # Set column widths
        for col in ("Odds", "Home Team", "Away Team", "League", "Sportsbook", "Commence Time"):
            self.odds_tree.heading(col, text=col, command=lambda _col=col: self.sort_treeview_column(_col))
            self.odds_tree.column(col, width=150, minwidth=100, stretch=True)

        treeview_frame.grid_rowconfigure(0, weight=1)
        treeview_frame.grid_columnconfigure(0, weight=1)

        self.odds_tree.bind("<Configure>", lambda e: odds_canvas.configure(scrollregion=odds_canvas.bbox("all")))
        self.odds_tree.tag_configure('favorite', background=SECONDARY_COLOR)
        self.odds_tree.tag_configure('interesting', background=PRIMARY_COLOR, foreground=TEXT_COLOR)

    def create_resize_grip(self):
        # Add a size grip to indicate the window is resizable
        size_grip = ttk.Sizegrip(self.root)
        size_grip.grid(row=3, column=1, sticky=tk.SE)

    def create_text_size_toggle(self):
        def toggle_font_size():
            self.current_font_size = FONT_SIZES[(FONT_SIZES.index(self.current_font_size) + 1) % len(FONT_SIZES)]
            self.create_styles()
            self.update_ui_fonts()

        toggle_button = ttk.Button(self.sidebar_frame, text="Toggle Text Size", command=toggle_font_size)
        toggle_button.grid(row=16, column=0, pady=(10, 10))  # Positioned under Show Analytics

    def create_save_settings_button(self):
        save_button = ttk.Button(self.sidebar_frame, text="Save Default Settings", command=self.save_default_settings)
        save_button.grid(row=15, column=0, pady=(10, 10))  # Positioned under Toggle Text Size

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

    # Place Bet Functionality with Wallet Management
    def place_bet_window(self):
        if not self.logged_in_user:
            messagebox.showerror("Error", "You need to log in to place a bet.")
            return

        # Ensure a game is selected
        selected_item = self.odds_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a game to place a bet.")
            return

        selected_game = self.odds_tree.item(selected_item, "values")
        game_description = f"{selected_game[1]} vs {selected_game[2]} ({selected_game[3]})"

        # Find the corresponding game data
        selected_game_data = None
        for game in self.odds_data:  # Ensure odds_data is filled when fetching odds
            if game["home_team"] == selected_game[1] and game["away_team"] == selected_game[2]:
                selected_game_data = game
                break

        if not selected_game_data:
            messagebox.showerror("Error", "Failed to find the selected game data.")
            return

        # Prompt the user to select multiple outcomes with checkboxes
        outcomes = []
        for bookmaker in selected_game_data["bookmakers"]:
            for outcome in bookmaker["markets"][0]["outcomes"]:
                outcomes.append((outcome['name'], bookmaker['title'], outcome['price']))

        bet_window = Toplevel(self.root)
        bet_window.title("Choose your bet")
        bet_window.geometry("300x400")

        checkboxes = []
        bet_vars = []

        for outcome, bookmaker, price in outcomes:
            bet_var = BooleanVar()
            bet_check = Checkbutton(bet_window, text=f"{outcome} ({bookmaker}) @ {price}", variable=bet_var)
            bet_check.pack(anchor="w")
            checkboxes.append(bet_check)
            bet_vars.append((bet_var, outcome, bookmaker, price))

        def confirm_bet():
            selected_bets = [(var, outcome, bookmaker, price) for var, outcome, bookmaker, price in bet_vars if var.get()]
            if not selected_bets:
                messagebox.showerror("Error", "Please select at least one bet.")
                return

            bet_amount = simpledialog.askfloat("Bet Amount", "Enter your bet amount:")
            if bet_amount is None or bet_amount <= 0:
                messagebox.showerror("Error", "Please enter a valid bet amount.")
                return

            # Check if the user has enough money in their wallet
            current_wallet = self.user_data[self.logged_in_user].get("wallet", 0)
            if bet_amount > current_wallet:
                messagebox.showerror("Error", "You don't have enough money in your wallet to place this bet.")
                return

            # Deduct bet amount from the user's wallet
            self.user_data[self.logged_in_user]["wallet"] -= bet_amount
            self.update_wallet_display()

            # Place the bets
            for var, outcome, bookmaker, price in selected_bets:
                bet = {
                    "game": game_description,
                    "outcome": f"{outcome} ({bookmaker})",
                    "amount": bet_amount / len(selected_bets),  # Divide the bet amount equally among selected bets
                    "price": price,
                    "result": None  # Placeholder for the result (win/loss)
                }
                self.user_data[self.logged_in_user]["bets"].append(bet)

            self.save_user_data()
            self.track_bets()
            bet_window.destroy()
            messagebox.showinfo("Bet Placed", "Your bet has been placed successfully.")

        ttk.Button(bet_window, text="OK", command=confirm_bet).pack(pady=10)
        ttk.Button(bet_window, text="Cancel", command=bet_window.destroy).pack()

    def open_bets_window(self):
        if not self.logged_in_user:
            messagebox.showerror("Error", "You need to log in to view bets.")
            return

        # Create or update the "Placed Bets" window
        if not hasattr(self, 'bets_window') or not self.bets_window.winfo_exists():
            self.bets_window = Toplevel(self.root)
            self.bets_window.title("Placed Bets")
            self.bets_window.geometry("500x400")

            self.bets_listbox = tk.Listbox(self.bets_window, height=15, width=60)
            self.bets_listbox.pack(pady=10)

            self.delete_bet_button = ttk.Button(self.bets_window, text="Delete Bet", command=self.delete_bet)
            self.delete_bet_button.pack(side=tk.LEFT, padx=5, pady=5)

            # Add View Statistics Button
            self.stats_button = ttk.Button(self.bets_window, text="View Statistics", command=self.view_statistics)
            self.stats_button.pack(side=tk.RIGHT, padx=5, pady=5)

            # Handle window close event
            self.bets_window.protocol("WM_DELETE_WINDOW", self.on_bets_window_close)

        self.update_bets_display()

    def view_statistics(self):
        if not self.logged_in_user:
            messagebox.showerror("Error", "You need to log in to view statistics.")
            return

        stats_window = Toplevel(self.root)
        stats_window.title("Betting Statistics")
        stats_window.geometry("400x400")

        user_bets = self.user_data[self.logged_in_user]["bets"]
        total_bets = len(user_bets)
        total_wins = self.user_data[self.logged_in_user].get("wins", 0)
        total_losses = self.user_data[self.logged_in_user].get("losses", 0)
        total_amount_bet = sum(bet["amount"] for bet in user_bets)
        total_earnings = sum(bet["amount"] * float(bet["price"]) for bet in user_bets if bet["result"] == "Win")
        net_profit_loss = total_earnings - total_amount_bet
        win_percentage = (total_wins / total_bets) * 100 if total_bets > 0 else 0
        biggest_win = max((bet["amount"] * float(bet["price"]) for bet in user_bets if bet["result"] == "Win"), default=0)
        biggest_loss = max((bet["amount"] for bet in user_bets if bet["result"] == "Loss"), default=0)

        ttk.Label(stats_window, text="Betting Statistics", font=(FONT, 16, "bold")).pack(pady=10)

        stats_text = (
            f"Total Bets Placed: {total_bets}\n"
            f"Total Wins: {total_wins}\n"
            f"Total Losses: {total_losses}\n"
            f"Win Percentage: {win_percentage:.2f}%\n"
            f"Total Amount Bet: ${total_amount_bet:.2f}\n"
            f"Total Earnings: ${total_earnings:.2f}\n"
            f"Net Profit/Loss: ${net_profit_loss:.2f}\n"
            f"Biggest Win: ${biggest_win:.2f}\n"
            f"Biggest Loss: ${biggest_loss:.2f}"
        )

        ttk.Label(stats_window, text=stats_text, font=(FONT, 12)).pack(pady=10)

    def on_bets_window_close(self):
        # Clean up references to the bets window and listbox when the window is closed
        self.bets_window.destroy()
        self.bets_window = None
        self.bets_listbox = None

    def update_bets_display(self):
        # Ensure the bets_listbox exists before trying to update it
        if self.bets_listbox and self.bets_listbox.winfo_exists():
            self.bets_listbox.delete(0, tk.END)
            for bet in self.user_data[self.logged_in_user]["bets"]:
                bet_info = f"{bet['game']} - {bet['outcome']} - ${bet['amount']} - {bet['result'] or 'Pending'}"
                self.bets_listbox.insert(tk.END, bet_info)

    def track_bets(self):
        # If the bets window is open and the listbox exists, update it
        if hasattr(self, 'bets_window') and self.bets_window and self.bets_window.winfo_exists():
            self.update_bets_display()

    def delete_bet(self):
        selected_bet_index = self.bets_listbox.curselection()
        if selected_bet_index:
            del self.user_data[self.logged_in_user]["bets"][selected_bet_index[0]]
            self.save_user_data()
            self.update_bets_display()

    # Event Handlers and Other Methods
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
            self.expand_button.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)  # Move to the top
            self.root.grid_columnconfigure(0, weight=0)  # Set column 0 to its minimum size
            self.root.grid_columnconfigure(1, weight=1)  # Make column 1 expand
        else:
            self.sidebar_frame.grid(row=2, column=0, sticky=tk.NSEW, pady=(10, 10))
            self.expand_button.grid_remove()
            self.root.grid_columnconfigure(0, weight=1)  # Reset column 0 size
            self.root.grid_columnconfigure(1, weight=100)  # Reset column 1 size
        self.sidebar_expanded = not self.sidebar_expanded

    def notify_user(self, home_team, away_team):
        messagebox.showinfo("Game Notification",
                            f"A new game featuring your favorite team(s): {home_team} vs {away_team}")

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
        self.update_odds(self.current_api_url, filtered_league=self.league_var.get(),
                         filtered_team=self.filter_var.get(), show_favorites_only=self.show_favorites_var.get())

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
            self.odds_data = odds_data  # Store the fetched odds data
            self.odds_tree.delete(*self.odds_tree.get_children())  # Clear the tree view
            rows = []
            row_index = 0  # To track the row index for alternating colors

            for game in odds_data:
                league = game.get('sport_title', 'N/A')
                home_team = game.get('home_team', 'N/A')
                away_team = game.get('away_team', 'N/A')
                commence_time = game.get('commence_time', 'N/A')
                bookmakers = game.get('bookmakers', [])

                # Convert commence_time to the user's local timezone
                if self.logged_in_user:
                    timezone = self.user_data[self.logged_in_user].get("timezone", "UTC")
                    local_time = self.convert_to_local_time(commence_time, timezone)
                else:
                    local_time = commence_time  # Default to UTC

                # Apply filter: skip filtering by league if "All" is selected
                if (filtered_league and filtered_league != "All" and league != filtered_league) or (
                        filtered_team and filtered_team not in [home_team, away_team]):
                    continue

                is_favorite = (
                        self.logged_in_user and (
                        league in self.user_data[self.logged_in_user]["favorites"]["leagues"] or
                        any(team in self.user_data[self.logged_in_user]["favorites"]["teams"] for team in
                            [home_team, away_team])
                )
                )

                if show_favorites_only and not is_favorite:
                    continue

                if bookmakers:
                    sportsbook = bookmakers[0]['title']
                    odds = ", ".join([f"{outcome['name']} @ {outcome['price']}" for outcome in
                                      bookmakers[0]['markets'][0]['outcomes']])
                else:
                    sportsbook = "No bookmakers available"
                    odds = "N/A"

                tag = 'favorite' if is_favorite else 'even' if row_index % 2 == 0 else 'odd'
                rows.append((odds, home_team, away_team, league, sportsbook, local_time, tag))

                # Check for favorite team notifications
                if self.logged_in_user and is_favorite and self.notify_var.get():
                    self.notify_user(home_team, away_team)

                row_index += 1  # Increment row index

            # Sort the rows before displaying
            if self.sort_column:
                if self.sort_column == "Home Team":
                    rows.sort(key=lambda x: (x[3], x[2]), reverse=self.sort_reverse)
                elif self.sort_column == "Away Team":
                    rows.sort(key=lambda x: (x[2], x[1]), reverse=self.sort_reverse)
                else:
                    rows.sort(key=lambda x: x[self.odds_tree["columns"].index(self.sort_column)],
                              reverse=self.sort_reverse)

            for row in rows:
                self.odds_tree.insert('', 'end', values=row[:6], tags=(row[6],))

        # Configure alternating row colors
        self.odds_tree.tag_configure('even', background='#ADD8E6')  # Light blue
        self.odds_tree.tag_configure('odd', background='#D3D3D3')  # Light gray

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
