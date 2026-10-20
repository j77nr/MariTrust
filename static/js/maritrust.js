document.addEventListener("click", (event) => {
  const toggle = event.target.closest("[data-password-toggle]");
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
  toggle.querySelector("i").className = visible ? "bi bi-eye-slash" : "bi bi-eye";
});
