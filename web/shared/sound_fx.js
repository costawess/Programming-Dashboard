(function () {
  const STORAGE_KEY = "embedded-sound-muted";

  class UiSoundManager {
    constructor() {
      this.muted = localStorage.getItem(STORAGE_KEY) === "true";
      this.audioContext = null;
      this.masterGain = null;
      this.lastPlayAt = 0;
    }

    init() {
      this.injectStyles();
      this.installHeaderToggles();
      this.installGlobalListeners();
      this.syncToggleLabels();
    }

    injectStyles() {
      if (document.getElementById("embedded-sound-style")) return;
      const style = document.createElement("style");
      style.id = "embedded-sound-style";
      style.textContent = `
        .header-tools {
          display: flex;
          align-items: center;
          justify-content: flex-end;
          gap: 12px;
          min-width: 0;
        }
        .sound-toggle {
          appearance: none;
          border: 2px solid rgba(125, 163, 182, 0.45);
          border-radius: 999px;
          padding: 10px 14px;
          background: rgba(12, 24, 34, 0.84);
          color: #e8f6ff;
          font: 700 14px "Segoe UI", Arial, sans-serif;
          cursor: pointer;
          white-space: nowrap;
        }
        .sound-toggle.muted {
          color: #9db9c8;
          opacity: 0.85;
        }
      `;
      document.head.appendChild(style);
    }

    installHeaderToggles() {
      document.querySelectorAll(".brand-logo").forEach((logo, index) => {
        if (logo.parentElement && logo.parentElement.classList.contains("header-tools")) return;

        const wrapper = document.createElement("div");
        wrapper.className = "header-tools";

        const button = document.createElement("button");
        button.type = "button";
        button.className = "sound-toggle";
        button.dataset.soundToggle = "true";
        button.dataset.soundToggleId = String(index);
        button.addEventListener("click", event => {
          event.preventDefault();
          this.toggleMuted();
        });

        logo.parentNode.insertBefore(wrapper, logo);
        wrapper.appendChild(button);
        wrapper.appendChild(logo);
      });
    }

    installGlobalListeners() {
      document.addEventListener("click", event => {
        const target = event.target.closest("button, .launch-button, .back, .back-button, a[href]");
        if (!target) return;
        if (target.matches("[data-sound-toggle]")) {
          this.play("toggle");
          return;
        }
        if (target.matches(".launch-button, .back, .back-button, a[href]")) this.play("navigate");
        else this.play("click");
      }, true);

      document.addEventListener("change", event => {
        if (event.target.matches("select, input[type='range'], input[type='checkbox']")) this.play("tick");
      }, true);

      window.addEventListener("keydown", event => {
        const tag = document.activeElement?.tagName || "";
        if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || event.repeat) return;
        if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", " ", "Enter"].includes(event.key)) this.play("tick");
      });
    }

    syncToggleLabels() {
      document.querySelectorAll("[data-sound-toggle]").forEach(button => {
        button.textContent = this.muted ? "Sound OFF" : "Sound ON";
        button.classList.toggle("muted", this.muted);
        button.setAttribute("aria-pressed", String(!this.muted));
      });
    }

    toggleMuted() {
      this.muted = !this.muted;
      localStorage.setItem(STORAGE_KEY, String(this.muted));
      this.syncToggleLabels();
    }

    ensureAudio() {
      if (!this.audioContext) {
        const Ctx = window.AudioContext || window.webkitAudioContext;
        if (!Ctx) return false;
        this.audioContext = new Ctx();
        this.masterGain = this.audioContext.createGain();
        this.masterGain.gain.value = 0.08;
        this.masterGain.connect(this.audioContext.destination);
      }
      if (this.audioContext.state === "suspended") this.audioContext.resume();
      return true;
    }

    beep(frequency, duration, type = "sine", gain = 1) {
      if (this.muted) return;
      if (!this.ensureAudio()) return;

      const now = this.audioContext.currentTime;
      const osc = this.audioContext.createOscillator();
      const amp = this.audioContext.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(frequency, now);
      amp.gain.setValueAtTime(0.0001, now);
      amp.gain.exponentialRampToValueAtTime(0.05 * gain, now + 0.01);
      amp.gain.exponentialRampToValueAtTime(0.0001, now + duration);
      osc.connect(amp);
      amp.connect(this.masterGain);
      osc.start(now);
      osc.stop(now + duration + 0.02);
    }

    play(kind = "click") {
      if (this.muted) return;
      const now = performance.now();
      if (now - this.lastPlayAt < 45) return;
      this.lastPlayAt = now;

      if (kind === "toggle") {
        this.beep(620, 0.05, "square", 0.9);
        this.beep(820, 0.07, "triangle", 0.7);
      } else if (kind === "navigate") {
        this.beep(500, 0.05, "triangle", 0.8);
        this.beep(760, 0.08, "triangle", 0.7);
      } else if (kind === "tick") {
        this.beep(720, 0.04, "square", 0.5);
      } else if (kind === "success") {
        this.beep(560, 0.05, "triangle", 0.7);
        this.beep(780, 0.09, "triangle", 0.85);
      } else if (kind === "warning") {
        this.beep(420, 0.08, "sawtooth", 0.7);
      } else if (kind === "error") {
        this.beep(320, 0.1, "sawtooth", 0.8);
      } else {
        this.beep(640, 0.05, "triangle", 0.6);
      }
    }
  }

  window.uiSound = new UiSoundManager();
  window.addEventListener("DOMContentLoaded", () => window.uiSound.init());
})();
