/** Shared marketing site interactions */
(function () {
  'use strict';

  const navToggle = document.getElementById('navToggle');
  const mobileMenu = document.getElementById('mobileMenu');
  const nav = document.getElementById('nav');

  if (navToggle && mobileMenu) {
    navToggle.addEventListener('click', () => {
      mobileMenu.classList.toggle('active');
      navToggle.classList.toggle('active');
    });
    mobileMenu.querySelectorAll('.mobile-link').forEach((link) => {
      link.addEventListener('click', () => {
        mobileMenu.classList.remove('active');
        navToggle.classList.remove('active');
      });
    });
  }

  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (!href || href.length <= 1) return;
      const el = document.querySelector(href);
      if (el) {
        e.preventDefault();
        el.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  if (nav) {
    window.addEventListener('scroll', () => {
      nav.classList.toggle('scrolled', window.scrollY > 50);
    }, { passive: true });
  }

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (!reducedMotion) {
    const revealObs = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            revealObs.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );
    document.querySelectorAll('.reveal').forEach((el) => revealObs.observe(el));
  } else {
    document.querySelectorAll('.reveal').forEach((el) => el.classList.add('visible'));
  }

  document.querySelectorAll('[data-count]').forEach((el) => {
    const target = parseInt(el.dataset.count, 10);
    if (isNaN(target)) return;
    const obs = new IntersectionObserver(
      (entries) => {
        if (!entries[0].isIntersecting) return;
        let cur = 0;
        const step = target / 50;
        const tick = () => {
          cur += step;
          el.textContent = cur < target ? Math.floor(cur) : target;
          if (cur < target) requestAnimationFrame(tick);
        };
        tick();
        obs.unobserve(el);
      },
      { threshold: 0.5 }
    );
    obs.observe(el);
  });

  const video = document.getElementById('demoVideo');
  const fallback = document.getElementById('videoFallback');
  const playOverlay = document.getElementById('videoPlayOverlay');

  if (video && fallback) {
    const showFallback = () => {
      video.style.display = 'none';
      if (playOverlay) playOverlay.style.display = 'none';
      fallback.classList.add('visible');
    };
    video.addEventListener('error', showFallback);
    if (!video.canPlayType('video/mp4')) showFallback();
    video.addEventListener('loadeddata', () => fallback.classList.remove('visible'));
  }

  if (playOverlay) {
    playOverlay.addEventListener('click', () => {
      const videoEl = document.getElementById('demoVideo');
      if (videoEl && videoEl.readyState >= 2) {
        playOverlay.style.display = 'none';
        videoEl.play();
      } else {
        window.location.href = '/demo';
      }
    });
  }
})();
