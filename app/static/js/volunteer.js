const volunteerForm = document.getElementById("volunteerForm");
const oneClickForm = document.getElementById("oneClickForm");
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

if (oneClickForm) {
  oneClickForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = document.getElementById("oneClickMsg");
    const data = new FormData(oneClickForm);

    message.textContent = "Processing 1-click sign-up...";

    try {
      const response = await fetch("/api/pilates/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: data.get("name"),
          email: data.get("email"),
          phone: data.get("phone"),
          interest: data.get("interest"),
          notes: "1-Click Customer Loyalty Member Sign-Up"
        })
      });

      const result = await response.json();
      if (response.ok && result.success) {
        message.textContent = "✨ 1-Click Sign-Up Complete! You're added to the Reformer Pilates Roster.";
        message.style.color = "var(--sana-forest)";
      } else {
        message.textContent = result.error || "Unable to complete sign-up. Please try again.";
        message.style.color = "var(--sana-clay)";
      }
    } catch (err) {
      message.textContent = "Sign-up request sent. We will follow up with you shortly.";
    }
  });
}

if (volunteerForm) {
  volunteerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = document.getElementById("volunteerMsg");
    const data = new FormData(volunteerForm);

    if (!data.get("name") || !data.get("email") || !data.get("phone") || !data.get("interest")) {
      message.textContent = "Please fill out all required fields.";
      return;
    }

    message.textContent = "Submitting sign-up request...";

    try {
      const response = await fetch("/api/pilates/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: data.get("name"),
          email: data.get("email"),
          phone: data.get("phone"),
          interest: data.get("interest"),
          notes: data.get("notes") || ""
        })
      });

      const result = await response.json();
      if (response.ok && result.success) {
        message.textContent = "✨ Welcome to the Reformer Pilates Roster! You're signed up.";
        message.style.color = "var(--sana-forest)";
        volunteerForm.reset();
      } else {
        message.textContent = result.error || "Unable to submit sign-up. Please try again.";
        message.style.color = "var(--sana-clay)";
      }
    } catch (err) {
      message.textContent = "Sign-up request sent. We will follow up with you shortly.";
      volunteerForm.reset();
    }
  });
}
