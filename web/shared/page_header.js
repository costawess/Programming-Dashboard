(function () {
  const pageMeta = {
    "course_topics_lab.html": {
      icon: "../assets/cards/ep_simulations.svg"
    },
    "arduino_flowchart_converter.html": {
      icon: "../assets/cards/arduino_flowchart.svg"
    }
  };

  function getBaseName() {
    const parts = window.location.pathname.split("/");
    return parts[parts.length - 1] || "";
  }

  function getIconPath(baseName) {
    if (pageMeta[baseName]?.icon) return pageMeta[baseName].icon;
    return `../assets/cards/${baseName.replace(/\.html$/i, ".svg")}`;
  }

  function injectStyles() {
    if (document.getElementById("pageHeaderEnhancerStyles")) return;
    const style = document.createElement("style");
    style.id = "pageHeaderEnhancerStyles";
    style.textContent = `
      .header.ep-page-header {
        grid-template-columns: minmax(0, 1fr) auto;
      }
      .header.ep-page-header .title {
        min-width: 0;
      }
      .header.ep-page-header .back {
        justify-self: end;
      }
      .ep-page-title-wrap {
        display: grid;
        grid-template-columns: 72px minmax(0, 1fr);
        gap: 16px;
        align-items: center;
      }
      .ep-page-title-icon {
        width: 72px;
        height: 72px;
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        background: rgba(255, 255, 255, 0.04);
        object-fit: cover;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.22);
      }
      .ep-page-title-copy {
        min-width: 0;
        display: grid;
        gap: 4px;
      }
      .ep-page-title-copy h1,
      .ep-page-title-copy p {
        margin: 0;
      }
      @media (max-width: 760px) {
        .ep-page-title-wrap {
          grid-template-columns: 56px minmax(0, 1fr);
          gap: 12px;
          align-items: start;
        }
        .ep-page-title-icon {
          width: 56px;
          height: 56px;
          border-radius: 14px;
        }
      }
    `;
    document.head.appendChild(style);
  }

  function enhanceHeader() {
    const header = document.querySelector(".header");
    const titleHost = header ? header.querySelector(".title") : null;
    if (!titleHost || titleHost.dataset.headerEnhanced === "true") return;

    const backLink = header.querySelector(".back");
    const brandLogo = header.querySelector(".brand-logo");
    if (brandLogo) {
      brandLogo.remove();
    }
    if (backLink) {
      header.insertBefore(titleHost, header.firstChild);
      header.appendChild(backLink);
      header.classList.add("ep-page-header");
    }

    const baseName = getBaseName();
    const meta = pageMeta[baseName] || {};
    const h1 = titleHost.querySelector("h1");
    const p = titleHost.querySelector("p");
    if (!h1) return;

    const titleText = meta.title || h1.textContent.trim();
    const descriptionText = meta.description || (p ? p.textContent.trim() : "");
    const iconPath = getIconPath(baseName);

    titleHost.innerHTML = "";

    const wrap = document.createElement("div");
    wrap.className = "ep-page-title-wrap";

    const icon = document.createElement("img");
    icon.className = "ep-page-title-icon";
    icon.src = iconPath;
    icon.alt = `${titleText} icon`;

    const copy = document.createElement("div");
    copy.className = "ep-page-title-copy";

    const newH1 = document.createElement("h1");
    newH1.textContent = titleText;
    copy.appendChild(newH1);

    if (descriptionText) {
      const newP = document.createElement("p");
      newP.textContent = descriptionText;
      copy.appendChild(newP);
    }

    wrap.appendChild(icon);
    wrap.appendChild(copy);
    titleHost.appendChild(wrap);
    titleHost.dataset.headerEnhanced = "true";
  }

  function boot() {
    injectStyles();
    enhanceHeader();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
