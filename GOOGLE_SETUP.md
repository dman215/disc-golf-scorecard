# Google Sheets Setup Guide

## Overview
The app uses a **Google Service Account** to read/write your sheet.
This is like creating a bot user that has access to your sheet.
No user login required — just share the sheet with the bot's email.

---

## Step 1: Create a Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Click the project dropdown (top left) → **New Project**
3. Name it something like `fufa-disc-golf`
4. Click **Create**

---

## Step 2: Enable Required APIs

With your project selected:

1. Go to **APIs & Services → Library**
2. Search for **Google Sheets API** → click it → click **Enable**
3. Go back to Library, search for **Google Drive API** → **Enable**

---

## Step 3: Create a Service Account

1. Go to **APIs & Services → Credentials**
2. Click **+ Create Credentials → Service Account**
3. Fill in:
   - **Name**: `fufa-scorecard-bot`
   - **ID**: auto-fills — leave it
   - **Description**: "Reads and writes disc golf round data"
4. Click **Create and Continue**
5. Skip "Grant this service account access" — click **Continue**
6. Skip "Grant users access" — click **Done**

---

## Step 4: Download the Credentials JSON

1. On the Credentials page, click your new service account email
2. Go to the **Keys** tab
3. Click **Add Key → Create New Key**
4. Choose **JSON** → **Create**
5. A file downloads automatically — this is your `credentials.json`
6. **Move it** to the root of this project:
   ```
   disc-golf-scorecard/
   ├── credentials.json   ← put it here
   ├── backend/
   └── frontend/
   ```
7. **Important**: This file is already in `.gitignore` — never commit it

---

## Step 5: Create Your Google Sheet

1. Go to https://sheets.google.com
2. Create a new blank spreadsheet
3. Name it: `FUFA Disc Golf League 2026`
4. Copy the **Sheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/THIS_IS_YOUR_SHEET_ID/edit
   ```

---

## Step 6: Share the Sheet with the Service Account

1. Open your Google Sheet
2. Click **Share** (top right)
3. In the email field, paste the service account email
   - It looks like: `fufa-scorecard-bot@fufa-disc-golf.iam.gserviceaccount.com`
   - Find it in Google Cloud Console → Credentials
4. Set permission to **Editor**
5. Uncheck "Notify people"
6. Click **Share**

---

## Step 7: Update Your .env File

Edit `backend/.env`:

```
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_SHEET_ID=paste_your_sheet_id_here
GOOGLE_CREDENTIALS_PATH=../credentials.json
```

---

## Step 8: Test the Connection

```bash
cd backend
poetry run python -c "
from sheets_client import get_sheet_client
import os
from dotenv import load_dotenv
load_dotenv()
gc = get_sheet_client()
sh = gc.open_by_key(os.getenv('GOOGLE_SHEET_ID'))
print('✅ Connected to:', sh.title)
"
```

If you see `✅ Connected to: FUFA Disc Golf League 2026` — you're all set!

---

## Troubleshooting

**"File not found" error**: Make sure `credentials.json` is in the right place and `GOOGLE_CREDENTIALS_PATH` in `.env` points to it correctly.

**"The caller does not have permission" error**: Make sure you shared the Google Sheet with the service account email (Step 6).

**"API not enabled" error**: Double-check that both Google Sheets API and Google Drive API are enabled in your Cloud project (Step 2).
