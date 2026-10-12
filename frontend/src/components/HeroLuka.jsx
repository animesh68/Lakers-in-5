import React, { useState, useRef, useEffect, useCallback } from 'react';
import { HERO_VIDEOS } from '../utils/heroVideos';

export default function HeroLuka() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [activeSlot, setActiveSlot] = useState(0); // 0 = slot A, 1 = slot B
  const [slotSources, setSlotSources] = useState([
    HERO_VIDEOS[0]?.src || '/hero-luka.mp4',
    HERO_VIDEOS[1 % HERO_VIDEOS.length]?.src || '/hero-luka.mp4',
  ]);

  const videoRefA = useRef(null);
  const videoRefB = useRef(null);
  const isTransitioningRef = useRef(false);

  const scrollTo = (id) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Safe playback helper with autoplay restriction recovery
  const playVideo = useCallback(async (videoEl) => {
    if (!videoEl) return;
    try {
      videoEl.muted = true;
      videoEl.defaultMuted = true;
      await videoEl.play();
    } catch {
      // Autoplay fallback: muted inline retry
      videoEl.muted = true;
      videoEl.play().catch(() => {});
    }
  }, []);

  // Advance to next video in sequence
  const advanceToNext = useCallback(() => {
    if (isTransitioningRef.current) return;
    isTransitioningRef.current = true;

    const nextIndex = (currentIndex + 1) % HERO_VIDEOS.length;
    const nextNextIndex = (nextIndex + 1) % HERO_VIDEOS.length;
    const nextSlot = activeSlot === 0 ? 1 : 0;
    const nextVideoEl = nextSlot === 0 ? videoRefA.current : videoRefB.current;

    // Start playing preloaded target video
    if (nextVideoEl) {
      playVideo(nextVideoEl);
    }

    setActiveSlot(nextSlot);
    setCurrentIndex(nextIndex);

    // Prepare idle slot with next upcoming video
    setSlotSources((prev) => {
      const nextSources = [...prev];
      nextSources[activeSlot] = HERO_VIDEOS[nextNextIndex]?.src || '/hero-luka.mp4';
      return nextSources;
    });

    setTimeout(() => {
      isTransitioningRef.current = false;
    }, 900);
  }, [currentIndex, activeSlot, playVideo]);

  // Initial playback on mount
  useEffect(() => {
    const activeEl = activeSlot === 0 ? videoRefA.current : videoRefB.current;
    if (activeEl) {
      playVideo(activeEl);
    }
  }, [activeSlot, playVideo]);

  // Graceful error fallback for Slot A
  const handleErrorA = (e) => {
    const currentVideo = HERO_VIDEOS[currentIndex];
    if (videoRefA.current && currentVideo?.fallbackSrc && videoRefA.current.src !== currentVideo.fallbackSrc) {
      videoRefA.current.src = currentVideo.fallbackSrc;
      playVideo(videoRefA.current);
    } else if (videoRefA.current && currentVideo?.rootFallback && videoRefA.current.src !== currentVideo.rootFallback) {
      videoRefA.current.src = currentVideo.rootFallback;
      playVideo(videoRefA.current);
    } else {
      advanceToNext();
    }
  };

  // Graceful error fallback for Slot B
  const handleErrorB = (e) => {
    const nextIndex = (currentIndex + 1) % HERO_VIDEOS.length;
    const nextVideo = HERO_VIDEOS[nextIndex];
    if (videoRefB.current && nextVideo?.fallbackSrc && videoRefB.current.src !== nextVideo.fallbackSrc) {
      videoRefB.current.src = nextVideo.fallbackSrc;
    } else if (videoRefB.current && nextVideo?.rootFallback && videoRefB.current.src !== nextVideo.rootFallback) {
      videoRefB.current.src = nextVideo.rootFallback;
    } else {
      advanceToNext();
    }
  };

  return (
    <section
      id="hero"
      style={{
        position: 'relative',
        height: '100vh',
        minHeight: '680px',
        width: '100%',
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'flex-end',
        paddingBottom: '80px',
        backgroundColor: '#121015',
      }}
    >
      {/* Dual Pre-buffered Video Rotation (Slot A) */}
      <video
        ref={videoRefA}
        src={slotSources[0]}
        autoPlay
        muted
        playsInline
        preload="auto"
        onEnded={() => {
          if (activeSlot === 0) advanceToNext();
        }}
        onError={handleErrorA}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: 'center 35%',
          zIndex: 1,
          pointerEvents: 'none',
          opacity: activeSlot === 0 ? 1 : 0,
          transition: 'opacity 800ms ease-in-out',
        }}
      />

      {/* Dual Pre-buffered Video Rotation (Slot B) */}
      <video
        ref={videoRefB}
        src={slotSources[1]}
        muted
        playsInline
        preload="auto"
        onEnded={() => {
          if (activeSlot === 1) advanceToNext();
        }}
        onError={handleErrorB}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: 'center 35%',
          zIndex: 1,
          pointerEvents: 'none',
          opacity: activeSlot === 1 ? 1 : 0,
          transition: 'opacity 800ms ease-in-out',
        }}
      />

      {/* Dark Cinematic Overlays */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'linear-gradient(180deg, rgba(18, 16, 21, 0.4) 0%, rgba(18, 16, 21, 0.15) 40%, rgba(18, 16, 21, 0.85) 85%, #121015 100%)',
          zIndex: 2,
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(circle at center, transparent 40%, rgba(18, 16, 21, 0.65) 100%)',
          zIndex: 2,
          pointerEvents: 'none',
        }}
      />

      {/* Hero Content (Restrained 20-30% visual field) */}
      <div className="container" style={{ position: 'relative', zIndex: 3, width: '100%' }}>
        <div style={{ maxWidth: '780px' }} className="animate-fade-in">
          {/* Small Eyebrow */}
          <div
            className="section-eyebrow light"
            style={{
              marginBottom: '12px',
              fontSize: '0.9rem',
              letterSpacing: '0.2em',
            }}
          >
            LAKERS IN 5
          </div>

          {/* Main Headline */}
          <h1
            className="font-display"
            style={{
              fontSize: 'clamp(2.8rem, 6.5vw, 5.4rem)',
              fontWeight: 800,
              lineHeight: 0.95,
              letterSpacing: '0.02em',
              color: '#FFFFFF',
              marginBottom: '16px',
              textShadow: '0 4px 20px rgba(0, 0, 0, 0.6)',
            }}
          >
            THE GAME,<br />BEFORE THE GAME.
          </h1>

          {/* Subheadline */}
          <p
            style={{
              fontSize: 'clamp(1.05rem, 1.8vw, 1.3rem)',
              color: '#E2DFE8',
              lineHeight: 1.5,
              marginBottom: '32px',
              maxWidth: '540px',
              textShadow: '0 2px 10px rgba(0, 0, 0, 0.8)',
            }}
          >
            Machine learning predictions for the Lakers' next game.
          </p>

          {/* Action CTAs */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              gap: '16px',
            }}
          >
            <button
              onClick={() => scrollTo('next-game')}
              className="btn-primary"
            >
              VIEW NEXT GAME →
            </button>
            <button
              onClick={() => scrollTo('engine')}
              className="btn-secondary"
            >
              EXPLORE THE ENGINE
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
