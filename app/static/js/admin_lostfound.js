const lostFoundTableBody = document.getElementById("lostFoundTableBody");
const lostFoundModal = document.getElementById("lostFoundModal");
const lostFoundModalForm = document.getElementById("lostFoundModalForm");
const saveLostFoundEdit = document.getElementById("saveLostFoundEdit");
const closeLostFoundModal = document.getElementById("closeLostFoundModal");
const toggleLostFoundPreview = document.getElementById("toggleLostFoundPreview");
const saveLostFoundPreviewSetting = document.getElementById("saveLostFoundPreviewSetting");

async function loadLostFoundAdmin() {
  const response = await fetch("/api/lostfound?approved_only=false");
  const posts = await response.json();
  lostFoundTableBody.innerHTML = "";

  posts.forEach((post) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${post.poster_name}</td>
      <td>${post.location}</td>
      <td>${post.date}</td>
      <td>${post.approved ? "Yes" : "No"}</td>
      <td>
        <button class="btn btn-small" data-action="edit" data-id="${post.id}">Edit</button>
        <button class="btn btn-small" data-action="approve" data-id="${post.id}">${post.approved ? "Unapprove" : "Approve"}</button>
        <button class="btn btn-alt btn-small" data-action="delete" data-id="${post.id}">Remove</button>
      </td>
    `;
    lostFoundTableBody.appendChild(row);
  });
}

async function getPost(postId) {
  const response = await fetch("/api/lostfound?approved_only=false");
  const posts = await response.json();
  return posts.find((post) => post.id === postId);
}

async function updatePost(postId, payload) {
  return fetch(`/api/lostfound/${postId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

if (lostFoundTableBody) {
  lostFoundTableBody.addEventListener("click", async (event) => {
    const btn = event.target.closest("button");
    if (!btn) return;
    const id = btn.dataset.id;
    const action = btn.dataset.action;

    if (action === "delete") {
      const response = await fetch(`/api/lostfound/${id}`, { method: "DELETE" });
      if (response.ok) loadLostFoundAdmin();
      return;
    }

    const post = await getPost(id);
    if (!post) return;

    if (action === "approve") {
      await updatePost(id, { approved: !post.approved });
      loadLostFoundAdmin();
      return;
    }

    if (action === "edit") {
      document.getElementById("lfId").value = post.id;
      document.getElementById("lfPoster").value = post.poster_name || "";
      document.getElementById("lfContact").value = post.contact || "";
      document.getElementById("lfLocation").value = post.location || "";
      document.getElementById("lfDate").value = post.date || "";
      document.getElementById("lfDescription").value = post.description || "";
      document.getElementById("lfApproved").checked = !!post.approved;
      lostFoundModal.showModal();
    }
  });
}

if (saveLostFoundEdit) {
  saveLostFoundEdit.addEventListener("click", async (event) => {
    event.preventDefault();
    const id = document.getElementById("lfId").value;
    const payload = {
      poster_name: document.getElementById("lfPoster").value.trim(),
      contact: document.getElementById("lfContact").value.trim(),
      location: document.getElementById("lfLocation").value.trim(),
      date: document.getElementById("lfDate").value,
      description: document.getElementById("lfDescription").value.trim(),
      approved: document.getElementById("lfApproved").checked,
    };
    await updatePost(id, payload);
    lostFoundModal.close();
    loadLostFoundAdmin();
  });
}

if (closeLostFoundModal) {
  closeLostFoundModal.addEventListener("click", (event) => {
    event.preventDefault();
    lostFoundModal.close();
  });
}

async function loadLostFoundPreviewSetting() {
  if (!toggleLostFoundPreview) return;
  const response = await fetch("/api/content");
  if (!response.ok) return;
  const content = await response.json();
  toggleLostFoundPreview.checked = !!content.lostfound_preview_enabled;
}

if (saveLostFoundPreviewSetting) {
  saveLostFoundPreviewSetting.addEventListener("click", async () => {
    const currentRes = await fetch("/api/content");
    if (!currentRes.ok) return;
    const current = await currentRes.json();

    const payload = {
      hero_text: current.hero_text,
      mission_snapshot: current.mission_snapshot,
      about_text_blocks: current.about_text_blocks || [],
      footer_text: current.footer_text,
      contact_info: current.contact_info || {},
      lostfound_preview_enabled: !!toggleLostFoundPreview.checked,
    };

    await fetch("/api/content", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  });
}

if (lostFoundTableBody) loadLostFoundAdmin();
loadLostFoundPreviewSetting();
