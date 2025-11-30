import requests
import tkinter as tk 
from tkinter import ttk 
from datetime import datetime 


# NOAA SWPC ENDPOINTS

PLASMA_URL = "https://services.swpc.noaa.gov/products/solar-wind/plasma-5-minute.json"
MAG_URL = "https://services.swpc.noaa.gov/products/solar-wind/mag-5-minute.json"
KP_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"

REFRESH_INTERVAL_MS = 5 * 60 * 1000 # 5 minutes



# Data Fetch Functions

def fetch_json_array(url, timeout=8):
    """Fetch a NOAA JSON array-of-arrays and return it."""
    headers = {"User-Agent": "SpaceWeatherMonitor/1.0 (Python requests)"}
    resp = requests.get(url, timeout=timeout, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list) or len(data) < 2:
        raise ValueError(f"Unexpected JSON structure from {url}")
    return data


def get_latest_plasma():
    """Returns a dict:
        {
            'time': 'YYYY-MM-DD HH:MM:SS',
            'density': float,
            'speed':float,
            'temperature': float
    }
    """
    data = fetch_json_array(PLASMA_URL)
    header, *rows = data
    latest = rows[-1]

    idx_time = header.index("time_tag")
    idx_density = header.index("density")
    idx_speed = header.index("speed")
    idx_temp = header.index("temperature")

    return {
            "time": latest[idx_time],
            "density": float(latest[idx_density]),
            "speed": float(latest[idx_speed]),
            "temperature": float(latest[idx_temp]),
    }


def get_latest_mag():
    """Returns a dict:
        {
            'time': 'YYYY-MM-DD HH:MM:SS',
            'bz': float,
            'bt': float,
    }
    """

    data = fetch_json_array(MAG_URL)
    header, *rows = data
    latest = rows[-1]

    idx_time = header.index("time_tag")
    idx_bz = header.index("bz_gsm")
    idx_bt = header.index("bt")

    return {
            "time": latest[idx_time],
            "bz": float(latest[idx_bz]),
            "bt": float(latest[idx_bt]),
    }


def get_latest_kp():
    """Returns a dict:
        {
            'time': 'YYYY-MM-DD HH:MM:SS',
            'kp': float,
            'a_running': float,
            'station_count': int 
    }
    """

    data = fetch_json_array(KP_URL)
    header, *rows = data
    latest = rows[-1]

    idx_time = header.index("time_tag")
    idx_kp = header.index("Kp")
    idx_a = header.index("a_running")
    idx_station = header.index("station_count")

    return {
            "time": latest[idx_time],
            "kp": float(latest[idx_kp]),
            "a_running": float(latest[idx_a]),
            "station_count": int(latest[idx_station]),
    }


# Interpretation Helpers! *IMPORTANT* 

def classify_kp(kp):
    """Rough Classification of Kp into a label and color.
    This is a simplified mapping, not the official NOAA G-Scale.
    """
    if kp < 3:
        return "Quiet", "#22c55e" #green
    elif kp < 4: 
        return "Unsettled", "#a3e635"
    elif kp < 5:
        return "Active", "#facc15" #yellow
    elif kp < 6:
        return "Minor Storm", "#fb923c" #red
    elif kp < 7:
        return "Moderate Storm", "#f97316"
    else:
        return "Severe Storm", "#ef4444" #even redder


def describe_bz(bz):
    if bz > 2:
        return "Northward IMF (less coupling)"
    elif bz < -2:
        return "Southward IMF (strong coupling)"
    else:
        return "Neutral-ish IMF orientation!"


# GUI APP

class SpaceWeatherApp:
    def __init__(self, root):
        self.root = root
        root.title("Solar Weather Monitor")

        # Dark theme
        bg = "#020617" # slate-950
        fg = "#e5e7eb" # grey-200
        accent = "#33d3ee" #cyan-400

        root.configure(bg=bg)

        # Use ttk but override a bit
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg, font=("JetBrains Mono", 10))
        style.configure("Title.TLabel", font=("JetBrains Mono", 18, "bold"), foreground=accent)
        style.configure("CardTitle.TLabel", font=("JetBrains Mono", 11, "bold"), foreground="#a5b4fc")
        style.configure("Value.TLabel", font=("JetBrains Mono", 16, "bold"))
        style.configure("Status.TLabel", font=("JetBrains Mono", 11))
        style.configure("TButton", font=("JetBrains Mono", 10), padding=6)

        # --------- Layout ----------
        main = ttk.Frame(root, padding=16)
        main.pack(fill="both", expand=True)

        # Title row
        title_row = ttk.Frame(main)
        title_row.pack(fill="x", pady=(0, 12))

        self.title_label = ttk.Label(
            title_row,
            text="SPACE WEATHER MONITOR // NOAA SWPC",
            style="Title.TLabel"
        )
        self.title_label.pack(side="left")

        self.updated_label = ttk.Label(
            title_row,
            text="Last update: --",
            font=("JetBrains Mono", 9),
        )
        self.updated_label.pack(side="right")

        # Cards row
        cards = ttk.Frame(main)
        cards.pack(fill="x")

        self.card_kp = self._build_card(cards, "Geomagnetic Activity (Kp)")
        self.card_plasma = self._build_card(cards, "Solar Wind Plasma")
        self.card_mag = self._build_card(cards, "Magnetic Field (Bz/Bt)")

        self.card_kp.pack(side="left", expand=True, fill="both", padx=(0, 8))
        self.card_plasma.pack(side="left", expand=True, fill="both", padx=4)
        self.card_mag.pack(side="left", expand=True, fill="both", padx=(8, 0))

        # Status row
        status_row = ttk.Frame(main)
        status_row.pack(fill="x", pady=(12, 8))

        self.status_label = ttk.Label(
            status_row,
            text="Status: waiting for first update...",
            style="Status.TLabel",
            wraplength=700,
            justify="left"
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        # Controls row
        control_row = ttk.Frame(main)
        control_row.pack(fill="x", pady=(4, 0))

        self.refresh_button = ttk.Button(
            control_row,
            text="Refresh now",
            command=self.update_data
        )
        self.refresh_button.pack(side="left")

        self.auto_label = ttk.Label(
            control_row,
            text="Auto-refresh: every 5 minutes",
            font=("JetBrains Mono", 9)
        )
        self.auto_label.pack(side="right")

        # Card value labels (keep references)
        self.kp_value_label = None
        self.kp_detail_label = None
        self.kp_circle = None

        self.plasma_value_label = None
        self.plasma_detail_label = None

        self.mag_value_label = None
        self.mag_detail_label = None

        # Attach widgets to cards
        self._init_card_contents()

        # Schedule first update
        self.update_data()

    def _build_card(self, parent, title):
        frame = ttk.Frame(parent, padding=10, relief="ridge")
        title_label = ttk.Label(frame, text=title, style="CardTitle.TLabel")
        title_label.pack(anchor="w")
        return frame

    def _init_card_contents(self):
        # Kp card
        # Use a small canvas circle as a "storm level" indicator
        kp_canvas = tk.Canvas(self.card_kp, width=40, height=40, highlightthickness=0, bg="#020617")
        kp_canvas.pack(anchor="w", pady=(4, 0))
        self.kp_circle = kp_canvas.create_oval(5, 5, 35, 35, fill="#111827", outline="#1f2933")

        self.kp_value_label = ttk.Label(self.card_kp, text="Kp: --", style="Value.TLabel")
        self.kp_value_label.pack(anchor="w", pady=(4, 0))

        self.kp_detail_label = ttk.Label(self.card_kp, text="Level: --", style="Status.TLabel")
        self.kp_detail_label.pack(anchor="w", pady=(2, 0))

        # Plasma card
        self.plasma_value_label = ttk.Label(self.card_plasma, text="Speed: -- km/s", style="Value.TLabel")
        self.plasma_value_label.pack(anchor="w", pady=(8, 0))

        self.plasma_detail_label = ttk.Label(
            self.card_plasma,
            text="Density: -- p/cm³\nTemp: -- K",
            style="Status.TLabel"
        )
        self.plasma_detail_label.pack(anchor="w", pady=(2, 0))

        # Mag card
        self.mag_value_label = ttk.Label(self.card_mag, text="Bz: -- nT", style="Value.TLabel")
        self.mag_value_label.pack(anchor="w", pady=(8, 0))

        self.mag_detail_label = ttk.Label(
            self.card_mag,
            text="Bt: -- nT\nIMF: --",
            style="Status.TLabel"
        )
        self.mag_detail_label.pack(anchor="w", pady=(2, 0))

    def update_data(self):
        """Fetch data from NOAA and update the GUI."""
        try:
            plasma = get_latest_plasma()
            mag = get_latest_mag()
            kp = get_latest_kp()

            # --- Update Kp card ---
            kp_value = kp["kp"]
            kp_label, kp_color = classify_kp(kp_value)

            self.kp_value_label.config(text=f"Kp: {kp_value:.1f}")
            self.kp_detail_label.config(text=f"Level: {kp_label}")
            # recolor circle
            kp_canvas = self.card_kp.winfo_children()[1]  # the canvas we created
            kp_canvas.itemconfig(self.kp_circle, fill=kp_color)

            # --- Update Plasma card ---
            self.plasma_value_label.config(text=f"Speed: {plasma['speed']:.0f} km/s")
            self.plasma_detail_label.config(
                text=f"Density: {plasma['density']:.2f} p/cm³\nTemp: {plasma['temperature']:.0f} K"
            )

            # --- Update Mag card ---
            bz = mag["bz"]
            bt = mag["bt"]
            self.mag_value_label.config(text=f"Bz: {bz:.2f} nT")
            self.mag_detail_label.config(
                text=f"Bt: {bt:.2f} nT\nIMF: {describe_bz(bz)}"
            )

            # --- Status line ---
            status_text = self._build_status_text(kp_value, plasma["speed"], bz)
            self.status_label.config(text=f"Status: {status_text}")

            # --- Updated label ---
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
            self.updated_label.config(text=f"Last update: {now}")

        except requests.exceptions.RequestException as e:
            self.status_label.config(text=f"Status: Network error while fetching space weather data: {e}")
        except Exception as e:
            self.status_label.config(text=f"Status: Unexpected error: {e}")

        # Schedule next auto-refresh
        self.root.after(REFRESH_INTERVAL_MS, self.update_data)

    def _build_status_text(self, kp, speed, bz):
        pieces = []

        # Geomagnetic
        kp_label, _ = classify_kp(kp)
        pieces.append(f"Kp {kp:.1f} ({kp_label})")

        # Solar wind
        if speed > 700:
            pieces.append("Very fast solar wind")
        elif speed > 500:
            pieces.append("Elevated solar wind speed")
        else:
            pieces.append("Normal solar wind speed")

        # Bz
        if bz < -5:
            pieces.append("Strong southward Bz → higher geomagnetic coupling")
        elif bz < -2:
            pieces.append("Southward Bz → some geomagnetic coupling")
        elif bz > 2:
            pieces.append("Northward Bz → reduced coupling")
        else:
            pieces.append("Weak/neutral Bz")

        return " | ".join(pieces)


def main():
    root = tk.Tk()
    app = SpaceWeatherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main() 

