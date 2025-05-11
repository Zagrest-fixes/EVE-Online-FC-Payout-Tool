import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import asyncio
import threading
import re
import pyperclip
from playwright.async_api import async_playwright
# needed for exe
import os

# Force Playwright to use local browser folder (for .exe compatibility)
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(os.getcwd(), "playwright-browsers")
# needed for exe

class Participant:
    def __init__(self, name, included=True, scout=False, character_id=None):
        self.name = name
        self.included = included
        self.scout = scout
        self.share = 0.0
        self.character_id = character_id

class FCPayoutApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FC Payout Tool(v1.0)")

        self.participants = []
        self.buyback_isk = 0.0
        self.dropped_isk = 0.0

        tk.Label(root, text="Paste zKill Links:").pack(anchor="w", padx=8)
        self.kill_entry = tk.Text(root, height=3, width=80)
        self.kill_entry.pack(pady=2)

        tk.Label(root, text="Buyback Settings:").pack(anchor="w", padx=8, pady=(10, 0))
        buyback_frame = tk.Frame(root)
        buyback_frame.pack(pady=2)
        tk.Label(buyback_frame, text="Buyback ISK:").pack(side=tk.LEFT)
        self.buyback_entry = tk.Entry(buyback_frame, width=20)
        self.buyback_entry.pack(side=tk.LEFT)
        self.buyback_entry.insert(0, "0.00")

        tk.Label(root, text="Controls:").pack(anchor="w", padx=8, pady=(10, 0))
        button_frame = tk.Frame(root)
        button_frame.pack(pady=4)
        tk.Button(button_frame, text="Import zKill Links", command=self.start_import).pack(side=tk.LEFT, padx=4)
        tk.Button(button_frame, text="Bulk Import Pilots", command=self.import_bulk_characters).pack(side=tk.LEFT, padx=4)
        tk.Button(button_frame, text="Recalculate", command=self.recalculate_shares).pack(side=tk.LEFT, padx=4)
        tk.Button(button_frame, text="Remove Selected", command=self.remove_selected).pack(side=tk.LEFT, padx=4)
        tk.Button(button_frame, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=4)
        tk.Button(button_frame, text="Copy Mail", command=self.copy_mail).pack(side=tk.LEFT, padx=4)

        tk.Label(root, text="Participants:").pack(anchor="w", padx=8, pady=(10, 0))
        self.tree = ttk.Treeview(root, columns=("Include", "Scout", "Name", "Share"), show="headings")
        self.tree.tag_configure("excluded", background="#ffd6d6")
        self.tree.tag_configure("included", font=("Segoe UI", 10))
        self.tree.tag_configure("boldshare", font=("Segoe UI", 10, "bold"))
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.toggle_checkbox)

        self.count_label = tk.Label(root, text="Scouts: 0 | Line: 0 | Total: 0"); self.count_label.config(font=("Segoe UI", 11, "bold"))
        self.count_label.pack(pady=2);
        self.footer = tk.Label(root, text="Buyback ISK: 0 | Scout gets: 0 | Line gets: 0 | Dropped ISK: 0")
        self.footer.config(font=("Segoe UI", 11, "bold"))
        self.footer.pack(pady=4)

    def start_import(self):
        links = self.kill_entry.get("1.0", tk.END).strip().splitlines()
        threading.Thread(target=self.import_links_thread, args=(links,)).start()

    def import_links_thread(self, links):
        asyncio.run(self.async_import_zkill(links))

    async def async_import_zkill(self, links):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context = await browser.new_context()
                for link in links:
                    try:
                        page = await context.new_page()
                        await page.goto(link.strip(), timeout=60000)
                        await page.wait_for_timeout(2000)
                        try:
                            agree_btn = page.locator("button:has-text('AGREE')")
                            await agree_btn.click()
                            await page.wait_for_timeout(500)
                        except:
                            pass
                        try:
                            elements = await page.locator("*:has-text('Dropped')").all()
                            for el in elements:
                                text = await el.inner_text()
                                match = re.search(r"Dropped:\s*([\d,]+)", text)
                                if match:
                                    self.dropped_isk += float(match.group(1).replace(",", ""))
                                    break
                        except:
                            pass
                        try:
                            rows = await page.locator("tr.attacker").all()
                            for row in rows:
                                pilot_links = row.locator("td.pilotinfo a[href^='/character/']")
                                if await pilot_links.count() == 0:
                                    continue
                                pilot_link = pilot_links.first
                                href = await pilot_link.get_attribute("href")
                                name = (await pilot_link.inner_text()).strip()
                                if href and name and name not in [p.name for p in self.participants]:
                                    char_id = href.split("/")[2]
                                    self.participants.append(Participant(name, character_id=char_id))
                        except:
                            pass
                        await page.close()
                    except Exception as e:
                        print(f"Error loading {link}: {e}")
            finally:
                await browser.close()
        self.refresh_tree()

    def remove_selected(self):
        selected = self.tree.selection()
        for sel in selected:
            idx = int(sel)
            del self.participants[idx]
        self.refresh_tree()

    def clear_all(self):
        self.participants.clear()
        self.refresh_tree()

    def toggle_checkbox(self, event):
        item_id = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not item_id:
            return
        idx = int(item_id)
        part = self.participants[idx]
        if col == '#1':
            part.included = not part.included
        elif col == '#2':
            part.scout = not part.scout
        self.recalculate_shares()

    def recalculate_shares(self):
        try:
            self.buyback_isk = float(self.buyback_entry.get().replace(",", ""))
        except ValueError:
            messagebox.showerror("Invalid ISK", "Please enter a valid Buyback ISK amount.")
            return

        included_participants = [p for p in self.participants if p.included]
        total_scouts = [p for p in included_participants if p.scout]
        total_lines = [p for p in included_participants if not p.scout]

        if total_scouts:
            scout_pool = self.buyback_isk * 0.5
            line_pool = self.buyback_isk * 0.5
        else:
            scout_pool = 0
            line_pool = self.buyback_isk

        scout_share = scout_pool / len(total_scouts) if total_scouts else 0
        line_share = line_pool / len(total_lines) if total_lines else 0

        for p in self.participants:
            if not p.included:
                p.share = 0.0
            elif p.scout:
                p.share = scout_share
            else:
                p.share = line_share

        self.refresh_tree()

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        included = [p for p in self.participants if p.included]
        scouts = [p for p in included if p.scout]
        lines = [p for p in included if not p.scout]
        for idx, p in enumerate(self.participants):
            tag = "excluded" if not p.included else "boldshare"
            self.tree.insert("", "end", iid=str(idx), values=(
                "Yes" if p.included else "No",
                "Yes" if p.scout else "No",
                p.name,
                f"{p.share:,.2f}"
            ), tags=(tag,))
        scout_isk = scouts[0].share if scouts else 0
        line_isk = lines[0].share if lines else 0
        self.count_label.config(text=f"Scouts: {len(scouts)} | Line: {len(lines)} | Total: {len(included)}")
        self.footer.config(text=f"Buyback ISK: {self.buyback_isk:,.2f} | Scout gets: {scout_isk:,.2f} | Line gets: {line_isk:,.2f} | Dropped ISK: {self.dropped_isk:,.2f}")

    def copy_mail(self):
        scouts = [p for p in self.participants if p.included and p.scout]
        lines = [p for p in self.participants if p.included and not p.scout]
        scout_lines = "\n".join([
            f"- <url=showinfo:1383//{p.character_id}>{p.name}</url> (50% = {p.share:,.2f} ISK)" if p.character_id else f"- {p.name} (50% = {p.share:,.2f} ISK)"
            for p in scouts
        ])
        line_lines = "\n".join([
            f"- <url=showinfo:1383//{p.character_id}>{p.name}</url>: {p.share:,.2f} ISK" if p.character_id else f"- {p.name}: {p.share:,.2f} ISK"
            for p in lines
        ])
        message = f"""Hey everyone,

Thanks for joining the op! Here's the payout for the recent loot buyback.

Buyback Total: {self.buyback_isk:,.2f} ISK
Dropped ISK: {self.dropped_isk:,.2f} ISK

Scout(s):
{scout_lines if scout_lines else 'None'}

Line Members:
{line_lines if line_lines else 'None'}

Fly safe,
- FC"""
        pyperclip.copy(message)
        messagebox.showinfo("Copied", "Payout mail copied to clipboard.")


    def import_bulk_characters(self):
        raw = simpledialog.askstring("Bulk Import", "Paste pilot data in format:\ncharID-########\nName")
        if raw:
            lines = raw.strip().splitlines()
            char_id = None
            for line in lines:
                line = line.strip()
                if line.lower().startswith("charid"):
                    match = re.match(r"charID[-: ]?(\d+)", line, re.IGNORECASE)
                    if match:
                        char_id = match.group(1)
                elif line:
                    self.participants.append(Participant(line, character_id=char_id))
                    char_id = None
            self.refresh_tree()


if __name__ == "__main__":
    root = tk.Tk()
    app = FCPayoutApp(root)
    root.mainloop()