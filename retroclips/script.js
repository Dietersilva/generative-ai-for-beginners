async function loadFilms() {
  const res = await fetch("data/films.json");
  const data = await res.json();
  document.getElementById("tagline").textContent = data.site.tagline;
  renderGrid(data.films);
}

// Only one thing should be making sound at a time: unmuting a clip stops any
// narration in progress, and narrating stops/mutes whichever clip is playing.
function stopAllAudio(exceptVideo) {
  window.speechSynthesis.cancel();
  document.querySelectorAll("video").forEach((v) => {
    if (v !== exceptVideo) v.muted = true;
  });
}

function renderGrid(films) {
  const grid = document.getElementById("grid");
  grid.innerHTML = "";

  const speechSupported = "speechSynthesis" in window;

  for (const film of films) {
    const card = document.createElement("article");
    card.className = "card";

    const clipFrame = document.createElement("div");
    clipFrame.className = "clip-frame";

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

    const soundBadge = document.createElement("button");
    soundBadge.type = "button";
    soundBadge.className = "sound-badge";
    const syncSoundBadge = () => {
      soundBadge.textContent = video.muted ? "🔇" : "🔊";
      soundBadge.setAttribute("aria-label", video.muted ? "Play clip with sound" : "Mute clip");
    };
    syncSoundBadge();
    video.addEventListener("volumechange", syncSoundBadge);

    const toggleSound = (event) => {
      event.stopPropagation();
      if (video.muted) {
        stopAllAudio(video);
        video.muted = false;
        video.play().catch(() => {});
      } else {
        video.muted = true;
      }
    };
    video.addEventListener("click", toggleSound);
    soundBadge.addEventListener("click", toggleSound);

    // Decorative caption ticker, burned onto the clip so the commentary
    // reads even muted/without looking away from the video. The real,
    // screen-reader-visible text is the .commentary paragraph below --
    // this is aria-hidden to avoid announcing the same text twice.
    const caption = document.createElement("div");
    caption.className = "clip-caption";
    caption.setAttribute("aria-hidden", "true");
    const captionTrack = document.createElement("div");
    captionTrack.className = "clip-caption-track";
    const secondsToRead = Math.min(28, Math.max(14, film.commentary.length * 0.09));
    captionTrack.style.animationDuration = `${secondsToRead}s`;
    const captionSpanA = document.createElement("span");
    captionSpanA.textContent = film.commentary;
    const captionSpanB = document.createElement("span");
    captionSpanB.textContent = film.commentary;
    captionTrack.append(captionSpanA, captionSpanB);
    caption.append(captionTrack);

    clipFrame.append(video, caption, soundBadge);

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

    const commentaryRow = document.createElement("div");
    commentaryRow.className = "commentary-row";

    const commentary = document.createElement("p");
    commentary.className = "commentary";
    commentary.textContent = film.commentary;
    commentaryRow.append(commentary);

    if (speechSupported) {
      const narrateBtn = document.createElement("button");
      narrateBtn.type = "button";
      narrateBtn.className = "narrate-btn";
      narrateBtn.textContent = "🔊 Listen";
      narrateBtn.setAttribute("aria-label", `Listen to the commentary for ${film.title}`);
      narrateBtn.addEventListener("click", () => {
        const isThisUtterance = narrateBtn.classList.contains("narrating");
        stopAllAudio(null);
        document.querySelectorAll(".narrate-btn.narrating").forEach((b) => b.classList.remove("narrating"));
        if (isThisUtterance) return; // clicking again just stops it (stopAllAudio already cancelled)

        const utterance = new SpeechSynthesisUtterance(film.commentary);
        utterance.rate = 0.95;
        narrateBtn.classList.add("narrating");
        narrateBtn.textContent = "⏸ Reading…";
        utterance.onend = utterance.onerror = () => {
          narrateBtn.classList.remove("narrating");
          narrateBtn.textContent = "🔊 Listen";
        };
        window.speechSynthesis.speak(utterance);
      });
      commentaryRow.append(narrateBtn);
    }

    const pdBasis = document.createElement("div");
    pdBasis.className = "pd-basis";
    let pdHTML = `<strong>Public domain:</strong> ${film.pd_basis}`;
    if (film.pd_caveat) {
      pdHTML += `<br>${film.pd_caveat}`;
    }
    pdBasis.innerHTML = pdHTML;

    body.append(titleRow, meta, sceneLabel, commentaryRow, pdBasis);
    card.append(clipFrame, body);
    grid.append(card);
  }
}

loadFilms();
