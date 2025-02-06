import tkinter as tk
from tkinter import ttk, messagebox
import requests
import time
from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()
# Constants
DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex/tokens/"

def fetch_token_data(contract_address):
    try:
        response = requests.get(f"{DEXSCREENER_API_URL}{contract_address}")
        response.raise_for_status()
        data = response.json()
        
        if "pairs" not in data or len(data["pairs"]) == 0:
            messagebox.showwarning("No Data", "No token data found for the provided contract address.")
            return None
        
        return data["pairs"][0]
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch data: {e}")
    except (KeyError, IndexError, TypeError) as e:
        messagebox.showerror("Error", f"Error parsing data: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")
    
    return None

def calculate_longevity_rating(token):
    try:
        liquidity = float(token.get("liquidity", {}).get("usd", 0))
        volume = float(token.get("volume", {}).get("h24", 0))
        market_cap = float(token.get("fdv", 0))
        age_seconds = token.get("pairCreatedAt")
        age = (time.time() - age_seconds / 1000) / (60 * 60 * 24) if age_seconds else 0

        weights = {
            "liquidity": 0.3,
            "volume": 0.3,
            "market_cap": 0.2,
            "age": 0.2
        }

        max_values = {
            "liquidity": 1000000,
            "volume": 1000000,
            "market_cap": 10000000,
            "age": 365
        }

        scores = {
            "liquidity": (liquidity / max_values["liquidity"]) * 100,
            "volume": (volume / max_values["volume"]) * 100,
            "market_cap": (market_cap / max_values["market_cap"]) * 100,
            "age": (age / max_values["age"]) * 100
        }

        longevity_score = sum(scores[key] * weights[key] for key in weights)

        return min(longevity_score, 100)
    except (TypeError, ValueError):
        return 0

def get_coingecko_data(contract_address):
    cg = CoinGeckoAPI()
    try:
        data = cg.get_coin_info_from_contract_address_by_id(id='solana', contract_address=contract_address)
        return data
    except Exception as e:
        print(f"Error fetching CoinGecko data: {e}")
        return None

def calculate_trustability_rating(token, coingecko_data):
    score = 0
    if coingecko_data:
        community_score = coingecko_data.get('community_score', 0)
        score += community_score * 20

    longevity_rating = calculate_longevity_rating(token)
    score += longevity_rating * 0.5

    return min(score, 100)

def analyze_contract_address():
    contract_address = contract_address_entry.get().strip()
    if not contract_address:
        messagebox.showwarning("Input Error", "Please enter a contract address.")
        return

    token = fetch_token_data(contract_address)
    if not token:
        return

    coingecko_data = get_coingecko_data(contract_address)
    trustability_rating = calculate_trustability_rating(token, coingecko_data)

    base_token = token.get("baseToken", {})
    token_name = base_token.get("name", "Unknown")
    token_symbol = base_token.get("symbol", "Unknown")
    longevity_rating = calculate_longevity_rating(token)
    liquidity = float(token.get("liquidity", {}).get("usd", 0))
    volume = float(token.get("volume", {}).get("h24", 0))
    market_cap = float(token.get("fdv", 0))
    age_seconds = token.get("pairCreatedAt")
    age = (time.time() - age_seconds / 1000) / (60 * 60 * 24) if age_seconds else 0

    tree.delete(*tree.get_children())
    tree.insert("", "end", values=(
        token_name,
        token_symbol,
        f"{longevity_rating:.2f}/100",
        f"${liquidity:,.2f}",
        f"${volume:,.2f}",
        f"${market_cap:,.2f}",
        f"{age:.2f} days",
        f"{trustability_rating:.2f}/100"
    ))

root = tk.Tk()
root.title("Solana Token Scanner")
root.geometry("900x600")

style = ttk.Style()
style.theme_use("clam")

input_frame = ttk.LabelFrame(root, text="Token Information", padding=10)
input_frame.pack(pady=10, padx=10, fill=tk.X)

table_frame = ttk.LabelFrame(root, text="Analysis Results", padding=10)
table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

contract_address_label = ttk.Label(input_frame, text="Contract Address:", width=15)
contract_address_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

contract_address_entry = ttk.Entry(input_frame, width=60)
contract_address_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

analyze_button = ttk.Button(input_frame, text="Analyze", command=analyze_contract_address)
analyze_button.grid(row=1, column=0, columnspan=2, pady=(5,0))

columns = ("Name", "Symbol", "Longevity Rating", "Liquidity", "24h Volume", "Market Cap", "Age", "Trustability Rating")
tree = ttk.Treeview(table_frame, columns=columns, show="headings")

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=120, anchor=tk.CENTER)

scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
tree.configure(yscroll=scrollbar_y.set)
scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

root.mainloop()
