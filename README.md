# Boxes and Arrows

System design and architecture, from zero to mastery, in plain words. Built and curated by <a href="https://anmol-vats-portfolio.vercel.app/" target="_blank" rel="noopener">Anmol Vats</a>.

**Website.** https://nucleiav.github.io/sys-arch/

## What is in here

| Part | What you get | Where |
| --- | --- | --- |
| Start here | 8 short steps, from what a system is to how an architect thinks. Diagrams, an animated request, quick checks and a scale simulator where you add a load balancer, cache, replicas, a CDN and a queue until 10 million users are healthy. | [`basics.html`](basics.html) |
| Concepts | 22 lessons in 5 levels. Foundations, data, many machines, running it for real, mastery. Each lesson has the idea in one minute, an animated step by step diagram, key words, how it works with diagrams, real life scenarios, a trade-off table, common mistakes, a quiz with multiple choice, fill-ups, small math and sorting, interview questions with feedback, a practice desk and references. | [`learn/`](learn/) |
| Design it | The method, then 14 full design tasks. Link shortener, chat, news feed, notifications, autocomplete, video streaming, file sync, ride sharing, ticket flash sale, payments, web crawler, leaderboard, collaborative docs and an AI chat app. Each has requirements, estimation questions, the API, the data model, an animated walkthrough, deep dives, trade-offs, a "your turn" task and follow-up questions. | [`design/`](design/) |
| Interview | Every interview question in one bank, filtered by level, with a random question button. Write your answer and press Get feedback to see which key points you covered, a model answer and what makes it great. | [`interview.html`](interview.html) |
| The plan | 10 weeks, about 5 hours a week, with every lesson and design in order. Ticks save in your browser. | [`plan.html`](plan.html) |
| Library | Books, practice sites, free guides and engineering blogs, with a note on when each helps. | [`library.html`](library.html) |

## How the pages are made

Every page is generated from YAML. Edit the content, then rebuild.

```
content/basics.yaml        Start here steps
content/learn/l01.yaml ... concept lessons, l01 to l22
content/design/d00.yaml .. design tasks, d00 to d14
content/interview.yaml     interview page intro, method and general questions
content/plan.yaml          the 10 week plan
content/library.yaml       the library
content/home.yaml          home page text
tools/build.py             turns the YAML into HTML pages and SVG diagrams
tools/check_style.py       checks the writing rules
```

Rebuild with Python 3.12 or later and PyYAML.

```
pip install pyyaml
python tools/check_style.py
python tools/build.py
```

### Content format

- Text uses a small markup. `**bold**`, `` `code` ``, `[text](url)`, lists with `- ` or `1. `, tables with `| a | b |`, headings with `### `, and boxes that start with `!plain`, `!warn`, `!eli5`, `!key`, `!fact` or `!tip`.
- Diagrams are described in YAML (`flow`, `cycle`, `layers`, `split`) and drawn as SVG at build time.
- Animated scenes are a list of blocks on a grid (`nodes` with `x` and `y`) and `steps`. Each step can light blocks (`on`), send packets along links (`flow`, colored `ink`, `atk`, `def` or `pen`), add badges (`mark` with `ok`, `bad` or `warn`), hide blocks (`show`) and update the stat cards (`stats`).
- Questions are `mcq`, `fill` (use `____` for the blank and a list of accepted answers), `num` (with `tol` and `unit`), `sort`, `open` and interview questions. Interview questions have `keys`, a list of key points with words that show the point was covered, a model answer `a` and extra feedback `fb`.

### Writing rules

Plain, simple English for a beginner. No em dashes, no emojis, and no colons in prose. Use a full stop instead. `check_style.py` fails if a rule is broken.

## Run it on your machine

No build step is needed to view it. From the repository folder:

```
python -m http.server 8000
```

Open `http://localhost:8000`.

## Host it on GitHub Pages

1. Push this repository to GitHub.
2. Open **Settings**, then **Pages**.
3. Under **Build and deployment**, set **Source** to **Deploy from a branch**.
4. Select the `main` branch and the `/ (root)` folder, then save.
5. The site appears at `https://<user>.github.io/sys-arch/` after a minute or two.

## Light and dark mode

The sun and moon button in the header switches themes. The choice is saved in your browser. With no choice saved, the site follows your system setting.

## Credits

- Site, lessons, designs, diagrams, practice desks and model answers. [Anmol Vats](https://anmol-vats-portfolio.vercel.app/).
- Inspired by and pointing to [System Design Simulator](https://systemdesignsimulator.org/), [Designed to Scale](https://designed-to-scale.vercel.app/) and the [Advent of System Design](https://www.devmaxx.dev/advent).
- Same look and engine as [Prompt to Patch](https://nucleiav.github.io/ai-cyber/).
- All linked books, papers, posts and tools belong to their authors.
