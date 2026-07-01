# Setup Guide (Roman Urdu)

## Step 1: Files repo mein daalein
In teeno files/folders ko apne GitHub repo `my-project` mein upload karein:
- `generate_and_post.py`
- `prompts.txt`
- `.github/workflows/hourly-post.yml`

GitHub website par: repo kholein > "Add file" > "Upload files" > files drag-drop karein > "Commit changes".
(`.github/workflows` folder structure exactly waisi hi rakhni hai.)

## Step 2: FB_PAGES secret banayein
Har Facebook Page ke liye aapko Page ID aur Page Access Token chahiye (jo aapke paas already hain).

Format ye hoga (JSON list):

```json
[
  {"name": "Page 1", "id": "PAGE_ID_YAHAN", "token": "PAGE_ACCESS_TOKEN_YAHAN"},
  {"name": "Page 2", "id": "PAGE_ID_YAHAN", "token": "PAGE_ACCESS_TOKEN_YAHAN"}
]
```

Isko GitHub Secret mein daalne ka tarika:
1. Repo kholein > **Settings** tab
2. Left menu mein **Secrets and variables** > **Actions**
3. **New repository secret** par click karein
4. Name: `FB_PAGES`
5. Value: upar wala JSON (apne real Page IDs/Tokens ke saath) paste karein
6. **Add secret** click karein

## Step 3: Test karein
Repo mein **Actions** tab kholein > "Hourly AI Image Post" workflow select karein > **Run workflow** button se manually ek baar chala kar dekhein ke sahi kaam kar raha hai.

Agar sab theek gaya to ye ab har ghante khud-ba-khud chalega — laptop ya mobile on hone ki zaroorat nahi.

## Zaroori Notes
- Page Access Token **long-lived** hona chahiye, warna kuch dinon mein expire ho jayega aur posting ruk jayegi. Agar token short-lived hai to Facebook Developer console se "long-lived token" generate karwa lein.
- GitHub free plan par scheduled Actions agar repo 60 din tak inactive rahe to automatically pause ho jate hain — bas kabhi kabhi repo mein koi chhoti tabdeeli (commit) kar dena kaafi hai.
- `prompts.txt` mein aap apni marzi ke prompts add/remove kar sakte hain — jitne zyada prompts, utni variety.
