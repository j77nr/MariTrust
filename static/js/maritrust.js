document.addEventListener("click", (event) => {
  const target = event.target instanceof Element ? event.target : null;
  const toggle = target?.closest("[data-password-toggle]");
  if (!toggle) return;

  const input = document.getElementById(toggle.dataset.target);
  if (!input) return;

  const visible = input.type === "password";
  input.type = visible ? "text" : "password";
  toggle.setAttribute("aria-pressed", String(visible));
  toggle.setAttribute(
    "aria-label",
    visible ? "Masquer le mot de passe" : "Afficher le mot de passe",
  );
  const icon = toggle.querySelector("i");
  if (icon) icon.className = visible ? "bi bi-eye-slash" : "bi bi-eye";
});

document.addEventListener("input", (event) => {
  const search = event.target;
  if (!(search instanceof HTMLInputElement) || !search.matches("[data-agent-search]")) {
    return;
  }

  const query = search.value.trim().toLocaleLowerCase("fr");
  let visibleRows = 0;
  document.querySelectorAll("[data-agent-row]").forEach((row) => {
    const matches = row.dataset.searchText.toLocaleLowerCase("fr").includes(query);
    row.hidden = !matches;
    if (matches) visibleRows += 1;
  });

  const emptyMessage = document.querySelector("[data-agent-no-results]");
  if (emptyMessage) emptyMessage.classList.toggle("d-none", visibleRows !== 0);
});
