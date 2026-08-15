# Publish this profile

Everything is pre-generated with your details, so you can push as-is. The
portrait, info card, and heatmap SVGs are already committed.

## 1. Create the magic repo

GitHub renders the README of a repo named exactly your username at the top of
your profile page.

```bash
gh repo create BhavneetBhoria29 --public --clone
cd BhavneetBhoria29
# copy every file from this folder in (including the .github and data folders)
git add -A && git commit -m "terminal profile" && git push
```

Confirm it looks right at github.com/BhavneetBhoria29 — the heatmap animates on
load, the portrait types itself in, the card prints line by line.

## 2. Turn on the daily heatmap refresh

The workflow re-scrapes your public contributions and re-renders the heatmap
every day (~06:17 UTC), then commits the result. It reads the username from the
repo owner automatically, so nothing to configure.

- Repo **Settings → Actions → General → Workflow permissions** → enable
  *Read and write permissions*.
- Go to the **Actions** tab, pick *Update profile art*, click *Run workflow*
  once to confirm it commits a fresh `contrib-heatmap.svg`.

## 3. Swap the photo or edit the card (optional)

The portrait and card are static — only regenerate when you change them.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements.txt

# new portrait: drop in a tightly-cropped headshot
python scripts/prep_photo.py source-photo.jpg   # -> source-prepped.png
python scripts/make_ascii_svg.py                # -> avi-ascii.svg

# edit the ROWS list in scripts/make_info_card.py, then:
python scripts/make_info_card.py                # -> info-card.svg
```

Preview any SVG frozen (no animation) with `STATIC=1` before committing, e.g.
`STATIC=1 python scripts/make_info_card.py`.

## Notes

- No third-party stat services and no personal access token — the only external
  dependency is GitHub's own public contributions HTML endpoint.
- GitHub strips `<script>` and most inline CSS from READMEs but *does* run
  SMIL / CSS-keyframe animation inside SVGs embedded via `<img>`. That's why all
  motion lives inside the SVG files.
- The heatmap widths (860) equal the two card columns (370 + 490) so the edges
  line up. Keep them in sync if you resize.
