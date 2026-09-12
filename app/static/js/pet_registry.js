const petRegistryForm = document.getElementById("petRegistryForm");
const petRegistryTableBody = document.getElementById("petRegistryTableBody");
const petRegistryReset = document.getElementById("petRegistryReset");
const petRegistryPreview = document.getElementById("petRegistryPreview");
const petRegistryStatus = document.getElementById("petRegistryStatus");
const petRegistrySearch = document.getElementById("petRegistrySearch");
const petRegistryVisibilityFilter = document.getElementById("petRegistryVisibilityFilter");
const petRegistryAdoptionFilter = document.getElementById("petRegistryAdoptionFilter");
const petBreedOptions = document.getElementById("petBreedOptions");

let cachedRegistryPets = [];

function initializeBreedOptions() {
  if (!petBreedOptions || !Array.isArray(window.PET_BREEDS)) return;
  petBreedOptions.innerHTML = "";
  window.PET_BREEDS.forEach((breed) => {
    const option = document.createElement("option");
    option.value = breed;
    petBreedOptions.appendChild(option);
  });
}

function ensureBreedOption(value) {
  const breedValue = String(value || "").trim();
  if (!petBreedOptions || !breedValue) return;
  const exists = Array.from(petBreedOptions.options).some((option) => option.value === breedValue);
  if (exists) return;
  const option = document.createElement("option");
  option.value = breedValue;
  petBreedOptions.appendChild(option);
}

function setRegistryStatus(message, type = "success") {
  if (!petRegistryStatus) return;
  petRegistryStatus.textContent = message;
  petRegistryStatus.classList.remove("success", "error");
  if (message) petRegistryStatus.classList.add(type);
}

function toRegistryFormData(form) {
  const data = new FormData(form);
  data.set("urgent", form.querySelector('[name="urgent"]').checked ? "true" : "false");
  data.set("adopted", form.querySelector('[name="adopted"]').checked ? "true" : "false");
  data.set("needs_adoption", form.querySelector('[name="needs_adoption"]').checked ? "true" : "false");
  data.set("is_mixed_breed", form.querySelector('[name="is_mixed_breed"]').checked ? "true" : "false");
  return data;
}

function updateRegistryPreview() {
  if (!petRegistryPreview) return;
  const input = document.getElementById("petRegistryPhotos");
  if (!input) return;

  petRegistryPreview.innerHTML = "";
  Array.from(input.files || []).forEach((file) => {
    if (!["image/jpeg", "image/png"].includes(file.type)) return;
    const img = document.createElement("img");
    img.src = URL.createObjectURL(file);
    img.alt = "Preview";
    petRegistryPreview.appendChild(img);
  });
}

function resetRegistryForm() {
  if (!petRegistryForm) return;
  petRegistryForm.reset();
  petRegistryForm.id.value = "";
  petRegistryForm.gallery_id.value = "";
  petRegistryForm.featured_order.value = "999";
  petRegistryForm.needs_adoption.checked = true;
  petRegistryForm.adopted.checked = false;
  petRegistryForm.urgent.checked = false;
  petRegistryForm.is_mixed_breed.checked = false;
  if (petRegistryPreview) petRegistryPreview.innerHTML = "";
  setRegistryStatus("");
}

async function fetchRegistryPets() {
  const response = await fetch("/api/pets");
  return response.json();
}

function applyRegistryFilters(pets) {
  const searchValue = (petRegistrySearch?.value || "").trim().toLowerCase();
  const visibilityFilter = petRegistryVisibilityFilter?.value || "all";
  const adoptionFilter = petRegistryAdoptionFilter?.value || "all";

  return pets
    .filter((pet) => {
      if (!searchValue) return true;
      const haystack = [pet.gallery_id, pet.name, pet.breed].map((v) => String(v || "").toLowerCase()).join(" ");
      return haystack.includes(searchValue);
    })
    .filter((pet) => {
      if (visibilityFilter === "needs_adoption") return !!pet.needs_adoption;
      if (visibilityFilter === "not_needing_adoption") return !pet.needs_adoption;
      return true;
    })
    .filter((pet) => {
      if (adoptionFilter === "adopted") return !!pet.adopted;
      if (adoptionFilter === "not_adopted") return !pet.adopted;
      return true;
    });
}

function renderRegistryTable(pets) {
  if (!petRegistryTableBody) return;
  petRegistryTableBody.innerHTML = "";

  pets
    .sort((a, b) => (a.featured_order ?? 999) - (b.featured_order ?? 999))
    .forEach((pet) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${pet.gallery_id || ""}</td>
        <td>${pet.name || ""}</td>
        <td>${pet.breed || ""}</td>
        <td>${pet.is_mixed_breed ? "Yes" : "No"}</td>
        <td>${pet.needs_adoption ? "Yes" : "No"}</td>
        <td>${pet.adopted ? "Yes" : "No"}</td>
        <td>${pet.featured_order ?? 999}</td>
        <td>
          <button class="btn btn-small" data-action="edit" data-id="${pet.id}">Edit</button>
          <button class="btn btn-alt btn-small" data-action="delete" data-id="${pet.id}">Delete</button>
        </td>
      `;
      petRegistryTableBody.appendChild(row);
    });

  if (!pets.length) {
    const row = document.createElement("tr");
    row.innerHTML = '<td colspan="8" class="muted">No registry records match the current filters.</td>';
    petRegistryTableBody.appendChild(row);
  }
}

function refreshRegistryTable() {
  const filtered = applyRegistryFilters(cachedRegistryPets);
  renderRegistryTable(filtered);
}

async function loadRegistryTable() {
  cachedRegistryPets = await fetchRegistryPets();
  refreshRegistryTable();
}

async function populateRegistryForm(petId) {
  const pets = await fetchRegistryPets();
  const pet = pets.find((item) => item.id === petId);
  if (!pet || !petRegistryForm) return;

  petRegistryForm.id.value = pet.id || "";
  petRegistryForm.gallery_id.value = pet.gallery_id || "";
  petRegistryForm.name.value = pet.name || "";
  petRegistryForm.age.value = pet.age || "";
  ensureBreedOption(pet.breed);
  petRegistryForm.breed.value = pet.breed || "";
  petRegistryForm.personality.value = pet.personality || "";
  petRegistryForm.medical.value = pet.medical || "";
  petRegistryForm.requirements.value = pet.requirements || "";
  petRegistryForm.featured_order.value = pet.featured_order ?? 999;
  petRegistryForm.needs_adoption.checked = !!pet.needs_adoption;
  petRegistryForm.adopted.checked = !!pet.adopted;
  petRegistryForm.urgent.checked = !!pet.urgent;
  petRegistryForm.is_mixed_breed.checked = !!pet.is_mixed_breed;
  setRegistryStatus(`Loaded ${pet.name} (${pet.gallery_id || "ID pending"}).`, "success");
}

if (petRegistryTableBody) {
  petRegistryTableBody.addEventListener("click", async (event) => {
    const button = event.target.closest("button");
    if (!button) return;

    const petId = button.dataset.id;
    if (button.dataset.action === "edit") {
      await populateRegistryForm(petId);
      return;
    }

    if (button.dataset.action === "delete") {
      const response = await fetch(`/api/pets/${petId}`, { method: "DELETE" });
      if (response.ok) {
        await loadRegistryTable();
        setRegistryStatus("Registry record removed.", "success");
      } else {
        setRegistryStatus("Unable to remove registry record.", "error");
      }
    }
  });
}

if (petRegistryForm) {
  petRegistryForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const id = petRegistryForm.id.value;
    const method = id ? "PUT" : "POST";
    const url = id ? `/api/pets/${id}` : "/api/pets";
    const data = toRegistryFormData(petRegistryForm);

    if (id) data.set("replace_photos", "false");

    const response = await fetch(url, {
      method,
      body: data,
    });

    if (response.ok) {
      const saved = await response.json();
      await loadRegistryTable();
      setRegistryStatus(`Saved ${saved.name || "pet"} with ID ${saved.gallery_id || "pending"}.`, "success");

      await populateRegistryForm(saved.id || id);
      return;
    }

    let errorMessage = "Unable to save registry record.";
    try {
      const payload = await response.json();
      if (payload && payload.error) errorMessage = payload.error;
    } catch (error) {
      // Keep default message.
    }
    setRegistryStatus(errorMessage, "error");
  });
}

if (petRegistryReset) {
  petRegistryReset.addEventListener("click", resetRegistryForm);
}

const petRegistryPhotos = document.getElementById("petRegistryPhotos");
if (petRegistryPhotos) {
  petRegistryPhotos.addEventListener("change", updateRegistryPreview);
}

if (petRegistrySearch) {
  petRegistrySearch.addEventListener("input", refreshRegistryTable);
}

if (petRegistryVisibilityFilter) {
  petRegistryVisibilityFilter.addEventListener("change", refreshRegistryTable);
}

if (petRegistryAdoptionFilter) {
  petRegistryAdoptionFilter.addEventListener("change", refreshRegistryTable);
}

initializeBreedOptions();

if (petRegistryTableBody) loadRegistryTable();
