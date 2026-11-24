# Boxes and Arrows

System design, architecture, infrastructure, network protocols and secure architecture with risk and GRC, from zero to mastery, in plain words. Built and curated by <a href="https://anmol-vats-portfolio.vercel.app/" target="_blank" rel="noopener">Anmol Vats</a>.

**Website.** https://nucleiav.github.io/sys-arch/

## What is in here

| Part | What you get | Where |
| --- | --- | --- |
| Start here | 9 short steps, from what a system is to how an architect thinks, with a scale simulator and a practice step at the end. | [`basics.html`](basics.html) |
| Concepts | 38 lessons in 6 levels, numbered 1.1 to 6.11. Design versus architecture, how a request travels, REST, GraphQL, gRPC, real time APIs, estimation, scaling, databases, caching, sharding, consistency, queues, consensus, failure, observability, security, microservices, multi-region and stream processing. Each level ends with a practice page. | [`learn/`](learn/) |
| Secure architecture, risk and GRC | Level 6 of Concepts, 11 lessons that follow one product, a connected infant incubator. Security principles, cryptography and access control, security requirements and standards, secure by design, threat modeling with STRIDE, controls, risk management, secure development and testing, patches and incidents in the field, laws and GRC, and the security architect's role with a release decision report. Every other lesson and design also has a security lens section. | [`learn/s01.html`](learn/s01.html) |
| Infra | 14 lessons in 4 levels. Git, branches, GitHub and pull requests, GitHub Actions, Linux, Docker, Compose, Kubernetes, AWS, networks and storage, serverless, Terraform and safe deploys. Practice includes commands, Dockerfiles, YAML and Terraform to read and fix. Each level ends with a practice page. | [`infra/`](infra/) |
| Protocols | 62 protocols animated packet by packet, with a network view, a sequence view, a current step panel, a packet inspector with fields and hex, playback speed and practice questions for each protocol. On wide screens the step panel and inspector sit beside the animation. | [`protocols.html`](protocols.html) |
| Design it | The method, then 17 full design tasks, from a link shortener to an AI chat app, a peer to peer network, a discussion forum and a secure medical device platform. | [`design/`](design/) |
| Interview | Every interview question in one bank with a filter and a random question button. Write an answer and get feedback on the key points you covered. | [`interview.html`](interview.html) |
| The plan | 14 weeks, about 6 hours a week, mixing all parts. Ticks save in your browser. | [`plan.html`](plan.html) |
| Library | Books, docs, practice sites, specifications and engineering blogs. | [`library.html`](library.html) |

Every lesson has the idea in one minute, an animated diagram, key words, how it works, real life scenarios, trade-offs, common mistakes, a security lens, a practice quiz, practice interview questions, a practice desk and references. Practice includes spot the bug, spot the risk or GRC issue, name the benefit, pick the mitigation and find a workaround. Answer options and dropdowns are shuffled each time a page loads.

## How the pages are made

Every page is generated from YAML. Edit the content, then rebuild.

```
content/basics.yaml              Start here steps
content/learn/_order.yaml        levels and lesson order for Concepts
content/learn/*.yaml             concept lessons, level 6 security lessons (s01 to s11) and level practice pages (p1 to p6)
content/infra/_order.yaml        levels and lesson order for Infra
content/infra/*.yaml             infra lessons and level practice pages (ip1 to ip4)
content/design/*.yaml            design tasks d00 to d17
content/protocols/*.yaml         protocol animations, one list per file
content/protocols/_page.yaml     help text under the protocol explorer
content/interview.yaml, plan.yaml, library.yaml, home.yaml
tools/build.py                   turns the YAML into HTML pages, SVG diagrams and assets/js/protocol-data.js
tools/check_style.py             checks the writing rules
tools/fix_yaml_quotes.py         quotes YAML values that contain ": " by mistake
```

Rebuild with Python 3.12 or later and PyYAML.

```
pip install pyyaml
python tools/check_style.py
python tools/build.py
```

### Content format

- Text uses a small markup. `**bold**`, `` `code` ``, `[text](url)`, lists with `- ` or `1. `, tables with `| a | b |`, headings with `### `, code blocks with three backticks, and boxes that start with `!plain`, `!warn`, `!eli5`, `!key`, `!fact` or `!tip`.
- Diagrams are described in YAML (`flow`, `cycle`, `layers`, `split`) and drawn as SVG at build time.
- Lesson scenes are blocks on an isometric grid (`nodes` with `x` and `y`) and `steps` that light blocks (`on`), move packets (`flow`), add badges (`mark`), hide blocks (`show`) and update stat cards (`stats`).
- Questions are `mcq`, `fill` (use `____` for the blank), `num` (with `tol` and `unit`), `sort`, `open` and interview questions with `keys`, a model answer `a` and extra feedback `fb`. Any question can show code or config in `info`.
- A level practice page has `kind: practice` and `rounds`, like a practice desk.
- `security` adds a Security lens section to a lesson, or a Security and abuse section to a design.

### Protocol format

```
- id: tcp
  name: TCP
  full: Transmission Control Protocol
  layer: 4
  cat: core            # core, app, security or data
  transport: IP
  port: "any"
  title: ...
  lede: ...
  overview: |          # markup
  nodes:
    client: [Label, sub label such as an IP, icon, x, y]
  links: [[client, net], [net, srv]]
  steps:
    - t: Step title
      tag: handshake
      d: What happens, in plain words.
      f: {Field: value}                 # shown in the current step panel
      p:                                # packets, in order
        - [from, to, "label", kind, {fields: {Name: value}, raw: "text bytes", hex: "optional real wire bytes"}]
      good: A tip.
  quiz: [...]
  refs: [...]
```

The hex view shows `hex` bytes when given, the bytes of `raw` for text protocols, and otherwise each field value encoded as bytes, colour coded per field. Packet kinds are `req`, `res`, `ctl`, `sec`, `data` and `bad`. Icons are laptop, phone, user, camera, tv, router, switch, ap, cloud, globe, gateway, server, web, mail, folder, terminal, dns, clock, proxy, db, queue, lock, key, shield and plc. In the network view a packet travels along the shortest path of links between its two nodes.

### Writing rules

Plain, simple English for a beginner, following ASD-STE100 Simplified Technical English for most sentences. Short sentences, active voice, one idea per sentence. No em dashes, no emojis and no colons in prose. `check_style.py` fails on dashes, emojis and colons, and reports how many sentences have 20 words or fewer.

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

## Credits

- Site, lessons, designs, protocol animations, diagrams, practice and model answers. [Anmol Vats](https://anmol-vats-portfolio.vercel.app/).
- Inspired by and pointing to [System Design Simulator](https://systemdesignsimulator.org/), [Designed to Scale](https://designed-to-scale.vercel.app/), [Protocol Explorer](https://protocolexplorer.org/) and the [Advent of System Design](https://www.devmaxx.dev/advent). No code or text from those sites is used.
- Same look and engine as [Prompt to Patch](https://nucleiav.github.io/ai-cyber/).
- Protocol facts follow the IETF RFCs and vendor documentation linked on each protocol.
- All linked books, papers, posts and tools belong to their authors.
