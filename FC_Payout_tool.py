import os
import contextlib
import io
import sys
from pathlib import Path

DEFAULT_PLAYWRIGHT_CACHE = Path(os.path.expanduser('~')) / '.playwright-browsers'
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(DEFAULT_PLAYWRIGHT_CACHE))


def _run_playwright_install_cli() -> None:
    from playwright.__main__ import main as playwright_cli_main

    original_argv = sys.argv[:]
    sys.argv = ['playwright', 'install', 'chromium']
    try:
        playwright_cli_main()
    finally:
        sys.argv = original_argv


if '--playwright-install' in sys.argv:
    _run_playwright_install_cli()
    sys.exit(0)

if getattr(sys, 'frozen', False):
    bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    bundle_browsers = Path(bundle_dir) / 'playwright-browsers'
    if bundle_browsers.is_dir():
        os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(bundle_browsers)

try:
    Path(os.environ['PLAYWRIGHT_BROWSERS_PATH']).mkdir(parents=True, exist_ok=True)
except OSError:
    pass

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import re
from dataclasses import dataclass
from typing import Optional
import pyperclip
import requests
from playwright.sync_api import sync_playwright


def _chromium_relative_path() -> Path:
    if sys.platform.startswith('win'):
        return Path('chrome-win') / 'chrome.exe'
    if sys.platform.startswith('darwin'):
        return Path('chrome-mac') / 'Chromium.app' / 'Contents' / 'MacOS' / 'Chromium'
    return Path('chrome-linux') / 'chrome'


def _chromium_installed() -> bool:
    browsers_path = Path(os.environ.get('PLAYWRIGHT_BROWSERS_PATH', DEFAULT_PLAYWRIGHT_CACHE))
    if not browsers_path.is_dir():
        return False
    for entry in browsers_path.iterdir():
        if entry.is_dir() and entry.name.startswith('chromium-'):
            if (entry / _chromium_relative_path()).exists():
                return True
    return False


def ensure_playwright_ready(root: tk.Tk) -> None:
    if _chromium_installed():
        print("Playwright browser already installed; continuing.")
        return

    print("Playwright browser not found; starting download...")
    dialog = tk.Toplevel(root)
    dialog.title("Preparing Playwright")
    dialog.geometry("460x280")
    dialog.transient(root)
    dialog.grab_set()
    dialog.resizable(False, False)
    dialog.protocol("WM_DELETE_WINDOW", lambda: None)

    header = tk.Label(dialog, text="Downloading Playwright Chromium...", font=("Segoe UI", 12, "bold"))
    header.pack(pady=(12, 6))

    log_box = tk.Text(dialog, width=60, height=10, state=tk.DISABLED)
    log_box.pack(padx=12, pady=(0, 8), fill=tk.BOTH, expand=True)

    status_var = tk.StringVar(value="Downloading browser...")
    status_label = tk.Label(dialog, textvariable=status_var, font=("Segoe UI", 10, "italic"))
    status_label.pack(pady=(0, 6))

    continue_button = tk.Button(dialog, text="Continue", state=tk.DISABLED, command=dialog.destroy, width=12)
    continue_button.pack(pady=(0, 12))

    def append_line(line: str) -> None:
        print(line.rstrip())
        log_box.config(state=tk.NORMAL)
        log_box.insert(tk.END, line)
        log_box.see(tk.END)
        log_box.config(state=tk.DISABLED)

    try:
        append_line("Running: playwright install chromium\n")
        _install_playwright_browser(on_output=append_line)
    except Exception as exc:
        status_var.set(f"Installation failed: {exc}")
        append_line(str(exc) + "\n")
        continue_button.config(state=tk.NORMAL)
    else:
        if _chromium_installed():
            status_var.set("Playwright browser installed successfully.")
            append_line("Playwright Chromium ready.\n")
            continue_button.config(state=tk.NORMAL)
            dialog.after(500, dialog.destroy)
        else:
            status_var.set("Playwright installed, but Chromium not detected. Please try again.")
            continue_button.config(state=tk.NORMAL)

    root.wait_window(dialog)



def _install_playwright_browser(on_output=None):
    env = os.environ.copy()
    browsers_path = env.get('PLAYWRIGHT_BROWSERS_PATH')
    if browsers_path:
        os.makedirs(browsers_path, exist_ok=True)
        os.environ['PLAYWRIGHT_BROWSERS_PATH'] = browsers_path
    emitter = _StreamEmitter(on_output)
    with contextlib.redirect_stdout(emitter), contextlib.redirect_stderr(emitter):
        try:
            _run_playwright_install_cli()
        except SystemExit as exit_exc:
            if exit_exc.code not in (None, 0):
                output = emitter.getvalue().strip()
                raise RuntimeError(output or f"Playwright exited with code {exit_exc.code}")
        except Exception as exc:
            output = emitter.getvalue().strip()
            details = f"{exc}\n{output}" if output else str(exc)
            raise RuntimeError(details)
        finally:
            emitter.flush()


class _StreamEmitter(io.StringIO):
    def __init__(self, callback):
        super().__init__()
        self._callback = callback
        self._buffer = ''

    def write(self, s):
        super().write(s)
        if not self._callback:
            return len(s)
        self._buffer += s
        while '\n' in self._buffer:
            line, self._buffer = self._buffer.split('\n', 1)
            self._callback(line + '\n')
        return len(s)

    def flush(self):
        if self._callback and self._buffer:
            self._callback(self._buffer)
            self._buffer = ''
        return super().flush()


def _launch_chromium_with_retry(playwright):
    try:
        return playwright.chromium.launch(headless=True)
    except Exception as exc:
        message = str(exc).lower()
        if 'playwright install' in message or 'browser executable' in message:
            try:
                _install_playwright_browser()
            except Exception as install_error:  # pragma: no cover - best effort install
                raise RuntimeError(f"Failed to install Playwright browser automatically: {install_error}") from exc
            return playwright.chromium.launch(headless=True)
        raise

# List of NPCs that can show up on killmails (May not include everyone)
# Got this list from https://zkillboard.com/corporation/1000274/top/
IGNORED_CHAR_NAMES = [   	
    "Hyleus Tyrannos",
    "Arithmos Tyrannos",
    "Agreus Tyrannos",
    "Scylla Tyrannos",
    "Karybdis Tyrannos",
    "Artemis Tyrannos",
    "Orpheus Tyrannos",
    "Apollo Tyrannos",
    "Phylarch Tyrannos",
    "Metis Tyrannos",
    "Tyrannos Strategos",
    "Tisiphone Tyrannos",
    "Tyrannos Navarkos",
    "Orion Tyrannos",
    "Tyrannos Polemos",
    "Hikanta Tyrannos"
]

@dataclass
class Participant:
    name: str
    included: bool = True
    scout: bool = False
    character_id: Optional[str] = None
    share: float = 0.0
    num_shares: int = 1

class FCPayoutApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FC Payout Tool")

        self.default_dynamic_shares = None

        self.participants = []
        self.buyback_isk = 0.0
        self.last_buyback_value = "0.00"

        tk.Label(root, text="Buyback Settings:").pack(anchor="w", padx=8, pady=(10, 0))
        buyback_frame = tk.Frame(root)
        buyback_frame.pack(pady=2)
        tk.Label(buyback_frame, text="Buyback ISK:").pack(side=tk.LEFT)
        self.buyback_entry = tk.Entry(buyback_frame, width=20)
        self.buyback_entry.pack(side=tk.LEFT)
        self.buyback_entry.insert(0, "0.00")
        self.buyback_entry.bind("<FocusOut>", self.on_buyback_focus_out)

        tk.Label(root, text="Controls:").pack(anchor="w", padx=8, pady=(10, 0))
        button_frame = tk.Frame(root)
        button_frame.pack(pady=4, fill=tk.X)

        tk.Button(button_frame, text="Import from Paste", command=self.import_from_paste, bg="#FF55FF").pack(
            side=tk.LEFT, padx=4, expand=True
        )
        tk.Button(button_frame, text="Import from BR URL", command=self.import_from_br_url, bg="#ff99cc").pack(
            side=tk.LEFT, padx=4, expand=True
        )
        tk.Button(button_frame, text="Remove Selected", command=self.remove_selected, bg="#66b3ff").pack(
            side=tk.LEFT, padx=4, expand=True
        )
        tk.Button(button_frame, text="Clear All", command=self.clear_all, bg="#ffa64d").pack(
            side=tk.LEFT, padx=4, expand=True
        )
        tk.Button(button_frame, text="Copy Mail", command=self.copy_payout_mail, bg="#66ff66").pack(
            side=tk.LEFT, padx=4, expand=True
        )
        tk.Button(button_frame, text="Toggle Dynamic Shares", command=self.toggle_dynamic_shares, bg="#66ffff").pack(
            side=tk.LEFT, padx=4, expand=True
        )

        tk.Label(root, text="Participants:").pack(anchor="w", padx=8, pady=(10, 0))
        self.participant_tree = ttk.Treeview(root, columns=("Include", "Scout", "Name", "Found ID", "Share Count", "Share"), show="headings")
        self.participant_tree.tag_configure("excluded", background="#ffd6d6")
        self.participant_tree.tag_configure("included", font=("Segoe UI", 10))
        self.participant_tree.tag_configure("boldshare", font=("Segoe UI", 10, "bold"))
        for col in self.participant_tree["columns"]:
            self.participant_tree.heading(col, text=col)
            self.participant_tree.column(col, anchor="center")
        self.participant_tree.pack(fill=tk.BOTH, expand=True)
        self.participant_tree.bind("<Double-1>", self.toggle_checkbox)

        self.count_label = tk.Label(root, text="Scouts: 0 | Line: 0 | Total: 0")
        self.count_label.config(font=("Segoe UI", 11, "bold"))
        self.count_label.pack(pady=2)

        self.footer = tk.Label(root, text="Buyback ISK: 0 | Scout gets: 0 | Line gets: 0")
        self.footer.config(font=("Segoe UI", 11, "bold"))
        self.footer.pack(pady=4)

    def clear_all(self):
        self.participants.clear()
        self.buyback_isk = 0.0
        self.buyback_entry.delete(0, tk.END)
        self.buyback_entry.insert(0, "0.00")
        self.last_buyback_value = "0.00"
        self.buyback_entry.config(bg="white")
        self.refresh_tree()

    def remove_selected(self):
        selected_ids = set(self.participant_tree.selection())
        if not selected_ids:
            return
        self.participants = [p for p in self.participants if str(id(p)) not in selected_ids]
        self.refresh_tree()

    def toggle_checkbox(self, event):
        item_id = self.participant_tree.identify_row(event.y)
        if not item_id:
            return
        participant = self._participant_from_iid(item_id)
        if not participant:
            return

        column = self.participant_tree.identify_column(event.x)
        if column == '#1':
            participant.included = not participant.included
        elif column == '#2':
            participant.scout = not participant.scout
        elif column == '#5':
            raw = simpledialog.askstring("Participant Shares", "Enter the number of shares this participant should recieve.")
            if raw is None:
                return
            try:
                participant.num_shares = int(raw.strip())
            except ValueError:
                print('Input value is not an integer')
                return

        self.recalculate_shares()

    def _participant_from_iid(self, iid):
        return next((p for p in self.participants if str(id(p)) == iid), None)

    def on_buyback_focus_out(self, event = None):
        raw = self.buyback_entry.get()
        cleaned = re.sub(r"[^\d.]", "", raw)

        if cleaned == "":
            self.buyback_entry.config(bg="#ffcccc")
            return

        if cleaned != self.last_buyback_value:
            try:
                self.buyback_isk = float(cleaned)
                self.buyback_entry.delete(0, tk.END)
                self.buyback_entry.insert(0, f"{self.buyback_isk:,.2f}")
                self.buyback_entry.config(bg="white")
                self.last_buyback_value = cleaned
                self.recalculate_shares()
            except ValueError:
                self.buyback_entry.config(bg="#ffcccc")
        else:
            self.buyback_entry.config(bg="white")

    def import_from_paste(self):
        raw = self.ask_multiline_text("Import Pilots", "Paste pilot data (BR composition, FAT link pilots, one name per line, or comma seperated names")
        if raw is None:
            return

        # Detect format and parse accordingly
        if "charID-" in raw:
            matches = re.findall(r"charID[-: ]?(?P<char_id>\d+)\n(?P<name>.*)", raw)
            for char_id, name in matches:
                if name in IGNORED_CHAR_NAMES:
                    continue
                self.add_participant(Participant(name, character_id=char_id))
            self.refresh_tree()
            return

        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if "\t" in raw:
            names = []
            for line in lines:
                name = line.split("\t", 1)[0].strip()
                if name and name not in IGNORED_CHAR_NAMES:
                    names.append(name)
        elif "," in raw:
            names = []
            for line in lines:
                for name in line.split(","):
                    name_fixed = name.strip()
                    if name_fixed:
                        names.append(name_fixed)
        else:
            names = [line for line in lines if line not in IGNORED_CHAR_NAMES]

        self.add_and_lookup_names(names)

    def import_from_br_url(self):
        """Fetch battle report data from br.evetools.org"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Import from BR URL")
        dialog.geometry("450x150")
        dialog.transient(self.root)

        result = [None]

        tk.Label(dialog, text="Enter the battle report URL:", font=("Segoe UI", 10)).pack(pady=10)

        entry = tk.Entry(dialog, width=70, font=("Segoe UI", 10))
        entry.pack(padx=20, pady=10, fill=tk.X)
        entry.focus_set()

        def on_ok():
            result[0] = entry.get().strip()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=on_cancel, width=10).pack(side=tk.LEFT, padx=5)

        entry.bind("<Return>", lambda e: on_ok())

        dialog.wait_window()

        url = result[0]
        if not url:
            return

        try:
            self.root.config(cursor="watch")
            self.root.update()

            with sync_playwright() as playwright:
                browser = _launch_chromium_with_retry(playwright)
                try:
                    page = browser.new_page()
                    page.goto(url, timeout=60000)
                    page.wait_for_timeout(4500)
                    html = page.content()
                finally:
                    browser.close()

            if 'Team A' not in html and 'Team B' not in html:
                messagebox.showerror("Error", "Page loaded but no team data found. The page may still be loading.")
                return

            # Parse teams, alliances, corporations, and characters
            team_headers = list(re.finditer(r'<h4[^>]*>Team ([A-Z])[^<]*</h4>', html))
            alliance_to_team = {}
            corp_to_team = {}
            for idx, match in enumerate(team_headers):
                team_letter = match.group(1)
                start = match.end()
                end = team_headers[idx + 1].start() if idx + 1 < len(team_headers) else len(html)
                header_chunk = html[start:end]

                for ally_match in re.finditer(r'allyID-(\d+)', header_chunk):
                    ally_id = ally_match.group(1)
                    if ally_id not in alliance_to_team:
                        alliance_to_team[ally_id] = team_letter

                for corp_match in re.finditer(r'corpID-(\d+)', header_chunk):
                    corp_id = corp_match.group(1)
                    if corp_id not in corp_to_team:
                        corp_to_team[corp_id] = team_letter

            # Find all character links and associate with nearby alliance
            team_characters = {}
            for match in re.finditer(r'href="[^"]*character/(\d+)/"[^>]*>([^<]+)<', html):
                char_id = match.group(1)
                char_name = match.group(2).strip()

                if char_name in IGNORED_CHAR_NAMES:
                    continue

                search_chunk = html[match.start():match.start()+2000]
                ally_match = re.search(r'allyID-(\d+)', search_chunk)
                corp_match = re.search(r'corpID-(\d+)', search_chunk)

                ally_id = ally_match.group(1) if ally_match else None
                corp_id = corp_match.group(1) if corp_match else None

                team_letter = None
                if ally_id:
                    team_letter = alliance_to_team.get(ally_id)
                if not team_letter and corp_id:
                    team_letter = corp_to_team.get(corp_id)

                if not team_letter:
                    continue

                if team_letter not in team_characters:
                    team_characters[team_letter] = {'chars': [], 'alliances': set(), 'corporations': set()}

                if not any(c['id'] == char_id for c in team_characters[team_letter]['chars']):
                    team_characters[team_letter]['chars'].append({'id': char_id, 'name': char_name})
                    if ally_id:
                        team_characters[team_letter]['alliances'].add(ally_id)
                    if corp_id:
                        team_characters[team_letter]['corporations'].add(corp_id)

            # Build final team data with alliance names
            team_data = []
            for team_letter in sorted(team_characters.keys()):
                # Get alliance names
                alliance_names = []
                for ally_id in team_characters[team_letter]['alliances']:
                    ally_name_match = re.search(r'alliance/{}/"[^>]*>([^<]+)<'.format(ally_id), html)
                    if ally_name_match:
                        alliance_names.append(ally_name_match.group(1))

                corp_names = []
                for corp_id in team_characters[team_letter]['corporations']:
                    corp_name_match = re.search(r'corporation/{}/"[^>]*>([^<]+)<'.format(corp_id), html)
                    if corp_name_match:
                        corp_names.append(corp_name_match.group(1))

                affil_names = sorted(set(alliance_names + corp_names))

                team_data.append({
                    'name': f"Team {team_letter}",
                    'alliances': ', '.join(affil_names) if affil_names else 'Unknown',
                    'characters': team_characters[team_letter]['chars']
                })

            if not team_data:
                messagebox.showerror("Error", "No teams found.")
                return

            selected_team = self.show_team_selection_dialog(team_data)
            if selected_team is None:
                return

            count = 0
            for char in team_data[selected_team]['characters']:
                self.add_participant(Participant(char['name'], character_id=char['id']))
                count += 1

            self.refresh_tree()
            messagebox.showinfo("Success", f"Imported {count} characters!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch BR: {str(e)}")
        finally:
            self.root.config(cursor="")

    def show_team_selection_dialog(self, teams):
        """Show a dialog to select which team to import."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Team for Payout")
        dialog.transient(self.root)

        base_width = 600
        base_height = 400
        extra_height = max(0, len(teams) - 2) * 140
        dialog.geometry(f"{base_width}x{base_height + extra_height}")
        dialog.minsize(base_width, base_height)

        selected_team = [-1]
        dialog.result = None

        tk.Label(dialog, text="Which team is payout for?", font=("Segoe UI", 12, "bold")).pack(pady=10)

        info_frame = tk.Frame(dialog)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        team_frames = []
        normal_bg = "#f3f3f3"
        highlight_bg = "#cde4ff"

        def set_frame_bg(frame, bg):
            frame.config(bg=bg)
            for child in frame.winfo_children():
                try:
                    child.config(bg=bg)
                except tk.TclError:
                    pass

        def on_select(index):
            selected_team[0] = index
            for i, frame in enumerate(team_frames):
                set_frame_bg(frame, highlight_bg if i == index else normal_bg)
            accept_button.config(state=tk.NORMAL)

        def bind_clicks(widget, index):
            widget.bind("<Button-1>", lambda _evt, i=index: on_select(i))
            for child in widget.winfo_children():
                bind_clicks(child, index)

        for idx, team in enumerate(teams):
            team_frame = tk.Frame(info_frame, relief=tk.RIDGE, borderwidth=2, bg=normal_bg, cursor="hand2")
            team_frame.pack(fill=tk.X, pady=8)
            team_frames.append(team_frame)

            tk.Label(team_frame, text=team['name'], font=("Segoe UI", 11, "bold"), bg=normal_bg).pack(pady=5)
            tk.Label(
                team_frame,
                text=f"Alliances: {team['alliances']}",
                font=("Segoe UI", 9),
                bg=normal_bg,
                wraplength=base_width - 80,
                justify=tk.CENTER
            ).pack(pady=2)

            pilot_count = len(team['characters'])
            tk.Label(
                team_frame,
                text=f"Pilots: {pilot_count}",
                font=("Segoe UI", 9),
                bg=normal_bg
            ).pack(pady=2)

            bind_clicks(team_frame, idx)

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)

        def accept_selection():
            if selected_team[0] == -1:
                messagebox.showwarning("Select Team", "Please choose a team before continuing.")
                return
            dialog.result = selected_team[0]
            dialog.destroy()

        def cancel_selection():
            dialog.result = None
            dialog.destroy()

        accept_button = tk.Button(button_frame, text="Accept", width=15, state=tk.DISABLED, command=accept_selection, bg="#66ff66")
        accept_button.pack(side=tk.LEFT, padx=10)

        tk.Button(button_frame, text="Cancel", width=15, command=cancel_selection).pack(side=tk.LEFT, padx=10)

        dialog.protocol("WM_DELETE_WINDOW", cancel_selection)
        dialog.grab_set()

        if len(teams) == 1:
            on_select(0)

        dialog.wait_window()
        return dialog.result

    def add_and_lookup_names(self, names):
        if not names:
            self.refresh_tree()
            return

        characters = {}
        try:
            response = requests.post(
                "https://esi.evetech.net/latest/universe/ids/",
                json=names,
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json() or {}
            characters = {item['name']: item['id'] for item in payload.get('characters', [])}
        except Exception as e:
            print(f"Error querying ESI: {e}")

        for name in names:
            self.add_participant(Participant(name, character_id=characters.get(name)))

        self.refresh_tree()

    def add_participant(self, participant):
        for existing_participant in self.participants:
            if existing_participant.name == participant.name:
                if existing_participant.character_id is None and participant.character_id is not None:
                    existing_participant.character_id = participant.character_id
                return
            
        if self.dynamic_shares_enabled:
            participant.num_shares = self.default_dynamic_shares
        self.participants.append(participant)

    def toggle_dynamic_shares(self):
        raw = simpledialog.askstring("Dynamic Share Default", "Enter the default number of shares or 'off' to disable dynamic shares.")
        if raw is None:
            return
        raw = raw.strip()
        if raw.lower() == 'off':
            self.default_dynamic_shares = None
        else:
            try:
                default_shares = int(raw)
            except ValueError:
                print('Input value is not an integer')
                return
            for participant in self.participants:
                participant.num_shares = default_shares
            self.default_dynamic_shares = default_shares
        self.refresh_tree()

    @property
    def dynamic_shares_enabled(self):
        return self.default_dynamic_shares is not None

    def recalculate_shares(self):
        included_participants = [p for p in self.participants if p.included]
        scouts = [p for p in included_participants if p.scout]
        lines = [p for p in included_participants if not p.scout]

        if scouts:
            scout_pool = self.buyback_isk * 0.5
            line_pool = self.buyback_isk * 0.5
        else:
            scout_pool = 0
            line_pool = self.buyback_isk

        dynamic = self.dynamic_shares_enabled
        if dynamic:
            scout_total = sum(p.num_shares for p in scouts)
            line_total = sum(p.num_shares for p in lines)
            scout_share = scout_pool / scout_total if scout_total else 0
            line_share = line_pool / line_total if line_total else 0
        else:
            scout_share = scout_pool / len(scouts) if scouts else 0
            line_share = line_pool / len(lines) if lines else 0

        for participant in self.participants:
            if not participant.included:
                participant.share = 0.0
                continue

            unit = scout_share if participant.scout else line_share
            multiplier = participant.num_shares if dynamic else 1
            participant.share = unit * multiplier

        self.refresh_tree()

    def refresh_tree(self):
        self.participant_tree.delete(*self.participant_tree.get_children())
        included = [p for p in self.participants if p.included]
        scouts = [p for p in included if p.scout]
        lines = [p for p in included if not p.scout]

        dynamic_shares_active = self.dynamic_shares_enabled
        for p in sorted(self.participants, key=lambda x: x.name.lower()):
            tag = "excluded" if not p.included else "boldshare"
            self.participant_tree.insert("", "end", iid=str(id(p)), values=(
                "Yes" if p.included else "No",
                "Yes" if p.scout else "No",
                p.name,
                "Yes" if p.character_id is not None else "No",
                p.num_shares if dynamic_shares_active else "NA",
                f"{p.share:,.2f}"
            ), tags=(tag,))

        scout_isk = scouts[0].share if scouts else 0
        line_isk = lines[0].share if lines else 0

        self.count_label.config(text=f"Scouts: {len(scouts)} | Line: {len(lines)} | Total: {len(included)}")
        self.footer.config(text=f"Buyback ISK: {self.buyback_isk:,.2f} | Scout gets: {scout_isk:,.2f} | Line gets: {line_isk:,.2f}")

    def ask_multiline_text(self, title, prompt):
        """Show a dialog with a multiline text box and return the entered text."""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("600x450")
        dialog.minsize(600, 450)

        result = [None]

        tk.Label(dialog, text=prompt, font=("Segoe UI", 10)).pack(pady=10)

        def on_ok():
            result[0] = text_widget.get("1.0", tk.END).strip()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        # Pack buttons first at the bottom so they reserve their space
        button_frame = tk.Frame(dialog)
        button_frame.pack(side=tk.BOTTOM, pady=15)
        tk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=on_cancel, width=10).pack(side=tk.LEFT, padx=5)

        # Now pack the text frame to fill remaining space
        text_frame = tk.Frame(dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)

        text_widget.focus_set()
        dialog.wait_window()

        return result[0]

    def copy_payout_mail(self):
        self.on_buyback_focus_out()
        
        def format_name(participant):
            if participant.character_id:
                return f"<url=showinfo:1383//{participant.character_id}>{participant.name}</url>"
            return participant.name

        included_summary = ", ".join(format_name(p) for p in self.participants if p.included)

        scouts = [p for p in self.participants if p.included and p.scout]
        lines = [p for p in self.participants if p.included and not p.scout]

        max_line_shares = sum([p.num_shares for p in lines])
        max_scout_shares = sum([p.num_shares for p in scouts])

        scout_member_lines = ""
        for p in scouts:
            scout_member_lines += f"- {format_name(p)}"
            if len(scouts) == 1:
                scout_member_lines += " (50% = "
            else:
                scout_member_lines += ": "
            
            scout_member_lines += f"{p.share:,.2f} ISK"
            if len(scouts) == 1:
                scout_member_lines += ")"
            elif self.dynamic_shares_enabled:
                scout_member_lines += f"   {p.num_shares}/{max_scout_shares} shares"

            scout_member_lines += "\n"


        line_member_lines = ""
        for p in lines:
            line_member_lines += f"- {format_name(p)}: {p.share:,.2f} ISK"
            if self.dynamic_shares_enabled:
                line_member_lines += f"   {p.num_shares}/{max_line_shares} shares"
            line_member_lines += "\n"


        message = f"""
SEND TO:
{included_summary if included_summary else 'None'}

Hey everyone,

Thanks for joining the op! Here's the payout for the recent loot buyback.

Buyback Total: {self.buyback_isk:,.2f} ISK

Scout(s):
{scout_member_lines if scout_member_lines else 'None'}
Line Members:
{line_member_lines if line_member_lines else 'None'}
"""
        pyperclip.copy(message)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    ensure_playwright_ready(root)
    root.deiconify()
    app = FCPayoutApp(root)
    root.mainloop()
