(function () {
  const currentPath = (window.location.pathname.split("/").pop() || "index.html").toLowerCase();

  document.querySelectorAll(".site-nav a").forEach(link => {
    const href = link.getAttribute("href");
    if (!href) return;
    const target = href.replace("./", "").toLowerCase();
    if (target === currentPath) link.classList.add("is-active");
  });

  document.querySelectorAll("[data-current-year]").forEach(node => {
    node.textContent = String(new Date().getFullYear());
  });
})();
