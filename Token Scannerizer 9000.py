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
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch data: {e}")
        return None

# Function to calculate longevity rating
def calculate_longevity_rating(token):
    liquidity = float(token.get("liquidity", {}).get("usd", 0))
    volume = float(token.get("volume", {}).get("h24", 0))
    market_cap = float(token.get("fdv", 0))
    age = (time.time() - int(token.get("pairCreatedAt", 0)) / 1000) / (60 * 60 * 24)  # Age in days

    # Scoring weights (adjust as needed)
    liquidity_weight = 0.4
    volume_weight = 0.3
    market_cap_weight = 0.2
    age_weight = 0.1

    # Normalize scores (example: scale liquidity to 0-100)
    liquidity_score = min(liquidity / 1000000, 100)  # 1M liquidity = 100 points
    volume_score = min(volume / 1000000, 100)  # 1M volume = 100 points
    market_cap_score = min(market_cap / 10000000, 100)  # 10M market cap = 100 points
    age_score = min(age / 365, 100)  # 1 year = 100 points

    # Calculate weighted score
    longevity_score = (
        liquidity_score * liquidity_weight +
        volume_score * volume_weight +
        market_cap_score * market_cap_weight +
        age_score * age_weight
    )

    return min(longevity_score, 100)  # Cap score at 100

# Function to analyze the contract address and display results
def analyze_contract_address():
    contract_address = contract_address_entry.get().strip()
    if not contract_address:
        messagebox.showwarning("Input Error", "Please enter a contract address.")
        return

    # Fetch token data
    token = fetch_token_data(contract_address)
    if not token:
        return

    # Extract token details
    base_token = token.get("baseToken", {})
    token_name = base_token.get("name", "Unknown")
    token_symbol = base_token.get("symbol", "Unknown")
    longevity_rating = calculate_longevity_rating(token)
    liquidity = float(token.get("liquidity", {}).get("usd", 0))
    volume = float(token.get("volume", {}).get("h24", 0))
    market_cap = float(token.get("fdv", 0))

    # Display results in the table
    for row in tree.get_children():
        tree.delete(row)
    tree.insert("", "end", values=(
        token_name,
        token_symbol,
        f"{longevity_rating:.2f}/100",
        f"${liquidity:,.2f}",
        f"${volume:,.2f}",
        f"${market_cap:,.2f}"
    ))

# Create the main window
root = tk.Tk()
root.title("Solana Token Scanner")
root.geometry("800x400")

# Create a frame for the input field
input_frame = ttk.Frame(root)
input_frame.pack(pady=10)

# Add a label and entry field for the contract address
contract_address_label = ttk.Label(input_frame, text="Contract Address:")
contract_address_label.pack(side=tk.LEFT, padx=5)
contract_address_entry = ttk.Entry(input_frame, width=50)
contract_address_entry.pack(side=tk.LEFT, padx=5)

# Add an analyze button
analyze_button = ttk.Button(input_frame, text="Analyze", command=analyze_contract_address)
analyze_button.pack(side=tk.LEFT, padx=5)

# Create a frame for the table
table_frame = ttk.Frame(root)
table_frame.pack(fill=tk.BOTH, expand=True)

# Create a treeview widget for the table
columns = ("Name", "Symbol", "Longevity Rating", "Liquidity", "24h Volume", "Market Cap")
tree = ttk.Treeview(table_frame, columns=columns, show="headings")
tree.heading("Name", text="Name")
tree.heading("Symbol", text="Symbol")
tree.heading("Longevity Rating", text="Longevity Rating")
tree.heading("Liquidity", text="Liquidity")
tree.heading("24h Volume", text="24h Volume")
tree.heading("Market Cap", text="Market Cap")

# Set column widths
tree.column("Name", width=150)
tree.column("Symbol", width=80)
tree.column("Longevity Rating", width=120)
tree.column("Liquidity", width=120)
tree.column("24h Volume", width=120)
tree.column("Market Cap", width=120)

# Add scrollbar
scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
tree.configure(yscroll=scrollbar.set)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
tree.pack(fill=tk.BOTH, expand=True)

# Run the application
root.mainloop()