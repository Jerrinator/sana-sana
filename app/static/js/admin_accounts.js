const adminAccountForm = document.getElementById("adminAccountForm");
const adminAccountsTableBody = document.getElementById("adminAccountsTableBody");
const adminAccountReset = document.getElementById("adminAccountReset");
const adminAccountModal = document.getElementById("adminAccountModal");
const closeAdminAccountModal = document.getElementById("closeAdminAccountModal");

async function loadAdminAccounts() {
  if (!adminAccountsTableBody) return;
  const response = await fetch("/api/admin-accounts");
  const accounts = await response.json();
  adminAccountsTableBody.innerHTML = "";

  accounts.forEach((account) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${account.first_name || ""} ${account.last_name || ""}</td>
      <td>${account.email || ""}</td>
      <td>${account.role || ""}</td>
      <td>${account.permission_level || ""}</td>
      <td>${account.is_active ? "Yes" : "No"}</td>
      <td>${account.must_change_password ? "Yes" : "No"}</td>
      <td>
        <button class="btn btn-small" data-action="edit" data-id="${account.id}">Edit</button>
        <button class="btn btn-small" data-action="reset" data-id="${account.id}">Reset PW</button>
        <button class="btn btn-alt btn-small" data-action="delete" data-id="${account.id}">Delete</button>
      </td>
    `;
    adminAccountsTableBody.appendChild(row);
  });
}

async function getAdminAccount(adminId) {
  const response = await fetch("/api/admin-accounts");
  const accounts = await response.json();
  return accounts.find((account) => account.id === adminId);
}

function resetForm() {
  adminAccountForm.reset();
  adminAccountForm.id.value = "";
  adminAccountForm.role.value = "admin";
  adminAccountForm.permission_level.value = "full";
  adminAccountForm.is_active.checked = true;
  adminAccountForm.must_change_password.checked = true;
  adminAccountForm.email.value = "";
}

if (adminAccountsTableBody) {
  adminAccountsTableBody.addEventListener("click", async (event) => {
    const button = event.target.closest("button");
    if (!button) return;

    const adminId = button.dataset.id;
    const action = button.dataset.action;

    if (action === "delete") {
      const response = await fetch(`/api/admin-accounts/${adminId}`, { method: "DELETE" });
      if (response.ok) loadAdminAccounts();
      return;
    }

    if (action === "reset") {
      const account = await getAdminAccount(adminId);
      if (!account) return;

      const response = await fetch(`/api/admin-accounts/${adminId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: account.email,
          first_name: account.first_name || "",
          last_name: account.last_name || "",
          role: account.role || "admin",
          permission_level: account.permission_level || "full",
          is_active: !!account.is_active,
          must_change_password: true,
        }),
      });

      if (response.ok) loadAdminAccounts();
      return;
    }

    if (action === "edit") {
      const account = await getAdminAccount(adminId);
      if (!account) return;
      adminAccountForm.id.value = account.id || "";
      adminAccountForm.first_name.value = account.first_name || "";
      adminAccountForm.last_name.value = account.last_name || "";
      adminAccountForm.email.value = account.email || "";
      adminAccountForm.role.value = account.role || "admin";
      adminAccountForm.permission_level.value = account.permission_level || "full";
      adminAccountForm.is_active.checked = !!account.is_active;
      adminAccountForm.must_change_password.checked = !!account.must_change_password;
      return;
    }
  });
}

if (adminAccountForm) {
  adminAccountForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const id = adminAccountForm.id.value;
    const payload = {
      first_name: adminAccountForm.first_name.value.trim(),
      last_name: adminAccountForm.last_name.value.trim(),
      email: adminAccountForm.email.value.trim(),
      role: adminAccountForm.role.value.trim(),
      permission_level: adminAccountForm.permission_level.value,
      is_active: adminAccountForm.is_active.checked,
      must_change_password: adminAccountForm.must_change_password.checked,
    };

    const response = await fetch(id ? `/api/admin-accounts/${id}` : "/api/admin-accounts", {
      method: id ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      if (adminAccountModal) adminAccountModal.showModal();
      resetForm();
      loadAdminAccounts();
    }
  });
}

if (adminAccountReset) {
  adminAccountReset.addEventListener("click", resetForm);
}

if (closeAdminAccountModal && adminAccountModal) {
  closeAdminAccountModal.addEventListener("click", () => adminAccountModal.close());
}

if (adminAccountsTableBody) loadAdminAccounts();