const petForm = document.getElementById("petForm");
const petsTableBody = document.getElementById("petsTableBody");
const petFormReset = document.getElementById("petFormReset");
const petEditModal = document.getElementById("petEditModal");
const closePetModal = document.getElementById("closePetModal");

function toFormData(form) {
  const data = new FormData(form);
  data.set("urgent", form.querySelector('[name="urgent"]').checked ? "true" : "false");
  data.set("adopted", form.querySelector('[name="adopted"]').checked ? "true" : "false");
  return data;
}

async function loadPets() {
  const response = await fetch("/api/pets");
  const pets = await response.json();
  petsTableBody.innerHTML = "";

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
      petsTableBody.appendChild(row);
    });
}

async function populateForm(petId) {
  const response = await fetch("/api/pets");
  const pets = await response.json();
  const pet = pets.find((item) => item.id === petId);
  if (!pet) return;

  petForm.id.value = pet.id;
  petForm.name.value = pet.name;
  petForm.age.value = pet.age;
  petForm.breed.value = pet.breed;
  petForm.personality.value = pet.personality;
  petForm.medical.value = pet.medical;
  petForm.requirements.value = pet.requirements;
  petForm.featured_order.value = pet.featured_order ?? 999;
  petForm.urgent.checked = !!pet.urgent;
  petForm.adopted.checked = !!pet.adopted;
  if (petEditModal) petEditModal.showModal();
}

if (petsTableBody) {
  petsTableBody.addEventListener("click", async (event) => {
    const button = event.target.closest("button");
    if (!button) return;

    const petId = button.dataset.id;
    if (button.dataset.action === "edit") {
      await populateForm(petId);
      return;
    }

    if (button.dataset.action === "delete") {
      const response = await fetch(`/api/pets/${petId}`, { method: "DELETE" });
      if (response.ok) loadPets();
    }
  });
}

if (petForm) {
  petForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!petForm.name.value.trim() || !petForm.breed.value.trim()) return;

    const id = petForm.id.value;
    const method = id ? "PUT" : "POST";
    const url = id ? `/api/pets/${id}` : "/api/pets";

    const data = toFormData(petForm);
    if (id) data.set("replace_photos", "false");

    const response = await fetch(url, {
      method,
      body: data,
    });

    if (response.ok) {
      petForm.reset();
      petForm.id.value = "";
      document.getElementById("petPreview").innerHTML = "";
      loadPets();
    }
  });
}

if (petFormReset) {
  petFormReset.addEventListener("click", () => {
    petForm.reset();
    petForm.id.value = "";
    document.getElementById("petPreview").innerHTML = "";
  });
}

if (closePetModal && petEditModal) {
  closePetModal.addEventListener("click", () => petEditModal.close());
}

if (petForm) loadPets();
