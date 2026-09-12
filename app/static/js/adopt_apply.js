const adoptApplicationForm = document.getElementById("adoptApplicationForm");

if (adoptApplicationForm) {
  adoptApplicationForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = document.getElementById("adoptApplicationMsg");
    const data = new FormData(adoptApplicationForm);

    if (!data.get("pet_id")) {
      message.textContent = "Please select a pet from the adopt page first.";
      return;
    }

    const requiredFields = ["applicant_name", "email", "phone", "city_state", "household", "pet_experience"];
    const missing = requiredFields.some((field) => !String(data.get(field) || "").trim());
    if (missing) {
      message.textContent = "Please complete all required fields.";
      return;
    }

    const payload = Object.fromEntries(data.entries());
    const response = await fetch("/api/adoption-applications", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      message.textContent = `Application sent for ${data.get("pet_name")}. BHLR admins have been notified by email.`;
      ["applicant_name", "email", "phone", "city_state", "household", "pet_experience", "notes"].forEach((name) => {
        const field = adoptApplicationForm.querySelector(`[name="${name}"]`);
        if (field) field.value = "";
      });
      return;
    }

    let errorMessage = "Unable to send application right now.";
    try {
      const errorPayload = await response.json();
      if (errorPayload && errorPayload.error) errorMessage = errorPayload.error;
    } catch (error) {
      // Keep default fallback message.
    }
    message.textContent = errorMessage;
  });
}
