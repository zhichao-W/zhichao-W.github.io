# zhichao-w.github.io

My personal website: https://zhichao-w.github.io/

Built with [Jekyll](https://jekyllrb.com/) and the [al-folio](https://github.com/alshedivat/al-folio) starter, with a custom look:
light mode uses a clean cobalt style, dark mode looks like a typeset preprint on graph paper.

## Where things live

| To change | Edit |
| --- | --- |
| Bio, photo caption, home page sections | `_pages/about.md` |
| Profile photo | replace `assets/img/prof_pic.jpg` (portrait, about 4:5) |
| Publications | `_bibliography/papers.bib` (add `selected = {true}` to show a paper on the home page) |
| A figure next to a paper | put an image in `assets/img/publication_preview/` and add `preview = {file.png}` to that paper |
| Talks, teaching, CV | `_pages/talks.md`, `_pages/teaching.md`, `pdf/CV.pdf` |
| Blog and projects in the menu | set `nav: true` in `_pages/blog.md` and `_pages/projects.md` (hidden for now) |
| GitHub link | uncomment `github_username` in `_data/socials.yml` |
| Blog posts | add `_posts/YYYY-MM-DD-title.md` (see `_drafts/example-post.md`) |
| Projects | add files to `_projects/` (see `_projects/example_project.md`) |
| Name, links, site settings | `_config.yml`, `_data/socials.yml` |
| Colours and fonts | `_sass/_zw.scss` |

## Preview locally

With Docker (easiest, nothing else to install):

```bash
docker compose up
# open http://localhost:8080
```

Or with Ruby 3.3 and ImageMagick installed (`brew install ruby imagemagick` on a Mac):

```bash
bundle install
bundle exec jekyll serve
# open http://localhost:4000
```

## Publishing

Pushing to `main` runs `.github/workflows/deploy.yml`, which builds the site and publishes it with GitHub Pages.

## Notes on the theme

Two theme files are local copies with small changes:

- `assets/css/main.scss`: the core stylesheet entry, plus one line that loads `_sass/_zw.scss`.
- `assets/js/theme.js`: the theme switcher, changed to two modes (light and dark) instead of three.

Both are recorded in `.al-folio-overrides.yml`; after updating the theme gems, run
`bundle exec al-folio upgrade overrides audit` to check whether they need refreshing.
