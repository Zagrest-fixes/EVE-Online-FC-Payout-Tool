# EVE-Online-FC-Payout-Tool
Tool to help fc do less and faster paperwork when doing payouts

---

## Executable Packages (recommended)

### Download from Releases

Pre-built executables for Windows, Linux, and macOS are automatically generated for each release. You can download them from the [Releases page](https://github.com/TsuroTsero/EVE-Online-FC-Payout-Tool/releases) without needing Python installed.

**Available downloads**
- `FC-Payout-Tool-vX.Y.Z-Windows.exe` - Windows executable (no console window)
- `FC-Payout-Tool-vX.Y.Z-Linux` - Linux executable
- `FC-Payout-Tool-vX.Y.Z-macOS` - macOS executable

**Note for Linux/macOS:** You may need to make the file executable after download:
```bash
chmod +x FC-Payout-Tool-vX.Y.Z-Linux  # or FC-Payout-Tool-vX.Y.Z-macOS
```

---

## Manual Build

### Step 1: Install Python

1. Go to: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Download **Python 3.9 or newer**
3. Run the installer

**IMPORTANT:** During installation, check the box: Add Python to PATH

## Step 2: Download tool and install dependencies

Either clone this GitHub repo, or download `FC_Payout_tool.py` and `requirements.txt` into a folder. Open a terminal or Powershell window to this folder and run the following command:

```bash
pip install -r requirements.txt
```

The packages installed will be:
- `pyperclip` – copying in-game mail text to clipboard
- `requests` - handles character id lookups and battle report imports
- `playwright` - pulls br.evetools.org data for parsing

### Step 3: Install playwright

The tool comes bundled with an installer you can run:

```bash
python FC_Payout_tool.py --playwright-install
```

### Step 4: Run the tool

To launch the FC payout GUI:

```bash
python FC_Payout_tool.py
```

You will be able to:
- Enter Buyback ISK amount
- Import pilots in bulk from br.evetools.org by going to report ---> composition ---> chars and copying pilots including their photo and name.
- Import pilots in bulk by name with a list of names each on its own line.
- Import pilots from a fat link by copy pasting the names (can and likely will include the system and ship they were in when they clicked the link. These will be ignored)
- Import pilots automatically from a br.evetools.org URL
- Mark scouts and exclude pilots from payout
- Automatically generate an in-game mail and copy to clipboard

---

## Troubleshooting and Developing

### Fix for Linux Clipboard

If `pyperclip` doesn’t work on Linux, install `xclip`:

```bash
sudo apt install xclip
```

### Build Your Own Executable

To manually build a standalone executable from source:

1. Install PyInstaller:

```bash
pip install pyinstaller
```

2. Build the executable:

**Windows (no console window):**
```bash
pyinstaller --onefile --noconsole FC_Payout_tool.py
```

**Linux/macOS:**
```bash
pyinstaller --onefile FC_Payout_tool.py
```

The built executable will be in the `dist/` folder.

**Automated Builds:** This project uses GitHub Actions to automatically build executables for all platforms on every release tag. The workflow builds on native runners to ensure compatibility.

### Contributing

- Clone this repo using `git clone`
- Generate and use a Python Virtual Environment `python -m venv .venv` and `source .venv/bin/activate`
- Always update requirements.txt from inside the venv `pipreqs . --ignore .venv,tests --encoding utf-8 --force`
