import tkinter as tk
from tkinter import ttk, messagebox
import requests
import time

# DexScreener API endpoint for token details
DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex/tokens/"

# Function to fetch token data by contract address
def fetch_token_data(contract_address):
    try:
        response = requests.get(f"{DEXSCREENER_API_URL}{contract_address}")
        response.raise_for_status()
        data = response.json()
        if "pairs" not in data or len(data["pairs"]) == 0:
            messagebox.showwarning("No Data", "No token data found for the provided contract address.")
            return None
        return data["pairs"][0]  # Return the first pair (most relevant)
    except requests.exceptions.RequestException as e:  # More specific exception handling
        messagebox.showerror("Error", f"Failed to fetch data: {e}")
        return None
    except (KeyError, IndexError, TypeError) as e:  # Catch potential JSON parsing errors
        messagebox.showerror("Error", f"Error parsing data: {e}")
        return None
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        return None


# Function to calculate longevity rating (IMPROVED LOGIC)
def calculate_longevity_rating(token):
    try:  # Handle potential missing data more gracefully
        liquidity = float(token.get("liquidity", {}).get("usd", 0))
        volume = float(token.get("volume", {}).get("h24", 0))
        market_cap = float(token.get("fdv", 0))
        age_seconds = token.get("pairCreatedAt")
        if age_seconds is None:
          age = 0
        else:
          age = (time.time() - age_seconds / 1000) / (60 * 60 * 24)  # Age in days

        # Scoring weights (adjust as needed)
        liquidity_weight = 0.3  # Adjusted weights
        volume_weight = 0.3
        market_cap_weight = 0.2
        age_weight = 0.2  # Increased age weight

        # Normalize scores (using a more robust approach)
        max_liquidity = 1000000  # Example maximums (adjust as needed)
        max_volume = 1000000
        max_market_cap = 10000000
        max_age = 365  # 1 year

        liquidity_score = (liquidity / max_liquidity) * 100 if max_liquidity > 0 else 0
        volume_score = (volume / max_volume) * 100 if max_volume > 0 else 0
        market_cap_score = (market_cap / max_market_cap) * 100 if max_market_cap > 0 else 0
        age_score = (age / max_age) * 100 if max_age > 0 else 0

        # Calculate weighted score
        longevity_score = (
            liquidity_score * liquidity_weight +
            volume_score * volume_weight +
            market_cap_score * market_cap_weight +
            age_score * age_weight
        )

        return min(longevity_score, 100)  # Cap score at 100

    except (TypeError, ValueError):  # Handle cases where data might not be in correct format
        return 0  # or another appropriate default score


# Function to analyze the contract address and display results
def analyze_contract_address():
    contract_address = contract_address_entry.get().strip()
    if not contract_address:
        messagebox.showwarning("Input Error", "Please enter a contract address.")
        return

    token = fetch_token_data(contract_address)
    if not token:
        return

    base_token = token.get("baseToken", {})
    token_name = base_token.get("name", "Unknown")
    token_symbol = base_token.get("symbol", "Unknown")
    longevity_rating = calculate_longevity_rating(token)
    liquidity = float(token.get("liquidity", {}).get("usd", 0))
    volume = float(token.get("volume", {}).get("h24", 0))
    market_cap = float(token.get("fdv", 0))
    age_seconds = token.get("pairCreatedAt")
    if age_seconds is None:
      age = 0
    else:
      age = (time.time() - age_seconds / 1000) / (60 * 60 * 24)  # Age in days


    for row in tree.get_children():
        tree.delete(row)
    tree.insert("", "end", values=(
        token_name,
        token_symbol,
        f"{longevity_rating:.2f}/100",
        f"${liquidity:,.2f}",
        f"${volume:,.2f}",
        f"${market_cap:,.2f}",
        f"{age:.2f} days"  # added age
    ))


# Create the main window
root = tk.Tk()
root.title("Solana Token Scanner")
root.geometry("900x600")  # Increased height

# --- Styling ---
style = ttk.Style()
style.theme_use("clam")  # Or "alt", "default", "classic"

# --- Frames ---
input_frame = ttk.LabelFrame(root, text="Token Information", padding=10)
input_frame.pack(pady=10, padx=10, fill=tk.X)

table_frame = ttk.LabelFrame(root, text="Analysis Results", padding=10)
table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))


# --- Input Section ---
contract_address_label = ttk.Label(input_frame, text="Contract Address:", width=15)
contract_address_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

contract_address_entry = ttk.Entry(input_frame, width=60)
contract_address_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

analyze_button = ttk.Button(input_frame, text="Analyze", command=analyze_contract_address)
analyze_button.grid(row=1, column=0, columnspan=2, pady=(5,0))


# --- Table (Treeview) ---
columns = ("Name", "Symbol", "Longevity Rating", "Liquidity", "24h Volume", "Market Cap", "Age")  # Added "Age"
tree = ttk.Treeview(table_frame, columns=columns, show="headings")

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=120, anchor=tk.CENTER)  # Adjusted column widths

# --- Scrollbar ---
scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
tree.configure(yscroll=scrollbar_y.set)
scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

root.mainloop()