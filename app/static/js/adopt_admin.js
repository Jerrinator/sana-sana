const adoptAdminForm = document.getElementById("adoptAdminForm");
const adoptAdminTableBody = document.getElementById("adoptAdminTableBody");
const adoptAdminReset = document.getElementById("adoptAdminReset");
const adoptAdminPreview = document.getElementById("adoptAdminPreview");
const adoptAdminStatus = document.getElementById("adoptAdminStatus");

function setStatus(message, type = "success") {
  if (!adoptAdminStatus) return;
  adoptAdminStatus.textContent = message;
  adoptAdminStatus.classList.remove("success", "error");
  adoptAdminStatus.classList.add(type);
}

function toAdminFormData(form) {
  const data = new FormData(form);
  data.set("urgent", form.querySelector('[name="urgent"]').checked ? "true" : "false");
  data.set("adopted", form.querySelector('[name="adopted"]').checked ? "true" : "false");
  return data;
}

function updateImagePreview() {
  const input = document.getElementById("adoptAdminPhotos");
  if (!input || !adoptAdminPreview) return;

  adoptAdminPreview.innerHTML = "";
  Array.from(input.files || []).forEach((file) => {
    if (!["image/jpeg", "image/png"].includes(file.type)) return;
    const img = document.createElement("img");
    img.src = URL.createObjectURL(file);
    img.alt = "Preview";
    adoptAdminPreview.appendChild(img);
  });
}

function resetAdminForm() {
  if (!adoptAdminForm) return;
  adoptAdminForm.reset();
  adoptAdminForm.id.value = "";
  adoptAdminForm.featured_order.value = "999";
  adoptAdminForm.urgent.checked = false;
  adoptAdminForm.adopted.checked = false;
  if (adoptAdminPreview) adoptAdminPreview.innerHTML = "";
  setStatus("");
}

async function fetchAllPets() {
  const response = await fetch("/api/pets");
  return response.json();
}

async function loadAdminTable() {
  if (!adoptAdminTableBody) return;
  const pets = await fetchAllPets();
  adoptAdminTableBody.innerHTML = "";

  pets
    .sort((a, b) => (a.featured_order ?? 999) - (b.featured_order ?? 999))
    .forEach((pet) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${pet.name}</td>
        <td>${pet.breed}</td>
        <td>${pet.urgent ? "Yes" : "No"}</td>
        <td>${pet.adopted ? "Yes" : "No"}</td>
        <td>${pet.featured_order ?? 999}</td>
        <td>
          <button class="btn btn-small" data-action="edit" data-id="${pet.id}">Edit</button>
          <button class="btn btn-alt btn-small" data-action="delete" data-id="${pet.id}">Delete</button>
        </td>
      `;
      adoptAdminTableBody.appendChild(row);
    });
}

async function populateAdminForm(petId) {
  const pets = await fetchAllPets();
  const pet = pets.find((item) => item.id === petId);
  if (!pet || !adoptAdminForm) return;

  adoptAdminForm.id.value = pet.id;
  adoptAdminForm.name.value = pet.name || "";
  adoptAdminForm.age.value = pet.age || "";
  adoptAdminForm.breed.value = pet.breed || "";
  adoptAdminForm.personality.value = pet.personality || "";
  adoptAdminForm.medical.value = pet.medical || "";
  adoptAdminForm.requirements.value = pet.requirements || "";
  adoptAdminForm.featured_order.value = pet.featured_order ?? 999;
  adoptAdminForm.urgent.checked = !!pet.urgent;
  adoptAdminForm.adopted.checked = !!pet.adopted;
}

if (adoptAdminTableBody) {
  adoptAdminTableBody.addEventListener("click", async (event) => {
    const button = event.target.closest("button");
    if (!button) return;

    const petId = button.dataset.id;
    if (button.dataset.action === "edit") {
      await populateAdminForm(petId);
      return;
    }

    if (button.dataset.action === "delete") {
      const response = await fetch(`/api/pets/${petId}`, { method: "DELETE" });
      if (response.ok) {
        await loadAdminTable();
        if (typeof renderAdoptGrid === "function") renderAdoptGrid();
        setStatus("Gallery item removed.", "success");
      } else {
        setStatus("Unable to remove gallery item.", "error");
      }
    }
  });
}

if (adoptAdminForm) {
  adoptAdminForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const id = adoptAdminForm.id.value;
    const method = id ? "PUT" : "POST";
    const url = id ? `/api/pets/${id}` : "/api/pets";
    const data = toAdminFormData(adoptAdminForm);

    if (id) data.set("replace_photos", "false");

    const response = await fetch(url, {
      method,
      body: data,
    });

    if (response.ok) {
      resetAdminForm();
      await loadAdminTable();
      if (typeof renderAdoptGrid === "function") renderAdoptGrid();
      setStatus(id ? "Gallery item updated." : "Gallery item created.", "success");
    } else {
      let message = "Unable to save gallery item.";
      try {
        const payload = await response.json();
        if (payload && payload.error) message = payload.error;
      } catch (error) {
        // Keep generic message if response is not JSON.
      }
      setStatus(message, "error");
    }
  });
}

if (adoptAdminReset) {
  adoptAdminReset.addEventListener("click", resetAdminForm);
}

const adoptAdminPhotos = document.getElementById("adoptAdminPhotos");
if (adoptAdminPhotos) {
  adoptAdminPhotos.addEventListener("change", updateImagePreview);
}

if (adoptAdminTableBody) loadAdminTable();
