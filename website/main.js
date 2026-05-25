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
  let revealObs = null;

  if (!reducedMotion) {
    revealObs = new IntersectionObserver(
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

  /** Load top-3 live use cases on landing from showcase.json. */
  async function loadLandingUseCases() {
    const grid = document.getElementById('useCasesGrid');
    if (!grid) return;
    const featuredIds = ['ararat', 'pegasszn', 'pretenzia'];
    try {
      const res = await fetch('/welcome-assets/data/showcase.json');
      if (!res.ok) throw new Error('load failed');
      const data = await res.json();
      const cards = (data.cards || []).filter((c) => featuredIds.includes(c.id));
      if (cards.length === 0) throw new Error('no cards');
      grid.innerHTML = cards
        .map(
          (card) => `<article class="use-case-card reveal${card.status === 'live' ? ' use-case-card--featured' : ''}">
            ${card.status === 'live' ? '<span class="use-case-badge">Production</span>' : ''}
            <h3>${escapeHtml(card.title)}</h3>
            <p>${escapeHtml(card.one_liner)}</p>
            <p style="font-size:13px;font-weight:600;color:var(--accent);margin-top:8px">${escapeHtml(card.metric)}</p>
            <a href="/showcase#showcase" class="use-case-link">Подробнее →</a>
          </article>`,
        )
        .join('');
      if (!reducedMotion && revealObs) {
        grid.querySelectorAll('.reveal').forEach((el) => revealObs.observe(el));
      } else {
        grid.querySelectorAll('.reveal').forEach((el) => el.classList.add('visible'));
      }
    } catch {
      grid.innerHTML = `<p style="color:var(--text-secondary);grid-column:1/-1;text-align:center">
        <a href="/showcase" class="btn btn-primary">Смотреть кейсы →</a>
      </p>`;
    }
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  loadLandingUseCases();
})();
