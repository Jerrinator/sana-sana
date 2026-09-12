const adoptGrid = document.getElementById("adoptGrid");

function resolvePhotoSrc(photo) {
  if (!photo) return "";
  if (photo.startsWith("http://") || photo.startsWith("https://") || photo.startsWith("data:")) {
    return photo;
  }
  return `/static/uploads/${photo}`;
}

function petCard(pet) {
  const imageSrc = resolvePhotoSrc((pet.photos || [])[0]);
  const image = imageSrc
    ? `<img src="${imageSrc}" alt="${pet.name}" class="card-image" loading="lazy" onerror="this.onerror=null;this.src='/static/images/pet-placeholder.svg';" />`
    : "";
  const breedLabel = pet.is_mixed_breed
    ? `Mixed (${pet.breed || "Dominant breed not provided"})`
    : (pet.breed || "Not provided");
  const urgent = pet.urgent ? '<span class="pill urgent">Urgent</span>' : "";
  return `
    <article class="card">
      ${image}
      <h3>${pet.name}</h3>
      <p><strong>Breed:</strong> ${breedLabel}</p>
      <p><strong>Age:</strong> ${pet.age || "Not provided"}</p>
      <p><strong>Personality:</strong> ${pet.personality || "Not provided"}</p>
      <p><strong>Medical:</strong> ${pet.medical || "Not provided"}</p>
      <p><strong>Requirements:</strong> ${pet.requirements || "Not provided"}</p>
      ${urgent}
      <a class="btn btn-small" href="/adopt/apply?pet_id=${pet.id}">Apply To Adopt This Pet</a>
    </article>
  `;
}

async function renderAdoptGrid() {
  if (!adoptGrid) return;
  const url = new URL(window.location.href);
  const breedFilter = (url.searchParams.get("breed") || "").toLowerCase().trim();
  const urgentOnly = (url.searchParams.get("urgent") || "").toLowerCase() === "true";

  const response = await fetch("/api/pets?include_adopted=false");
  const pets = await response.json();

  const filtered = pets
    .filter((pet) => !breedFilter || (pet.breed || "").toLowerCase().includes(breedFilter))
    .filter((pet) => !urgentOnly || pet.urgent)
    .sort((a, b) => (a.featured_order ?? 999) - (b.featured_order ?? 999));

  adoptGrid.innerHTML = filtered.length ? filtered.map((pet) => petCard(pet)).join("") : "<p>No pets available at this time.</p>";
}

renderAdoptGrid();
