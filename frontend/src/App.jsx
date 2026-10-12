import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import HeroLuka from './components/HeroLuka';
import NextGameSection from './components/NextGameSection';
import PlayerProjectionsSection from './components/PlayerProjectionsSection';
import ScheduleSection from './components/ScheduleSection';
import EngineTeaserBanner from './components/EngineTeaserBanner';
import EnginePage from './components/EnginePage';
import Footer from './components/Footer';
import { api } from './api';

export default function App() {
  const [currentRoute, setCurrentRoute] = useState(() => {
    return window.location.pathname.startsWith('/engine') ? '/engine' : '/';
  });
  const [activeSection, setActiveSection] = useState('hero');

  // Listen for browser forward/backward navigation
  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname.startsWith('/engine') ? '/engine' : '/';
      setCurrentRoute(path);
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const handleNavigate = (route, targetId = null) => {
    const targetRoute = route.startsWith('/engine') ? '/engine' : '/';
    if (targetRoute !== currentRoute) {
      window.history.pushState({}, '', targetRoute);
      setCurrentRoute(targetRoute);
    }
    if (targetRoute === '/engine') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else if (targetRoute === '/' && targetId) {
      setTimeout(() => {
        const el = document.getElementById(targetId);
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 60);
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  // Single source of truth for Selected Game
  const [selectedGame, setSelectedGame] = useState({
    game_id: "5",
    game_num: 5,
    home_team: "Los Angeles Lakers",
    away_team: "Golden State Warriors",
    home_team_code: "LAL",
    away_team_code: "GSW",
    game_date: "2026-10-21",
    is_lakers_home: true,
  });

  // Current Prediction State
  const [currentPrediction, setCurrentPrediction] = useState(null);
  const [loadingPrediction, setLoadingPrediction] = useState(true);
  const [predictionError, setPredictionError] = useState(null);

  // Schedule list for quick switcher and schedule section
  const [scheduleGames, setScheduleGames] = useState([]);

  // Initial Load: Load Next Lakers Prediction & Full Lakers Schedule
  useEffect(() => {
    let isCancelled = false;

    const loadInitialData = async () => {
      setLoadingPrediction(true);
      setPredictionError(null);

      // 1. Fetch next Lakers prediction
      try {
        const nextData = await api.getLakersNext();
        if (!isCancelled && nextData) {
          setCurrentPrediction(nextData);
          setSelectedGame({
            game_id: String(nextData.game_id || "5"),
            game_num: parseInt(nextData.game_id || "5"),
            home_team: nextData.home_team || "Los Angeles Lakers",
            away_team: nextData.away_team || "Golden State Warriors",
            home_team_code: nextData.home_team_code || (nextData.is_lakers_home ? "LAL" : "GSW"),
            away_team_code: nextData.away_team_code || (!nextData.is_lakers_home ? "LAL" : "GSW"),
            game_date: nextData.game_date || "2026-10-21",
            is_lakers_home: nextData.is_lakers_home ?? true,
          });
          setLoadingPrediction(false);
        }
      } catch (err) {
        if (!isCancelled) {
          setPredictionError(err.message || 'Unable to load prediction');
          setLoadingPrediction(false);
        }
      }

      // 2. Fetch official 2026-27 Lakers schedule
      try {
        const schedData = await api.getSchedule("2026-27", "LAL", 20);
        const parsedGames = Array.isArray(schedData) ? schedData : (schedData?.games || []);
        if (!isCancelled && parsedGames.length > 0) {
          setScheduleGames(parsedGames);
        }
      } catch {
        // Non-fatal schedule fetch
      }
    };

    loadInitialData();
    return () => { isCancelled = true; };
  }, []);

  // Track active section for header navigation
  useEffect(() => {
    const handleScroll = () => {
      const sections = ['hero', 'next-game', 'player-projections', 'schedule', 'engine'];
      const scrollPosition = window.scrollY + 200;

      for (const section of sections) {
        const el = document.getElementById(section);
        if (el) {
          const top = el.offsetTop;
          const height = el.offsetHeight;
          if (scrollPosition >= top && scrollPosition < top + height) {
            setActiveSection(section);
            break;
          }
        }
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Handle Game Selection from Schedule or Dropdown (Updates all sections synchronously)
  const handleSelectGame = async (game) => {
    const homeCode = game.home_team_code || (game.is_lakers_home ? 'LAL' : 'GSW');
    const awayCode = game.away_team_code || (!game.is_lakers_home ? 'LAL' : 'GSW');
    const gameDate = game.game_date;
    const gameId = String(game.game_num || game.game_id || '5');

    // Update single source of truth
    setSelectedGame({
      game_id: gameId,
      game_num: parseInt(gameId),
      home_team: game.home_team,
      away_team: game.away_team,
      home_team_code: homeCode,
      away_team_code: awayCode,
      game_date: gameDate,
      is_lakers_home: homeCode === 'LAL',
    });

    setLoadingPrediction(true);
    setPredictionError(null);

    try {
      const pred = await api.predictMatchup(
        game.home_team || homeCode,
        game.away_team || awayCode,
        gameDate
      );

      const isLALHome = homeCode === 'LAL';
      setCurrentPrediction({
        game_id: gameId,
        game_date: gameDate,
        is_lakers_home: isLALHome,
        home_team: game.home_team || 'Los Angeles Lakers',
        away_team: game.away_team || 'Golden State Warriors',
        opponent_team: isLALHome ? (game.away_team || awayCode) : (game.home_team || homeCode),
        lakers_win_probability: isLALHome ? pred.home_win_probability : pred.away_win_probability,
        opponent_win_probability: isLALHome ? pred.away_win_probability : pred.home_win_probability,
        predicted_lakers_margin: isLALHome ? pred.predicted_home_margin : -pred.predicted_home_margin,
      });
      setLoadingPrediction(false);
    } catch (err) {
      setPredictionError(err.message || 'Unable to load prediction for selected game');
      setLoadingPrediction(false);
    }

    // Scroll to the next game section
    const el = document.getElementById('next-game');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  if (currentRoute === '/engine') {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Header currentRoute={currentRoute} onNavigate={handleNavigate} />
        <main style={{ flex: 1 }}>
          <EnginePage onNavigate={handleNavigate} />
        </main>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* 0. Header (Minimal Wordmark & Sports Navigation) */}
      <Header currentRoute={currentRoute} activeSection={activeSection} onNavigate={handleNavigate} />

      {/* Main Experience Flow */}
      <main style={{ flex: 1 }}>
        {/* 1. HERO: Full-Bleed Luka Doncic Video Hero */}
        <HeroLuka />

        {/* 2. NEXT GAME: Prediction & Broadcast Matchup */}
        <NextGameSection
          prediction={currentPrediction}
          loading={loadingPrediction}
          error={predictionError}
          scheduleGames={scheduleGames}
          selectedGame={selectedGame}
          onSelectGame={handleSelectGame}
        />

        {/* 3. PROJECTED LINEUP & PLAYER PREDICTIONS: THE ROTATION */}
        <PlayerProjectionsSection
          gameId={selectedGame.game_id}
          homeTeam={selectedGame.home_team_code}
          awayTeam={selectedGame.away_team_code}
          gameDate={selectedGame.game_date}
        />

        {/* 4. SCHEDULE: Live Dynamic Schedule from /schedule/2026-27 */}
        <ScheduleSection
          onSelectGame={handleSelectGame}
          selectedGameId={selectedGame.game_id}
        />

        {/* 5. COMPACT TECHNICAL TEASER: Editorial transition linking to /engine */}
        <EngineTeaserBanner onNavigate={handleNavigate} />
      </main>

      {/* 6. FOOTER: 75vh Contained Player Slideshow Closing Scene */}
      <Footer />
    </div>
  );
}
