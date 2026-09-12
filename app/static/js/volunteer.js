const volunteerForm = document.getElementById("volunteerForm");
const fosterRulesBtn = document.getElementById("fosterRulesBtn");
const fosterRulesModal = document.getElementById("fosterRulesModal");
const closeFosterRulesModal = document.getElementById("closeFosterRulesModal");

if (fosterRulesBtn && fosterRulesModal) {
  fosterRulesBtn.addEventListener("click", () => {
    fosterRulesModal.showModal();
  });
}

if (closeFosterRulesModal && fosterRulesModal) {
  closeFosterRulesModal.addEventListener("click", () => {
    fosterRulesModal.close();
  });
}

if (fosterRulesModal) {
  fosterRulesModal.addEventListener("keydown", (event) => {
    event.preventDefault();
    fosterRulesModal.close();
  });
}

if (volunteerForm) {
  volunteerForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const message = document.getElementById("volunteerMsg");
    const data = new FormData(volunteerForm);

    if (!data.get("name") || !data.get("email") || !data.get("interest")) {
      message.textContent = "Please fill all required fields.";
      return;
    }

    message.textContent = "Application received. We will follow up by email.";
    volunteerForm.reset();
  });
}
