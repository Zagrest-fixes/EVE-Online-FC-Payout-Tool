import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import re
import pyperclip
import requests
import json
from playwright.sync_api import sync_playwright
import time

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

    def import_from_paste(self):
        raw = self.ask_multiline_text("Import Pilots", "Paste pilot data (BR composition, FAT link pilots, or one name per line):")
        if raw is None:
            return

        # Detect format and parse accordingly
        if "charID" in raw:
            # BR format: contains charID markers with IDs and names
            matches = re.findall(r"charID[-: ]?(?P<char_id>\d+)\n(?P<name>.*)", raw)
            for match in matches:
                id = match[0]
                name = match[1]
                if name in IGNORED_CHAR_NAMES:
                    continue
                self.add_participant(Participant(name, character_id=id))
            self.refresh_tree()
        elif "\t" in raw:
            # FAT link format: contains tab characters
            names = []
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                name_match = re.match(r"^([^\t]+)", line)
                if name_match:
                    name = name_match.group(1).strip()
                    if name and name not in IGNORED_CHAR_NAMES:
                        names.append(name)
            self.add_and_lookup_names(names)
        else:
            # Raw names format: newline-separated names
            names = []
            for line in raw.splitlines():
                line = line.strip()
                if line and line not in IGNORED_CHAR_NAMES:
                    names.append(line)
            self.add_and_lookup_names(names)

    def import_from_br_url(self):
        """Fetch battle report data from br.evetools.org using Playwright."""
        url = simpledialog.askstring("Import from BR URL", "Enter the battle report URL (e.g., https://br.evetools.org/br/...)")
        if not url:
            return

        try:
            self.root.config(cursor="watch")
            self.root.update()

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url)
                page.wait_for_selector('[role="tab"]', timeout=10000)
                time.sleep(2)
                page.get_by_role('tab', name='Composition').click()
                time.sleep(1)

                for button in page.get_by_text('Chars').all():
                    button.click()
                    time.sleep(0.5)

                time.sleep(1)
                html_content = page.content()
                browser.close()

                # Parse HTML using HTMLParser
                from html.parser import HTMLParser

                class BRParser(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.teams = []
                        self.current_team = None
                        self.current_corp = None

                    def handle_starttag(self, tag, attrs):
                        attrs_dict = dict(attrs)

                        if tag == 'img' and 'alt' in attrs_dict:
                            alt = attrs_dict['alt']
                            if alt.startswith('allyID-'):
                                self.current_team = {
                                    'name': f"Team {chr(65 + len(self.teams))}",
                                    'alliance': None,
                                    'corps': []
                                }
                                self.teams.append(self.current_team)
                            elif alt.startswith('corpID-') and self.current_team is not None:
                                self.current_corp = {
                                    'id': alt.replace('corpID-', ''),
                                    'name': 'Unknown',
                                    'charCount': '0',
                                    'characters': []
                                }
                                self.current_team['corps'].append(self.current_corp)

                        if tag == 'a' and 'href' in attrs_dict:
                            href = attrs_dict['href']
                            if '/character/' in href and self.current_corp is not None:
                                char_id = href.rstrip('/').split('/')[-1]
                                if char_id.isdigit():
                                    self.current_corp['characters'].append({'id': char_id, 'name': None})
                            elif '/corporation/' in href and self.current_corp is not None:
                                self.current_corp['_awaiting_corp_name'] = True
                            elif '/alliance/' in href and self.current_team is not None and self.current_team['alliance'] is None:
                                self.current_team['_awaiting_ally_name'] = True

                    def handle_data(self, data):
                        data = data.strip()
                        if not data:
                            return

                        if self.current_corp and self.current_corp['characters']:
                            last_char = self.current_corp['characters'][-1]
                            if last_char['name'] is None:
                                last_char['name'] = data

                        if self.current_corp and self.current_corp.get('_awaiting_corp_name'):
                            self.current_corp['name'] = data
                            match = re.match(r'\((\d+)\)', data)
                            if match:
                                self.current_corp['charCount'] = match.group(1)
                            del self.current_corp['_awaiting_corp_name']

                        if self.current_team and self.current_team.get('_awaiting_ally_name'):
                            self.current_team['alliance'] = data
                            del self.current_team['_awaiting_ally_name']

                parser = BRParser()
                parser.feed(html_content)
                team_data = parser.teams

                if not team_data:
                    self.root.config(cursor="")
                    messagebox.showerror("Error", "No teams found on the battle report page.")
                    return

                selected_team = self.show_team_selection_dialog(team_data)
                if selected_team is None:
                    self.root.config(cursor="")
                    return

                count = 0
                for corp in team_data[selected_team]['corps']:
                    for char in corp['characters']:
                        if char['name'] not in IGNORED_CHAR_NAMES:
                            self.add_participant(Participant(char['name'], character_id=char['id']))
                            count += 1

                self.refresh_tree()
                self.root.config(cursor="")
                messagebox.showinfo("Success", f"Imported {count} characters from {team_data[selected_team]['name']}!")

        except Exception as e:
            self.root.config(cursor="")
            messagebox.showerror("Error", f"Failed to fetch battle report data: {str(e)}\n\nMake sure Playwright is installed correctly. Run: playwright install chromium")

    def show_team_selection_dialog(self, teams):
        """Show a dialog to select which team to import."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Team for Payout")
        dialog.geometry("800x500")

        selected_team = [None]

        tk.Label(dialog, text="Which team is payout for?", font=("Segoe UI", 12, "bold")).pack(pady=10)

        # Create a frame for the table
        table_frame = tk.Frame(dialog)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create scrollbars
        v_scrollbar = tk.Scrollbar(table_frame)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        h_scrollbar = tk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Create canvas for scrolling
        canvas = tk.Canvas(table_frame, yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        v_scrollbar.config(command=canvas.yview)
        h_scrollbar.config(command=canvas.xview)

        # Create frame inside canvas
        content_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=content_frame, anchor='nw')

        # Get all unique corps across all teams
        all_corps = set()
        for team in teams:
            for corp in team['corps']:
                all_corps.add(corp['name'])
        all_corps = sorted(all_corps)

        # Create header row
        tk.Label(content_frame, text="Corporation", font=("Segoe UI", 10, "bold"),
                borderwidth=1, relief="solid", width=30).grid(row=0, column=0, sticky='nsew')

        for idx, team in enumerate(teams):
            team_label = f"{team['name']}\n{team['alliance'] or 'Unknown'}"
            tk.Label(content_frame, text=team_label, font=("Segoe UI", 10, "bold"),
                    borderwidth=1, relief="solid", width=20).grid(row=0, column=idx+1, sticky='nsew')

        # Create rows for each corp
        for row_idx, corp_name in enumerate(all_corps, start=1):
            tk.Label(content_frame, text=corp_name, borderwidth=1, relief="solid",
                    anchor='w', padx=5).grid(row=row_idx, column=0, sticky='nsew')

            for col_idx, team in enumerate(teams):
                # Find if this corp exists in this team
                corp_in_team = next((c for c in team['corps'] if c['name'] == corp_name), None)
                count_text = corp_in_team['charCount'] if corp_in_team else ""

                tk.Label(content_frame, text=count_text, borderwidth=1, relief="solid").grid(
                    row=row_idx, column=col_idx+1, sticky='nsew')

        # Update scroll region
        content_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox('all'))

        # Create team selection buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)

        def select_team(team_idx):
            selected_team[0] = team_idx
            dialog.destroy()

        for idx, team in enumerate(teams):
            btn_text = f"Import {team['name']} ({team['alliance'] or 'Unknown'})"
            tk.Button(button_frame, text=btn_text, command=lambda i=idx: select_team(i),
                     width=30, bg="#66ff66").pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="Cancel", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)

        dialog.wait_window()
        return selected_team[0]

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

    def ask_multiline_text(self, title, prompt):
        """Show a dialog with a multiline text box and return the entered text."""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("600x400")

        result = [None]

        tk.Label(dialog, text=prompt, font=("Segoe UI", 10)).pack(pady=10)

        text_frame = tk.Frame(dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)

        def on_ok():
            result[0] = text_widget.get("1.0", tk.END).strip()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=on_cancel, width=10).pack(side=tk.LEFT, padx=5)

        text_widget.focus_set()
        dialog.wait_window()

        return result[0]

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


if __name__ == "__main__":
    root = tk.Tk()
    app = FCPayoutApp(root)
    root.mainloop()
