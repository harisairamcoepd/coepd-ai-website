(() => {
  function initContactForm() {
    const form = document.getElementById("contactForm");
    const msg = document.getElementById("formMsg");
    if (!form || !msg) return;

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      msg.textContent = "Thanks! Your enquiry has been captured. Our team will contact you shortly.";
      form.reset();
    });
  }

  function initMarqueePause() {
    const marquee = document.querySelector(".logo-marquee");
    const track = document.querySelector(".logo-track");
    if (!marquee || !track) return;

    marquee.addEventListener("mouseenter", () => {
      track.style.animationPlayState = "paused";
    });

    marquee.addEventListener("mouseleave", () => {
      track.style.animationPlayState = "running";
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initContactForm();
    initMarqueePause();
  });
})();
