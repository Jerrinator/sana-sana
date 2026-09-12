const lostFoundForm = document.getElementById("lostFoundForm");

async function refreshLostFoundFeed() {
  const feed = document.getElementById("lostFoundFeed");
  if (!feed) return;
  const response = await fetch("/api/lostfound?approved_only=true");
  const posts = await response.json();

  feed.innerHTML = "";
  if (!posts.length) {
    feed.innerHTML = "<p>No approved posts yet.</p>";
    return;
  }

  posts.forEach((post) => {
    const article = document.createElement("article");
    article.className = "card";
    article.innerHTML = `
      <h3>${post.location}</h3>
      <p>${post.description}</p>
      <p class="muted">Posted by ${post.poster_name} | ${post.date}</p>
    `;
    feed.appendChild(article);
  });
}

if (lostFoundForm) {
  lostFoundForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = document.getElementById("lostFoundMessage");
    const data = new FormData(lostFoundForm);

    if (!data.get("poster_name") || !data.get("contact") || !data.get("description")) {
      message.textContent = "Please complete all required fields.";
      return;
    }

    const response = await fetch("/api/lostfound", {
      method: "POST",
      body: data,
    });

    if (response.ok) {
      message.textContent = "Submitted for moderation.";
      lostFoundForm.reset();
      const preview = document.getElementById("lostFoundPreview");
      if (preview) preview.innerHTML = "";
    } else {
      message.textContent = "Unable to submit right now.";
    }
  });

  refreshLostFoundFeed();
}
