async function loadFilms() {
  const res = await fetch("data/films.json");
  const data = await res.json();
  document.getElementById("tagline").textContent = data.site.tagline;
  renderGrid(data.films);
}

// Only one film's audio plays at a time -- unmuting a clip mutes every
// other clip. Narration is different: most of these are silent films with
// just an orchestral score, so the narrator can read right over that score
// like a documentary voiceover. Listen ducks its own card's clip to a low
// volume instead of silencing it, and only cancels a narration running on
// a *different* card (still only one voice at a time).
function muteOtherVideos(exceptVideo) {
  document.querySelectorAll("video").forEach((v) => {
    if (v !== exceptVideo) v.muted = true;
  });
}

// Cancels whatever narration is running, unless it's exceptBtn's own.
function stopNarrationExcept(exceptBtn) {
  const activeBtn = document.querySelector(".narrate-btn.narrating");
  if (activeBtn && activeBtn !== exceptBtn) {
    window.speechSynthesis.cancel();
    activeBtn.classList.remove("narrating");
    activeBtn.textContent = "🔊 Listen";
  }
}

const CLIP_DUCK_VOLUME = 0.22;

// The reaction-cam's expression follows whichever card you're hovering.
function moodForGenre(genre) {
  const g = genre.toLowerCase();
  if (g.includes("horror") || g.includes("psychological")) return "scared";
  if (g.includes("comedy")) return "laughing";
  if (g.includes("science")) return "amazed";
  return "neutral";
}

function setReactionMood(mood) {
  const cam = document.querySelector(".reaction-cam");
  if (cam) cam.dataset.mood = mood;
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
    const mood = moodForGenre(film.genre);
    card.addEventListener("mouseenter", () => {
      video.play().catch(() => {});
      setReactionMood(mood);
    });
    card.addEventListener("mouseleave", () => {
      const ownNarrationPlaying = narrateBtn && narrateBtn.classList.contains("narrating");
      if (!ownNarrationPlaying) video.pause();
      setReactionMood("neutral");
    });

    // Declared now, assigned once the narrate button exists below --
    // toggleSound needs to know if *this* card's own narration is playing.
    let narrateBtn = null;

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
        const ownNarrationPlaying = narrateBtn && narrateBtn.classList.contains("narrating");
        stopNarrationExcept(ownNarrationPlaying ? narrateBtn : null);
        muteOtherVideos(video);
        video.muted = false;
        video.volume = ownNarrationPlaying ? CLIP_DUCK_VOLUME : 1;
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
      narrateBtn = document.createElement("button");
      narrateBtn.type = "button";
      narrateBtn.className = "narrate-btn";
      narrateBtn.textContent = "🔊 Listen";
      narrateBtn.setAttribute("aria-label", `Listen to the commentary for ${film.title}, read over the clip`);
      narrateBtn.addEventListener("click", () => {
        if (narrateBtn.classList.contains("narrating")) {
          window.speechSynthesis.cancel();
          narrateBtn.classList.remove("narrating");
          narrateBtn.textContent = "🔊 Listen";
          video.volume = 1;
          return;
        }

        stopNarrationExcept(null); // only one narration plays at a time
        muteOtherVideos(video); // ...and only one film's audio at a time
        video.muted = false;
        video.volume = CLIP_DUCK_VOLUME; // ducked so the narrator reads clearly over the score
        video.play().catch(() => {});

        const utterance = new SpeechSynthesisUtterance(film.commentary);
        utterance.rate = 0.95;
        narrateBtn.classList.add("narrating");
        narrateBtn.textContent = "⏸ Reading…";
        utterance.onend = utterance.onerror = () => {
          narrateBtn.classList.remove("narrating");
          narrateBtn.textContent = "🔊 Listen";
          video.volume = 1;
        };
        window.speechSynthesis.speak(utterance);
      });
      commentaryRow.append(narrateBtn);
    }

    const pdBadge = document.createElement("a");
    pdBadge.className = "pd-badge";
    pdBadge.href = `about.html#${film.id}`;
    pdBadge.textContent = "© Public Domain";
    pdBadge.title = film.pd_caveat ? `${film.pd_basis} ${film.pd_caveat}` : film.pd_basis;

    body.append(titleRow, meta, sceneLabel, commentaryRow, pdBadge);
    card.append(clipFrame, body);
    grid.append(card);
  }
}

loadFilms();
