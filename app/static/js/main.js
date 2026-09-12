const menuToggle = document.getElementById("menuToggle");
const siteNav = document.getElementById("siteNav");

if (menuToggle && siteNav) {
  menuToggle.addEventListener("click", () => {
    siteNav.classList.toggle("open");
  });
}

function previewImages(inputId, previewId) {
  const input = document.getElementById(inputId);
  const preview = document.getElementById(previewId);
  if (!input || !preview) return;

  input.addEventListener("change", () => {
    preview.innerHTML = "";
    Array.from(input.files || []).forEach((file) => {
      if (!["image/jpeg", "image/png"].includes(file.type)) return;
      const img = document.createElement("img");
      img.src = URL.createObjectURL(file);
      img.alt = "Preview";
      preview.appendChild(img);
    });
  });
}

previewImages("lostFoundPhotos", "lostFoundPreview");
previewImages("petPhotos", "petPreview");
