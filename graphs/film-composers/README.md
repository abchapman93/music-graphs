---
name: "Film Composers"
description: "Contemporary film composers, the directors they collaborate with, and the films that link them — seeded with Ludwig Göransson, Jonny Greenwood, and Trent Reznor."
spotify_playlist_url: "https://open.spotify.com/playlist/0IXAc1LvHKhruQBew81vwP"
resources:
  - type: wikipedia-page
    url: https://en.wikipedia.org/wiki/Ludwig_G%C3%B6ransson
    label: "Ludwig Göransson"
  - type: wikipedia-page
    url: https://en.wikipedia.org/wiki/Jonny_Greenwood
    label: "Jonny Greenwood"
  - type: wikipedia-page
    url: https://en.wikipedia.org/wiki/Trent_Reznor_and_Atticus_Ross
    label: "Trent Reznor and Atticus Ross (film scores)"
  - type: wikipedia-category
    url: https://en.wikipedia.org/wiki/Category:21st-century_American_film_score_composers
    label: "21st-century American film score composers"
---

A graph built around the composer↔director relationship in contemporary film. Nodes are composers (`person`), directors (`person`), and films (`album`, treating each score as the film's representative release). Each film links its director to its composer. Seeded from three working composers — Ludwig Göransson, Jonny Greenwood, and Trent Reznor — and expanded by following each composer's filmography to their directors, then each director's filmography back to other composers.
