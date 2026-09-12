const contactForm = document.getElementById("contactForm");

if (contactForm) {
  contactForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = document.getElementById("contactMsg");
    const data = new FormData(contactForm);

    if (!data.get("name") || !data.get("email") || !data.get("message")) {
      message.textContent = "Please fill out required fields.";
      return;
    }

    const payload = Object.fromEntries(data.entries());
    const response = await fetch("/api/contact-messages", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      message.textContent = "Message sent. BHLR admins have been notified by email.";
      contactForm.reset();
      return;
    }

    let errorMessage = "Unable to send message right now.";
    try {
      const errorPayload = await response.json();
      if (errorPayload && errorPayload.error) errorMessage = errorPayload.error;
    } catch (error) {
      // Keep default fallback message.
    }
    message.textContent = errorMessage;
  });
}
