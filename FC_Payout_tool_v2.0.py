import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import re
import pyperclip
import requests
import json

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

class Participant:
    def __init__(self, name, included=True, scout=False, character_id=None):
        self.name = name
        self.included = included
        self.scout = scout
        self.share = 0.0
        self.character_id = character_id
        self.num_shares = 1

class FCPayoutApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FC Payout Tool (v2.1)")

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

        tk.Button(button_frame, text="Import From BR", command=self.import_br_characters, bg="#FF55FF").pack(
            side=tk.LEFT, padx=4, expand=True
        )
        tk.Button(button_frame, text="Import From Names", command=self.import_by_name, bg="#FF5555").pack(
            side=tk.LEFT, padx=4, expand=True
        )
        tk.Button(button_frame, text="Import From Fat Link", command=self.import_by_fat_link, bg="#FFFF55").pack(
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
        selected = self.participant_tree.selection()
        for sel in selected:
            p = next((p for p in self.participants if str(id(p)) == sel), None)
            if p:
                self.participants.remove(p)
        self.refresh_tree()

    def toggle_checkbox(self, event):
        item_id = self.participant_tree.identify_row(event.y)
        col = self.participant_tree.identify_column(event.x)
        if not item_id:
            return
        p = next((p for p in self.participants if str(id(p)) == item_id), None)
        if not p:
            return
        if col == '#1':
            p.included = not p.included
        elif col == '#2':
            p.scout = not p.scout
        elif col == '#5':
            raw = simpledialog.askstring("Participant Shares", "Enter the number of shares this participant should recieve.")
            try:
                shares = int(raw.strip())
            except ValueError:
                print('Input value is not an integer')
                return
            p.num_shares = shares

        self.recalculate_shares()

    def on_buyback_focus_out(self, event):
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

        if self.dynamic_shares_enabled():
            num_scout_shares = sum(p.num_shares for p in scouts)
            num_line_shares = sum(p.num_shares for p in lines)

            scout_share = scout_pool / num_scout_shares if num_scout_shares > 0 else 0
            line_share = line_pool / num_line_shares if num_line_shares > 0 else 0

            for p in self.participants:
                if not p.included:
                    p.share = 0.0
                elif p.scout:
                    p.share = scout_share * p.num_shares
                else:
                    p.share = line_share * p.num_shares
        else:
            scout_share = scout_pool / len(scouts) if scouts else 0
            line_share = line_pool / len(lines) if lines else 0

            for p in self.participants:
                if not p.included:
                    p.share = 0.0
                elif p.scout:
                    p.share = scout_share
                else:
                    p.share = line_share

        self.refresh_tree()

    def refresh_tree(self):
        self.participant_tree.delete(*self.participant_tree.get_children())
        included = [p for p in self.participants if p.included]
        scouts = [p for p in included if p.scout]
        lines = [p for p in included if not p.scout]

        for p in sorted(self.participants, key=lambda x: x.name.lower()):
            tag = "excluded" if not p.included else "boldshare"
            self.participant_tree.insert("", "end", iid=str(id(p)), values=(
                "Yes" if p.included else "No",
                "Yes" if p.scout else "No",
                p.name,
                "Yes" if p.character_id is not None else "No",
                p.num_shares if self.dynamic_shares_enabled() else "NA",
                f"{p.share:,.2f}"
            ), tags=(tag,))

        scout_isk = scouts[0].share if scouts else 0
        line_isk = lines[0].share if lines else 0

        self.count_label.config(text=f"Scouts: {len(scouts)} | Line: {len(lines)} | Total: {len(included)}")
        self.footer.config(text=f"Buyback ISK: {self.buyback_isk:,.2f} | Scout gets: {scout_isk:,.2f} | Line gets: {line_isk:,.2f}")

    def copy_payout_mail(self):
        included_summary = ", ".join([
            f"<url=showinfo:1383//{p.character_id}>{p.name}</url>" if p.character_id else p.name
            for p in self.participants if p.included
        ])

        scouts = [p for p in self.participants if p.included and p.scout]
        lines = [p for p in self.participants if p.included and not p.scout]

        scout_member_lines = "\n".join([
            f"- <url=showinfo:1383//{p.character_id}>{p.name}</url> (50% = {p.share:,.2f} ISK)" if p.character_id else f"- {p.name} (50% = {p.share:,.2f} ISK)"
            for p in scouts
        ])

        line_member_lines = "\n".join([
            f"- <url=showinfo:1383//{p.character_id}>{p.name}</url>: {p.share:,.2f} ISK" if p.character_id else f"- {p.name}: {p.share:,.2f} ISK"
            for p in lines
        ])

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

    def import_br_characters(self):
        raw = simpledialog.askstring("BR Import", "Paste pilot data from a BR composition")
        if raw is None:
            return
        matches = re.findall(r"charID[-: ]?(?P<char_id>\d+)\n(?P<name>.*)", raw)
        for match in matches:
            id = match[0]
            name = match[1]
            if name in IGNORED_CHAR_NAMES:
                continue
            self.add_participant(Participant(name, character_id=id))
        
        self.refresh_tree()

    def add_and_lookup_names(self, names):
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post("https://esi.evetech.net/latest/universe/ids/", headers=headers, data=json.dumps(names))
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error querying ESI: {e}")

        if 'characters' in response.json():
            characters = {character['name']: character['id'] for character in response.json()['characters']}
        else:
            characters = dict()

        for name in names:
            id = None
            if name in characters:
                id = characters[name]
            self.add_participant(Participant(name, character_id=id))

        self.refresh_tree()

    def import_by_name(self):
        raw = simpledialog.askstring("Import by Name", "Paste pilot names with one on each line")
        if raw is None:
            return
        names = []

        for line in raw.splitlines():
            line = line.strip()
            if line in IGNORED_CHAR_NAMES:
                continue
            names.append(line)

        self.add_and_lookup_names(names)

    def import_by_fat_link(self):
        raw = simpledialog.askstring("FAT link pilots", "Paste pilots from a fat link")
        if raw is None:
            return
        names = []
        for line in raw.splitlines():
            name = re.match(r"^[^\t]+", line)
            names.append(name[0])
        
        self.add_and_lookup_names(names)

    def add_participant(self, participant):
        for existing_participant in self.participants:
            if existing_participant.name == participant.name:
                if existing_participant.character_id is None and participant.character_id is not None:
                    existing_participant.character_id = participant.character_id
                return
            
        if self.default_dynamic_shares is not None:
            participant.num_shares = self.default_dynamic_shares
        self.participants.append(participant)

    def toggle_dynamic_shares(self):
        raw = simpledialog.askstring("Dynamic Share Default", "Enter the default number of shares or 'off' to disable dynamic shares.")
        if raw is None:
            return
        raw = raw.strip()
        if raw.lower() == 'off':
            self.default_dynamic_shares = None
            self.refresh_tree()
            return
        try:
            default_shares = int(raw.strip())
        except ValueError:
            print('Input value is not an integer')
            return
        for participant in self.participants:
            participant.num_shares = default_shares
        self.default_dynamic_shares = default_shares

        self.refresh_tree()


    def dynamic_shares_enabled(self):
        return self.default_dynamic_shares is not None


if __name__ == "__main__":
    root = tk.Tk()
    app = FCPayoutApp(root)
    root.mainloop()
