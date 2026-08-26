async function loadFilms() {
  const res = await fetch("data/films.json");
  const data = await res.json();
  document.getElementById("tagline").textContent = data.site.tagline;
  renderGrid(data.films);
}

function renderGrid(films) {
  const grid = document.getElementById("grid");
  grid.innerHTML = "";

  for (const film of films) {
    const card = document.createElement("article");
    card.className = "card";

    const video = document.createElement("video");
    video.src = `assets/clips/${film.id}.mp4`;
    video.poster = `assets/clips/${film.id}.jpg`;
    video.preload = "metadata";
    video.muted = true;
    video.loop = true;
    video.playsInline = true;
    video.setAttribute("aria-label", `${film.title} (${film.year}) clip: ${film.scene_label}`);
    card.addEventListener("mouseenter", () => video.play().catch(() => {}));
    card.addEventListener("mouseleave", () => video.pause());

    const body = document.createElement("div");
    body.className = "card-body";

    const titleRow = document.createElement("div");
    titleRow.className = "card-title-row";
    titleRow.innerHTML = `<h2>${film.title}</h2><span class="card-year">${film.year}</span>`;

    const meta = document.createElement("div");
    meta.className = "card-meta";
    meta.textContent = `${film.director} — ${film.country} — ${film.genre}`;

    const sceneLabel = document.createElement("div");
    sceneLabel.className = "scene-label";
    sceneLabel.textContent = film.scene_label;

    const commentary = document.createElement("p");
    commentary.className = "commentary";
    commentary.textContent = film.commentary;

    const pdBasis = document.createElement("div");
    pdBasis.className = "pd-basis";
    let pdHTML = `<strong>Public domain:</strong> ${film.pd_basis}`;
    if (film.pd_caveat) {
      pdHTML += `<br>${film.pd_caveat}`;
    }
    pdBasis.innerHTML = pdHTML;

    body.append(titleRow, meta, sceneLabel, commentary, pdBasis);
    card.append(video, body);
    grid.append(card);
  }
}

loadFilms();
