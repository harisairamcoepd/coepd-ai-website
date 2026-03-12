(() => {
  /* ── Base UI (year, nav toggle, smooth scroll, nav shadow, scroll progress) ── */
  function initBaseUI() {
    const yearEl = document.getElementById("year");
    if (yearEl) yearEl.textContent = String(new Date().getFullYear());

    const navToggle = document.getElementById("nav-toggle");
    const links = document.querySelector(".links");
    if (navToggle && links) {
      navToggle.addEventListener("click", () => links.classList.toggle("open"));
    }

    // Close mobile menu on anchor click
    document.querySelectorAll('a[href^="#"]').forEach((a) => {
      a.addEventListener("click", () => {
        if (links && links.classList.contains("open")) links.classList.remove("open");
      });
    });

    // Smooth scroll with header offset
    document.querySelectorAll('a[href^="#"]').forEach((a) => {
      a.addEventListener("click", (e) => {
        const href = a.getAttribute("href");
        if (!href || href === "#") return;
        const target = document.querySelector(href);
        if (!target) return;
        e.preventDefault();
        const y = target.getBoundingClientRect().top + window.scrollY - 80;
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

  /* ── Staggered scroll-reveal for sections ── */
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

  /* ── data-animate fallback reveal system (used when AOS is unavailable) ── */
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

  /* ── AOS scroll animations ── */
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

  /* ── Testimonial Slider (Swiper) ── */
  function initTestimonialsSwiper() {
    const container = document.getElementById("testimonialSwiper");
    if (!container || typeof window.Swiper === "undefined") return;

    new window.Swiper(container, {
      slidesPerView: 1,
      spaceBetween: 20,
      loop: true,
      speed: 700,
      autoplay: {
        delay: 4500,
        disableOnInteraction: false,
      },
      pagination: {
        el: "#testimonialPagination",
        clickable: true,
      },
      navigation: {
        nextEl: "#testimonialNext",
        prevEl: "#testimonialPrev",
      },
      breakpoints: {
        720: { slidesPerView: 1.1, spaceBetween: 20 },
        1060: { slidesPerView: 2, spaceBetween: 24 },
      },
    });
  }

  /* ── Location card redirects ── */
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

  /* ── Contact form with validation ── */
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

      if (!val("interested_domain")) { showErr("interested_domain", "Please select a domain"); ok = false; }

      return ok;
    }

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!validate()) return;

      msg.textContent = "Submitting…";
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
        const data = await res.json().catch(() => ({}));
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

  /* ── Metric counter animation ── */
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

  /* ── Placement Lottie lazy-load on viewport entry ── */
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

  /* ── Active nav link tracking based on scroll position ── */
  function initActiveNavTracking() {
    const navLinks = document.querySelectorAll(".links a[href^='#']");
    if (!navLinks.length) return;
    const sections = [];
    navLinks.forEach((link) => {
      const href = link.getAttribute("href");
      if (!href || href === "#") return;
      const section = document.querySelector(href);
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

  /* ── Parallax hero orbs on mouse move ── */
  function initHeroParallax() {
    const hero = document.querySelector(".hero");
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

  /* ── Tool Detail Modal Popups ── */
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
      excel: {
        icon: "\ud83d\udcd1",
        title: "Excel",
        desc: "Microsoft Excel is the essential tool for data analysis, modeling, and business reporting.",
        usage: "Business Analysts use Excel for data analysis, creating pivot tables, building financial models, performing gap analysis, and managing requirements traceability matrices.",
        example: "Building a cost-benefit analysis for a new feature, creating a requirements traceability matrix, and performing data validation with pivot tables."
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
      if (!data) return;
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

  document.addEventListener("DOMContentLoaded", () => {
    initBaseUI();
    initSectionReveal();
    initAOSAnimations();
    initTestimonialsSwiper();
    initMetricCounters();
    initPlacementAnimations();
    initLocationRedirects();
    initContactForm();
    initToolModals();
    initHeroParallax();
  });
})();
