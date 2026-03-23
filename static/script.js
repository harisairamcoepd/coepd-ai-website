(() => {
  /* â”€â”€ Base UI (year, nav toggle, smooth scroll, nav shadow, scroll progress) â”€â”€ */
  function initBaseUI() {
    const yearEl = document.getElementById("year");
    if (yearEl) yearEl.textContent = String(new Date().getFullYear());

    const navToggle = document.getElementById("nav-toggle");
    const links = document.querySelector(".nav-menu, .links");
    if (navToggle && links) {
      navToggle.addEventListener("click", () => {
        const isOpen = links.classList.toggle("open");
        navToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
      });

      document.addEventListener("click", (event) => {
        if (!links.classList.contains("open")) return;
        if (links.contains(event.target) || navToggle.contains(event.target)) return;
        links.classList.remove("open");
        navToggle.setAttribute("aria-expanded", "false");
      });
    }

    function getSamePageHashTarget(href) {
      if (!href || href === "#") return null;

      try {
        const url = new URL(href, window.location.origin);
        if (url.pathname !== window.location.pathname && url.pathname !== "/") return null;
        return url.hash || null;
      } catch (_) {
        return href.startsWith("#") ? href : null;
      }
    }

    // Close mobile menu on in-page anchor click
    document.querySelectorAll("a").forEach((a) => {
      a.addEventListener("click", () => {
        const hash = getSamePageHashTarget(a.getAttribute("href"));
        if (!hash) return;
        if (links && links.classList.contains("open")) {
          links.classList.remove("open");
          if (navToggle) navToggle.setAttribute("aria-expanded", "false");
        }
      });
    });

    // Smooth scroll with header offset
    document.querySelectorAll("a").forEach((a) => {
      a.addEventListener("click", (e) => {
        const hash = getSamePageHashTarget(a.getAttribute("href"));
        if (!hash) return;
        const target = document.querySelector(hash);
        if (!target) return;
        e.preventDefault();
        const navHeight = document.querySelector(".site-header")?.offsetHeight || 80;
        const y = target.getBoundingClientRect().top + window.scrollY - navHeight - 12;
        window.scrollTo({ top: y, behavior: "smooth" });
      });
    });

    // Nav shadow on scroll + scroll progress bar
    const nav = document.querySelector(".nav");
    const progressBar = document.querySelector(".scroll-progress");
    if (nav) {
      const onScroll = () => {
        nav.classList.toggle("scrolled", window.scrollY > 10);
        if (progressBar) {
          const scrollTop = window.scrollY;
          const docHeight = document.documentElement.scrollHeight - window.innerHeight;
          const progress = docHeight > 0 ? scrollTop / docHeight : 0;
          progressBar.style.transform = "scaleX(" + progress + ")";
        }
      };
      window.addEventListener("scroll", onScroll, { passive: true });
      onScroll();
    }

    // Active nav link tracking
    initActiveNavTracking();
  }

  /* â”€â”€ Staggered scroll-reveal for sections â”€â”€ */
  function initSectionReveal() {
    const els = document.querySelectorAll(".section");
    if (!els.length) return;
    els.forEach((el) => el.classList.add("reveal"));

    const observer = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          obs.unobserve(entry.target);
        });
      },
      { threshold: 0.08, rootMargin: "0px 0px -60px 0px" }
    );
    els.forEach((el) => observer.observe(el));
  }

  /* â”€â”€ data-animate fallback reveal system (used when AOS is unavailable) â”€â”€ */
  function initDataAnimateFallback() {
    const items = document.querySelectorAll("[data-animate]");
    if (!items.length) return;

    const observer = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const el = entry.target;
          const delay = parseInt(el.getAttribute("data-delay") || "0", 10);
          if (delay > 0) {
            setTimeout(() => el.classList.add("is-visible"), delay);
          } else {
            el.classList.add("is-visible");
          }
          obs.unobserve(el);
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
    );
    items.forEach((el) => observer.observe(el));
  }

  /* â”€â”€ AOS scroll animations â”€â”€ */
  function initAOSAnimations() {
    const items = document.querySelectorAll("[data-animate]");
    const map = {
      "fade-up": "fade-up",
      "fade-down": "fade-down",
      "fade-left": "fade-left",
      "fade-right": "fade-right",
      "zoom-in": "zoom-in"
    };

    items.forEach((el) => {
      const anim = el.getAttribute("data-animate") || "fade-up";
      const delay = el.getAttribute("data-delay") || "0";
      el.setAttribute("data-aos", map[anim] || "fade-up");
      el.setAttribute("data-aos-delay", delay);
      el.setAttribute("data-aos-duration", "700");
      el.setAttribute("data-aos-once", "true");
    });

    if (typeof window.AOS !== "undefined") {
      window.AOS.init({
        easing: "cubic-bezier(.22,1,.36,1)",
        once: true,
        mirror: false,
        offset: 70,
      });
      return;
    }

    document.body.classList.add("use-custom-animate");
    initDataAnimateFallback();
  }

  /* â”€â”€ Location card redirects â”€â”€ */
  function initLocationRedirects() {
    const cards = document.querySelectorAll(".location-card[data-redirect]");
    if (!cards.length) return;

    function go(card) {
      const url = card.getAttribute("data-redirect");
      if (url) window.location.href = url;
    }

    cards.forEach((card) => {
      card.addEventListener("click", () => go(card));
      card.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          go(card);
        }
      });
    });
  }

  /* â”€â”€ Direct dialing for call links â”€â”€ */
  function initCallRedirects() {
    const callLinks = document.querySelectorAll('a[href^="tel:"]');
    if (!callLinks.length) return;

    callLinks.forEach((link) => {
      link.addEventListener("click", (event) => {
        const phone = link.getAttribute("href");
        if (!phone) return;
        event.preventDefault();
        window.location.href = phone;
      });
    });
  }

  /* â”€â”€ Contact form with validation â”€â”€ */
  function initContactForm() {
    const form = document.getElementById("contactForm");
    const msg = document.getElementById("formMsg");
    if (!form || !msg) return;

    const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const phoneRe = /^[+]?[\d\s\-()]{7,15}$/;

    function showErr(name, text) {
      const el = document.getElementById("err-" + name);
      const input = form.querySelector('[name="' + name + '"]');
      if (el) el.textContent = text;
      if (input) input.classList.toggle("input-error", !!text);
    }

    function clearErrors() {
      form.querySelectorAll(".field-error").forEach((el) => (el.textContent = ""));
      form.querySelectorAll(".input-error").forEach((el) => el.classList.remove("input-error"));
    }

    function validate() {
      clearErrors();
      const val = (n) => String(form.querySelector('[name="' + n + '"]')?.value || "").trim();
      let ok = true;

      if (!val("firstName")) { showErr("firstName", "First name is required"); ok = false; }
      if (!val("lastName"))  { showErr("lastName", "Last name is required"); ok = false; }

      const em = val("email");
      if (!em) { showErr("email", "Email is required"); ok = false; }
      else if (!emailRe.test(em)) { showErr("email", "Enter a valid email"); ok = false; }

      const ph = val("phone");
      if (!ph) { showErr("phone", "Phone number is required"); ok = false; }
      else if (!phoneRe.test(ph)) { showErr("phone", "Enter a valid phone number"); ok = false; }

      if (!val("interested_domain")) { showErr("interested_domain", "Please select your domain"); ok = false; }

      return ok;
    }

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!validate()) return;

      msg.textContent = "Submittingâ€¦";
      msg.style.color = "#475569";

      const val = (n) => String(form.querySelector('[name="' + n + '"]')?.value || "").trim();

      const payload = {
        name: val("firstName") + " " + val("lastName"),
        email: val("email"),
        phone: val("phone"),
        interested_domain: val("interested_domain"),
        location: val("location"),
        message: val("message"),
        source: "webpage",
      };

      try {
        const res = await fetch((window.__API_BASE__ || "") + "/enquiry", {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify(payload),
        });
        if (!res.ok) {
          const errBody = await res.text().catch(() => "");
          throw new Error("HTTP " + res.status + ": " + errBody);
        }
        const contentType = String(res.headers.get("content-type") || "").toLowerCase();
        if (!contentType.includes("application/json")) {
          throw new Error("Non-JSON response received");
        }
        const data = await res.json().catch(() => ({}));
        if (!data || data.ok !== true || !data.id) {
          throw new Error("Lead save was not acknowledged by backend");
        }
        msg.textContent = data.message || "Thanks! Our team will contact you within 24 hours.";
        msg.style.color = "#10B981";
        form.reset();
        clearErrors();
      } catch (err) {
        console.error("Contact form error:", err);
        msg.textContent = "Unable to submit right now. Please try again.";
        msg.style.color = "#dc2626";
      }
    });

    // Real-time clear errors on input
    form.querySelectorAll("input, select, textarea").forEach((el) => {
      el.addEventListener("input", () => {
        const name = el.getAttribute("name");
        if (name) showErr(name, "");
      });
    });
  }

  /* â”€â”€ Metric counter animation â”€â”€ */
  function initMetricCounters() {
    const nums = document.querySelectorAll(".metric-num[data-target]");
    if (!nums.length) return;

    const observer = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const el = entry.target;
          obs.unobserve(el);
          const target = parseInt(el.getAttribute("data-target"), 10);
          if (isNaN(target)) return;
          const duration = 2200;
          const start = performance.now();
          function tick(now) {
            const t = Math.min((now - start) / duration, 1);
            const ease = 1 - Math.pow(1 - t, 3);
            el.textContent = Math.round(target * ease).toLocaleString("en-IN");
            if (t < 1) requestAnimationFrame(tick);
          }
          requestAnimationFrame(tick);
        });
      },
      { threshold: 0.3 }
    );
    nums.forEach((el) => observer.observe(el));
  }

  /* â”€â”€ Placement Lottie lazy-load on viewport entry â”€â”€ */
  function initPlacementAnimations() {
    const players = document.querySelectorAll("#placements lottie-player[data-lottie-src]");
    if (!players.length) return;

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const observer = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const player = entry.target;
          const src = player.getAttribute("data-lottie-src");
          if (!src || player.getAttribute("src")) {
            obs.unobserve(player);
            return;
          }

          player.setAttribute("src", src);
          if (reduceMotion) {
            player.removeAttribute("autoplay");
          } else {
            player.setAttribute("autoplay", "");
          }

          obs.unobserve(player);
        });
      },
      { threshold: 0.25, rootMargin: "0px 0px -40px 0px" }
    );

    players.forEach((player) => observer.observe(player));
  }

  /* â”€â”€ Active nav link tracking based on scroll position â”€â”€ */
  function initActiveNavTracking() {
    const navLinks = document.querySelectorAll(".links a, .nav-menu a");
    if (!navLinks.length) return;
    const sections = [];
    navLinks.forEach((link) => {
      const href = link.getAttribute("href");
      if (!href || href === "#") return;
      const hash = href.includes("#") ? "#" + href.split("#")[1] : null;
      if (!hash) return;
      const section = document.querySelector(hash);
      if (section) sections.push({ el: section, link: link });
    });
    if (!sections.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const match = sections.find((s) => s.el === entry.target);
          if (match) {
            if (entry.isIntersecting) {
              navLinks.forEach((l) => l.classList.remove("active"));
              match.link.classList.add("active");
            }
          }
        });
      },
      { threshold: 0.2, rootMargin: "-80px 0px -40% 0px" }
    );
    sections.forEach((s) => observer.observe(s.el));
  }

  /* â”€â”€ Parallax hero orbs on mouse move â”€â”€ */
  function initHeroParallax() {
    const hero = document.querySelector(".hero-section, .hero");
    if (!hero || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const orbs = hero.querySelectorAll(".hero-orb");
    if (!orbs.length) return;

    hero.addEventListener("mousemove", (e) => {
      const rect = hero.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      orbs.forEach((orb, i) => {
        const speed = (i + 1) * 8;
        orb.style.transform = "translate(" + (x * speed) + "px, " + (y * speed) + "px)";
      });
    });
  }

  /* â”€â”€ Tool Detail Modal Popups â”€â”€ */
  function initToolModals() {
    var toolData = {
      jira: {
        icon: "\ud83d\udccb",
        title: "Jira",
        desc: "Jira is a leading project management tool used by Agile teams worldwide to plan, track, and release software.",
        usage: "Business Analysts use Jira to manage Agile projects, track requirements, write user stories, manage the product backlog, and collaborate with development teams during sprint planning and execution.",
        example: "Creating user stories for a banking application, managing the backlog for a healthcare portal, and tracking sprint progress for an e-commerce project."
      },
      sql: {
        icon: "\ud83d\uddc3\ufe0f",
        title: "SQL",
        desc: "SQL (Structured Query Language) is the standard language for managing and querying relational databases.",
        usage: "Business Analysts use SQL to extract data for analysis, validate business rules against databases, write queries for reporting, and verify data integrity during UAT testing.",
        example: "Writing queries to extract customer transaction data from a banking database, generating monthly sales reports, and validating data migration accuracy."
      },
      powerbi: {
        icon: "\ud83d\udcca",
        title: "Power BI",
        desc: "Power BI is Microsoft\u2019s business intelligence platform for creating interactive dashboards and data visualizations.",
        usage: "Business Analysts use Power BI to build dashboards for stakeholders, create visual reports from complex datasets, and present data-driven insights to leadership teams.",
        example: "Building a real-time sales dashboard for an e-commerce company, creating KPI reports for hospital management, and visualizing insurance claim trends."
      },
      tableau: {
        icon: "\ud83d\udcc8",
        title: "Tableau",
        desc: "Tableau is a powerful data visualization tool that helps transform raw data into interactive and shareable dashboards.",
        usage: "Business Analysts use Tableau to create visual analytics, identify trends and patterns, build interactive reports, and present findings to business stakeholders.",
        example: "Analyzing customer churn patterns for a telecom company, building geographic sales heat maps, and creating executive dashboards for quarterly reviews."
      },
      balsamiq: {
        icon: "\u270f\ufe0f",
        title: "Balsamiq",
        desc: "Balsamiq is a rapid wireframing tool that helps teams design user interfaces and application layouts.",
        usage: "Business Analysts use Balsamiq to create low-fidelity wireframes for new features, validate UI requirements with stakeholders, and communicate design ideas to development teams.",
        example: "Designing wireframes for a mobile banking app, prototyping a patient registration portal, and mocking up dashboard layouts for approval."
      },
      drawio: {
        icon: "\ud83d\udd17",
        title: "Draw.io",
        desc: "Draw.io is a free diagramming tool for creating flowcharts, process diagrams, and system architecture visuals.",
        usage: "Business Analysts use Draw.io to map business processes, create workflow diagrams, design data flow diagrams (DFDs), and document system interactions.",
        example: "Mapping the loan approval workflow for a bank, creating a patient admission process flowchart, and designing data flow for an inventory system."
      },
      visio: {
        icon: "\ud83d\udcd0",
        title: "MS Visio",
        desc: "Microsoft Visio is an enterprise-grade diagramming tool for creating UML diagrams, architecture blueprints, and process maps.",
        usage: "Business Analysts use Visio to create UML use case diagrams, activity diagrams, swim lane process flows, and enterprise architecture documentation.",
        example: "Creating UML diagrams for a CRM system, designing swim lane workflows for insurance claim processing, and mapping enterprise data architecture."
      },
      confluence: {
        icon: "\ud83d\udcd1",
        title: "Confluence",
        desc: "Atlassian Confluence is a collaboration and documentation platform for teams and projects.",
        usage: "Business Analysts use Confluence for requirements documentation, knowledge base maintenance, stakeholder collaboration, and sharing specifications and meeting notes.",
        example: "Maintaining a requirements repository, documenting user stories and decisions, and sharing meeting notes with stakeholders."
      },
      azure: {
        icon: "\u2601\ufe0f",
        title: "Azure",
        desc: "Microsoft Azure is a cloud computing platform offering services for building, deploying, and managing applications.",
        usage: "Business Analysts use Azure DevOps for project management, CI/CD pipeline understanding, and collaborating with development teams in cloud-based environments.",
        example: "Managing project boards in Azure DevOps, understanding deployment pipelines for a SaaS product, and tracking work items for an Agile team."
      }
    };

    var overlay = document.getElementById("toolModalOverlay");
    var closeBtn = document.getElementById("toolModalClose");
    if (!overlay || !closeBtn) return;

    var iconEl = document.getElementById("toolModalIcon");
    var titleEl = document.getElementById("toolModalTitle");
    var descEl = document.getElementById("toolModalDesc");
    var usageEl = document.getElementById("toolModalUsage");
    var exampleEl = document.getElementById("toolModalExample");

    function openModal(key) {
      var data = toolData[key];
      if (!data) {
        return;
      }
      // Copy SVG icon from the tool card
      var cardEl = document.querySelector('.tool-card[data-tool="' + key + '"] .tool-icon');
      if (cardEl) {
        iconEl.innerHTML = cardEl.innerHTML;
      } else {
        iconEl.textContent = data.icon;
      }
      titleEl.textContent = data.title;
      descEl.textContent = data.desc;
      usageEl.textContent = data.usage;
      exampleEl.textContent = data.example;
      overlay.classList.add("is-active");
      document.body.style.overflow = "hidden";
    }

    function closeModal() {
      overlay.classList.remove("is-active");
      document.body.style.overflow = "";
    }

    document.querySelectorAll(".tool-card[data-tool]").forEach(function(card) {
      card.addEventListener("click", function() {
        openModal(card.getAttribute("data-tool"));
      });
    });

    closeBtn.addEventListener("click", closeModal);
    overlay.addEventListener("click", function(e) {
      if (e.target === overlay) closeModal();
    });
    document.addEventListener("keydown", function(e) {
      if (e.key === "Escape" && overlay.classList.contains("is-active")) closeModal();
    });
  }

  function initSuccessStoryLightbox() {
    const lightbox = document.getElementById("successLightbox");
    const lightboxImage = document.getElementById("successLightboxImage");
    const closeBtn = document.getElementById("successLightboxClose");
    const prevBtn = document.getElementById("successLightboxPrev");
    const nextBtn = document.getElementById("successLightboxNext");
    const zoomInBtn = document.getElementById("successZoomIn");
    const zoomOutBtn = document.getElementById("successZoomOut");
    const zoomResetBtn = document.getElementById("successZoomReset");
    const triggerImages = document.querySelectorAll(".success-story-item:not([aria-hidden='true']) img");
    if (!lightbox || !lightboxImage || !closeBtn || !triggerImages.length) return;

    const gallery = Array.from(triggerImages).map((img) => ({
      src: img.getAttribute("src") || "",
      alt: img.getAttribute("alt") || "Success story image",
    }));
    let currentIndex = 0;
    let zoomLevel = 1;

    function renderCurrentImage() {
      const current = gallery[currentIndex];
      if (!current) return;
      const src = current.src;
      const alt = current.alt;
      if (!src) return;
      lightboxImage.setAttribute("src", src);
      lightboxImage.setAttribute("alt", alt);
      lightboxImage.style.transform = `scale(${zoomLevel})`;
      if (zoomResetBtn) zoomResetBtn.textContent = `${Math.round(zoomLevel * 100)}%`;
    }

    function openLightbox(sourceImage) {
      const source = sourceImage.getAttribute("src");
      const index = gallery.findIndex((item) => item.src === source);
      currentIndex = index >= 0 ? index : 0;
      zoomLevel = 1;
      renderCurrentImage();
      lightbox.classList.add("is-open");
      lightbox.setAttribute("aria-hidden", "false");
      document.body.classList.add("lightbox-open");
    }

    function closeLightbox() {
      lightbox.classList.remove("is-open");
      lightbox.setAttribute("aria-hidden", "true");
      lightboxImage.setAttribute("src", "");
      lightboxImage.setAttribute("alt", "");
      zoomLevel = 1;
      document.body.classList.remove("lightbox-open");
    }

    function showPrevious() {
      currentIndex = (currentIndex - 1 + gallery.length) % gallery.length;
      zoomLevel = 1;
      renderCurrentImage();
    }

    function showNext() {
      currentIndex = (currentIndex + 1) % gallery.length;
      zoomLevel = 1;
      renderCurrentImage();
    }

    function updateZoom(nextZoom) {
      zoomLevel = Math.max(0.5, Math.min(3, nextZoom));
      lightboxImage.style.transform = `scale(${zoomLevel})`;
      if (zoomResetBtn) zoomResetBtn.textContent = `${Math.round(zoomLevel * 100)}%`;
    }

    triggerImages.forEach((image) => {
      image.addEventListener("click", () => openLightbox(image));
      image.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openLightbox(image);
        }
      });
    });

    closeBtn.addEventListener("click", closeLightbox);
    if (prevBtn) prevBtn.addEventListener("click", showPrevious);
    if (nextBtn) nextBtn.addEventListener("click", showNext);
    if (zoomInBtn) zoomInBtn.addEventListener("click", () => updateZoom(zoomLevel + 0.25));
    if (zoomOutBtn) zoomOutBtn.addEventListener("click", () => updateZoom(zoomLevel - 0.25));
    if (zoomResetBtn) zoomResetBtn.addEventListener("click", () => updateZoom(1));
    lightbox.addEventListener("click", (event) => {
      if (event.target.hasAttribute("data-close-lightbox")) {
        closeLightbox();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (!lightbox.classList.contains("is-open")) return;
      if (event.key === "Escape") closeLightbox();
      if (event.key === "ArrowLeft") showPrevious();
      if (event.key === "ArrowRight") showNext();
      if (event.key === "+") updateZoom(zoomLevel + 0.25);
      if (event.key === "-") updateZoom(zoomLevel - 0.25);
    });
  }

  function initSuccessStoriesScroller() {
    const marquee = document.querySelector(".success-stories-marquee");
    const track = marquee ? marquee.querySelector(".success-track") : null;
    const prevBtn = document.getElementById("successStoriesPrev");
    const nextBtn = document.getElementById("successStoriesNext");
    if (!marquee || !track) return;

    let paused = false;
    let rafId = null;
    let resumeTimer = null;
    const speed = 0.45;
    const trackStyle = window.getComputedStyle(track);
    const gap = parseFloat(trackStyle.columnGap || trackStyle.gap || "18") || 18;

    function getStepSize() {
      const firstCard = track.querySelector(".success-story-item");
      if (!firstCard) return 320;
      return firstCard.getBoundingClientRect().width + gap;
    }

    function tick() {
      if (!paused) {
        marquee.scrollLeft += speed;
        const loopPoint = track.scrollWidth / 2;
        if (marquee.scrollLeft >= loopPoint) {
          marquee.scrollLeft -= loopPoint;
        }
        if (marquee.scrollLeft <= 0) {
          marquee.scrollLeft += loopPoint;
        }
      }
      rafId = window.requestAnimationFrame(tick);
    }

    function nudge(direction) {
      paused = true;
      marquee.scrollBy({ left: getStepSize() * direction, behavior: "smooth" });
      if (resumeTimer) window.clearTimeout(resumeTimer);
      resumeTimer = window.setTimeout(() => {
        paused = false;
      }, 1200);
    }

    marquee.addEventListener("mouseenter", () => { paused = true; });
    marquee.addEventListener("mouseleave", () => { paused = false; });
    marquee.addEventListener("touchstart", () => { paused = true; }, { passive: true });
    marquee.addEventListener("touchend", () => { paused = false; }, { passive: true });

    if (prevBtn) prevBtn.addEventListener("click", () => nudge(-1));
    if (nextBtn) nextBtn.addEventListener("click", () => nudge(1));

    rafId = window.requestAnimationFrame(tick);
    window.addEventListener("beforeunload", () => {
      if (rafId) window.cancelAnimationFrame(rafId);
      if (resumeTimer) window.clearTimeout(resumeTimer);
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initBaseUI();
    initSectionReveal();
    initAOSAnimations();
    initSuccessStoriesScroller();
    initMetricCounters();
    initPlacementAnimations();
    initLocationRedirects();
    initCallRedirects();
    initContactForm();
    initToolModals();
    initSuccessStoryLightbox();
    initHeroParallax();
  });
})();
