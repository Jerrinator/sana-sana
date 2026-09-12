const contentForm = document.getElementById("contentForm");
const contentModal = document.getElementById("contentModal");
const closeContentModal = document.getElementById("closeContentModal");
const tipForm = document.getElementById("tipForm");
const tipsTableBody = document.getElementById("tipsTableBody");
const tipReset = document.getElementById("tipReset");

async function loadContent() {
  if (!contentForm) return;
  const response = await fetch("/api/content");
  const content = await response.json();

  contentForm.hero_text.value = content.hero_text || "";
  contentForm.mission_snapshot.value = content.mission_snapshot || "";
  contentForm.banner_image.value = content.banner_image || "";
  contentForm.about_text_blocks.value = (content.about_text_blocks || []).join("\n");
  contentForm.footer_text.value = content.footer_text || "";
  contentForm.lostfound_preview_enabled.checked = !!content.lostfound_preview_enabled;

  const contact = content.contact_info || {};
  const social = contact.social || {};

  contentForm.contact_email.value = contact.email || "";
  contentForm.contact_phone.value = contact.phone || "";
  contentForm.contact_address.value = contact.address || "";
  contentForm.social_facebook.value = social.facebook || "";
  contentForm.social_instagram.value = social.instagram || "";
}

async function saveContent(event) {
  event.preventDefault();
  const payload = {
    hero_text: contentForm.hero_text.value.trim(),
    mission_snapshot: contentForm.mission_snapshot.value.trim(),
    banner_image: contentForm.banner_image.value.trim(),
    about_text_blocks: contentForm.about_text_blocks.value
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean),
    footer_text: contentForm.footer_text.value.trim(),
    lostfound_preview_enabled: contentForm.lostfound_preview_enabled.checked,
    contact_info: {
      email: contentForm.contact_email.value.trim(),
      phone: contentForm.contact_phone.value.trim(),
      address: contentForm.contact_address.value.trim(),
      social: {
        facebook: contentForm.social_facebook.value.trim(),
        instagram: contentForm.social_instagram.value.trim(),
      },
    },
  };

  const response = await fetch("/api/content", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (response.ok && contentModal) {
    contentModal.showModal();
  }
}

async function loadTips() {
  const response = await fetch("/api/tips");
  const tips = await response.json();
  tipsTableBody.innerHTML = "";

  tips.forEach((tip) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${tip.title}</td>
      <td>${tip.category}</td>
      <td>
        <button class="btn btn-small" data-action="edit" data-id="${tip.id}">Edit</button>
        <button class="btn btn-alt btn-small" data-action="delete" data-id="${tip.id}">Delete</button>
      </td>
    `;
    tipsTableBody.appendChild(row);
  });

  return tips;
}

async function getTip(tipId) {
  const response = await fetch("/api/tips");
  const tips = await response.json();
  return tips.find((tip) => tip.id === tipId);
}

if (contentForm) {
  contentForm.addEventListener("submit", saveContent);
}

if (closeContentModal && contentModal) {
  closeContentModal.addEventListener("click", () => contentModal.close());
}

if (tipsTableBody) {
  tipsTableBody.addEventListener("click", async (event) => {
    const btn = event.target.closest("button");
    if (!btn) return;

    const id = btn.dataset.id;
    const action = btn.dataset.action;

    if (action === "delete") {
      const response = await fetch(`/api/tips/${id}`, { method: "DELETE" });
      if (response.ok) loadTips();
      return;
    }

    const tip = await getTip(id);
    if (!tip) return;

    tipForm.tip_id.value = tip.id;
    tipForm.title.value = tip.title;
    tipForm.description.value = tip.description;
    tipForm.category.value = tip.category;
  });
}

if (tipForm) {
  tipForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const id = tipForm.tip_id.value;
    const payload = {
      title: tipForm.title.value.trim(),
      description: tipForm.description.value.trim(),
      category: tipForm.category.value.trim(),
    };

    const response = await fetch(id ? `/api/tips/${id}` : "/api/tips", {
      method: id ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      tipForm.reset();
      tipForm.tip_id.value = "";
      loadTips();
    }
  });
}

if (tipReset) {
  tipReset.addEventListener("click", () => {
    tipForm.reset();
    tipForm.tip_id.value = "";
  });
}

if (contentForm) loadContent();
if (tipsTableBody) loadTips();
