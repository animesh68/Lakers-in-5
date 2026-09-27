import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Footer from './components/Footer';
import SettingsModal from './components/SettingsModal';
import ForecastHero from './components/ForecastHero';
import MatchupFactors from './components/MatchupFactors';
import UpcomingLakers from './components/UpcomingLakers';
import MatchupPredictor from './components/MatchupPredictor';
import ScheduleTimeline from './components/ScheduleTimeline';
import ModelHealthView from './components/ModelHealthView';
import { api, getStoredApiUrl } from './api';

const getTeamCode = (nameOrCode) => {
  if (!nameOrCode) return 'LAL';
  const clean = String(nameOrCode).trim();
  if (clean.length === 3) return clean.toUpperCase();
  if (clean.includes('Lakers')) return 'LAL';
  if (clean.includes('Warriors')) return 'GSW';
  if (clean.includes('Celtics')) return 'BOS';
  if (clean.includes('Knicks')) return 'NYK';
  if (clean.includes('Nuggets')) return 'DEN';
  if (clean.includes('Suns')) return 'PHX';
  if (clean.includes('Bucks')) return 'MIL';
  if (clean.includes('Mavericks')) return 'DAL';
  if (clean.includes('Heat')) return 'MIA';
  if (clean.includes('Clippers')) return 'LAC';
  if (clean.includes('76ers')) return 'PHI';
  if (clean.includes('Timberwolves')) return 'MIN';
  if (clean.includes('Thunder')) return 'OKC';
  if (clean.includes('Cavaliers')) return 'CLE';
  if (clean.includes('Kings')) return 'SAC';
  if (clean.includes('Pacers')) return 'IND';
  if (clean.includes('Magic')) return 'ORL';
  if (clean.includes('Rockets')) return 'HOU';
  if (clean.includes('Bulls')) return 'CHI';
  if (clean.includes('Hawks')) return 'ATL';
  if (clean.includes('Nets')) return 'BKN';
  if (clean.includes('Hornets')) return 'CHA';
  if (clean.includes('Pistons')) return 'DET';
  if (clean.includes('Grizzlies')) return 'MEM';
  if (clean.includes('Pelicans')) return 'NOP';
  if (clean.includes('Trail Blazers')) return 'POR';
  if (clean.includes('Spurs')) return 'SAS';
  if (clean.includes('Raptors')) return 'TOR';
  if (clean.includes('Jazz')) return 'UTA';
  if (clean.includes('Wizards')) return 'WAS';
  return clean;
};

export default function App() {
  const [activeTab, setActiveTab] = useState('forecast'); // 'forecast' | 'matchups' | 'schedule' | 'model'
  const [apiUrl, setApiUrl] = useState(getStoredApiUrl());
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [apiStatus, setApiStatus] = useState({ online: false, checking: true, latency: 0, info: null, error: null });

  // Lakers Next Game Prediction State
  const [lakersNext, setLakersNext] = useState({ loading: true, data: null, error: null });

  // Custom Matchup Predictor State
  const [simHome, setSimHome] = useState('LAL');
  const [simAway, setSimAway] = useState('GSW');
  const [simDate, setSimDate] = useState('2026-10-21');
  const [simPersist, setSimPersist] = useState(false);
  const [simLoading, setSimLoading] = useState(false);
  const [simResult, setSimResult] = useState(null);
  const [simError, setSimError] = useState(null);
  const [matchupGames, setMatchupGames] = useState([]);
  const [matchupLoading, setMatchupLoading] = useState(false);

  // Schedule Timeline State
  const [schedTeam, setSchedTeam] = useState('LAL');
  const [schedLimit, setSchedLimit] = useState(20);
  const [schedLoading, setSchedLoading] = useState(false);
  const [schedGames, setSchedGames] = useState([]);
  const [schedError, setSchedError] = useState(null);
  const [lakersUpcomingGames, setLakersUpcomingGames] = useState([]);

  // Model & MLOps State
  const [mlopsLoading, setMlopsLoading] = useState(false);
  const [mlopsHealth, setMlopsHealth] = useState(null);
  const [mlopsDrift, setMlopsDrift] = useState(null);
  const [mlopsRetrain, setMlopsRetrain] = useState(null);
  const [mlopsError, setMlopsError] = useState(null);

  // Connectivity Check
  const checkConnection = async () => {
    setApiStatus(prev => ({ ...prev, checking: true, error: null }));
    const start = performance.now();
    try {
      const data = await api.checkHealth();
      const latency = Math.round(performance.now() - start);
      setApiStatus({ online: true, checking: false, latency, info: data, error: null });
    } catch (err) {
      setApiStatus({ online: false, checking: false, latency: 0, info: null, error: err.message });
    }
  };

  useEffect(() => {
    checkConnection();
  }, [apiUrl]);

  // Fetch Next Lakers Game
  const fetchLakersNext = async () => {
    setLakersNext({ loading: true, data: null, error: null });
    try {
      const data = await api.getLakersNext();
      setLakersNext({ loading: false, data, error: null });
    } catch (err) {
      setLakersNext({ loading: false, data: null, error: err.message });
    }
  };

  // Fetch Lakers upcoming games for short horizon
  const fetchLakersHorizon = async () => {
    try {
      const games = await api.getSchedule('2026-27', 'LAL', 6);
      setLakersUpcomingGames(games || []);
    } catch (err) {
      console.warn("Could not load upcoming Lakers games:", err);
    }
  };

  useEffect(() => {
    fetchLakersNext();
    fetchLakersHorizon();
  }, [apiUrl]);

  // Fetch Full Schedule on tab change or filter change
  const fetchSchedule = async () => {
    setSchedLoading(true);
    setSchedError(null);
    try {
      const data = await api.getSchedule('2026-27', schedTeam, schedLimit);
      setSchedGames(data || []);
    } catch (err) {
      setSchedError(err.message);
    } finally {
      setSchedLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'schedule') {
      fetchSchedule();
    }
  }, [activeTab, schedTeam, schedLimit, apiUrl]);

  // Fetch MLOps Diagnostic Data on Model tab
  const fetchMlopsData = async () => {
    setMlopsLoading(true);
    setMlopsError(null);
    try {
      const [health, drift, retrain] = await Promise.allSettled([
        api.getMonitoringHealth('30d'),
        api.getDriftReport(),
        api.getRetrainingDecision('season')
      ]);
      if (health.status === 'fulfilled') setMlopsHealth(health.value);
      if (drift.status === 'fulfilled') setMlopsDrift(drift.value);
      if (retrain.status === 'fulfilled') setMlopsRetrain(retrain.value);
    } catch (err) {
      setMlopsError(err.message);
    } finally {
      setMlopsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'model') {
      fetchMlopsData();
    }
  }, [activeTab, apiUrl]);

  // Fetch scheduled games when Matchup teams change
  useEffect(() => {
    let isMounted = true;
    if (!simHome || !simAway || simHome === simAway) {
      setMatchupGames([]);
      return;
    }

    const fetchDates = async () => {
      setMatchupLoading(true);
      try {
        const games = await api.getMatchupSchedule(simHome, simAway);
        if (isMounted) {
          const list = games || [];
          setMatchupGames(list);
          if (list.length > 0) {
            const dates = list.map(g => g.game_date);
            if (!dates.includes(simDate)) {
              setSimDate(list[0].game_date);
            }
          } else {
            setSimDate('');
          }
        }
      } catch {
        if (isMounted) setMatchupGames([]);
      } finally {
        if (isMounted) setMatchupLoading(false);
      }
    };

    fetchDates();
    return () => { isMounted = false; };
  }, [simHome, simAway, apiUrl]);

  // Handle Matchup Predict Submission
  const handleSimulate = async (e) => {
    e?.preventDefault();
    if (simHome === simAway) {
      setSimError("Home team and Away team must be distinct.");
      return;
    }
    if (!simDate) {
      setSimError("Please select an official scheduled game date.");
      return;
    }

    setSimLoading(true);
    setSimError(null);
    setSimResult(null);

    try {
      const data = await api.predictMatchup(simHome, simAway, simDate, simPersist);
      setSimResult(data);
    } catch (err) {
      setSimError(err.message || "Prediction request failed.");
    } finally {
      setSimLoading(false);
    }
  };

  // 1-Click Launch from Schedule or Horizon into Matchup Predictor
  const handlePredictGame = async (game) => {
    const home = getTeamCode(game.home_team_code || game.home_team);
    const away = getTeamCode(game.away_team_code || game.away_team);
    const date = game.game_date;

    setSimHome(home);
    setSimAway(away);
    setSimDate(date);
    setSimResult(null);
    setSimError(null);
    setActiveTab('matchups');

    // Automatically trigger prediction for the selected game
    setSimLoading(true);
    try {
      const data = await api.predictMatchup(home, away, date, false);
      setSimResult(data);
    } catch (err) {
      setSimError(err.message || "Failed to load prediction for scheduled game.");
    } finally {
      setSimLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Header
        activeTab={activeTab}
        onTabChange={setActiveTab}
        isOnline={apiStatus.online}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* Main Content Area */}
      <main style={{ maxWidth: '1200px', width: '100%', margin: '0 auto', padding: '32px 24px', flex: 1 }}>
        {/* VIEW 1: FORECAST (HERO) */}
        {activeTab === 'forecast' && (
          <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
            {/* Hero Card */}
            <ForecastHero
              prediction={lakersNext.data}
              loading={lakersNext.loading}
              error={lakersNext.error}
              onRefresh={fetchLakersNext}
              onExploreMatchup={() => {
                if (lakersNext.data) {
                  handlePredictGame({
                    home_team: lakersNext.data.home_team,
                    away_team: lakersNext.data.away_team,
                    game_date: lakersNext.data.game_date
                  });
                } else {
                  setActiveTab('matchups');
                }
              }}
            />

            {/* Factors Reflected in Prediction */}
            {lakersNext.data && (
              <MatchupFactors prediction={lakersNext.data} />
            )}

            {/* Short Upcoming Horizon */}
            <UpcomingLakers
              games={lakersUpcomingGames}
              onSelectGame={handlePredictGame}
              currentPredictionDate={lakersNext.data?.game_date}
            />
          </div>
        )}

        {/* VIEW 2: MATCHUPS */}
        {activeTab === 'matchups' && (
          <MatchupPredictor
            simHome={simHome}
            setSimHome={setSimHome}
            simAway={simAway}
            setSimAway={setSimAway}
            simDate={simDate}
            setSimDate={setSimDate}
            simPersist={simPersist}
            setSimPersist={setSimPersist}
            simLoading={simLoading}
            simResult={simResult}
            simError={simError}
            onSimulate={handleSimulate}
            matchupGames={matchupGames}
            matchupLoading={matchupLoading}
          />
        )}

        {/* VIEW 3: SCHEDULE */}
        {activeTab === 'schedule' && (
          <ScheduleTimeline
            games={schedGames}
            loading={schedLoading}
            error={schedError}
            selectedTeam={schedTeam}
            onTeamChange={setSchedTeam}
            limit={schedLimit}
            onLimitChange={setSchedLimit}
            onPredictGame={handlePredictGame}
          />
        )}

        {/* VIEW 4: MODEL & ENGINEERING */}
        {activeTab === 'model' && (
          <ModelHealthView
            healthData={mlopsHealth}
            driftData={mlopsDrift}
            retrainData={mlopsRetrain}
            loading={mlopsLoading}
            error={mlopsError}
            onRefresh={fetchMlopsData}
          />
        )}
      </main>

      {/* Footer */}
      <Footer onOpenModelTab={() => setActiveTab('model')} />

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        apiStatus={apiStatus}
        onRecheck={checkConnection}
      />
    </div>
  );
}
