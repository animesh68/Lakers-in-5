/**
 * Deterministic Player Metadata & Verified Headshot Resolution
 * Strictly enforces asset separation:
 * - Player Profile Headshots: Official individual NBA headshot CDN (or neutral silhouette)
 * - Footer Slideshow Assets: Reserved exclusively for the footer slideshow
 * - NEVER maps editorial, hero, meme, or footer assets to player headshots
 */

import { FOOTER_SLIDES } from './footerSlides';

// Explicit set of footer slideshow image assets
const FOOTER_ASSET_PATHS = new Set(
  Array.isArray(FOOTER_SLIDES) ? FOOTER_SLIDES.map(s => s.image) : []
);

/**
 * Validates whether a given asset path or URL belongs to the footer slideshow,
 * hero video/photo collection, or editorial meme directory.
 */
export function isFooterSlideAsset(url) {
  if (!url || typeof url !== 'string') return false;
  const clean = url.trim().toLowerCase();
  
  if (FOOTER_ASSET_PATHS.has(url.trim())) return true;
  if (clean.startsWith('/imgs/') || clean.startsWith('imgs/')) return true;
  if (clean.startsWith('/hero/') || clean.startsWith('hero/')) return true;
  if (clean.includes('luka77') || clean.includes('ar15') || clean.includes('jake12') || clean.includes('kessler_lal')) return true;
  return false;
}

/**
 * Resolves a verified individual NBA player headshot URL.
 * Only returns a URL for authentic numeric NBA person IDs.
 * Under NO circumstances will this ever return a footer image, editorial photo, or placeholder image.
 */
export function getVerifiedPlayerHeadshotUrl(player) {
  if (!player) return null;
  const idStr = String(player.player_id || '').trim();
  
  // NBA person IDs are pure numeric strings of 3 to 10 digits
  // Synthetic IDs (e.g. 'R-0123456') or invalid identifiers return null to trigger neutral silhouette
  if (/^\d{3,10}$/.test(idStr)) {
    const headshotUrl = `https://cdn.nba.com/headshots/nba/latest/260x190/${idStr}.png`;
    if (!isFooterSlideAsset(headshotUrl)) {
      return headshotUrl;
    }
  }
  return null;
}

/**
 * Verified player positions, jersey numbers, and canonical display names.
 * Contains ZERO image paths to strictly prevent footer asset leakage.
 */
export const KNOWN_PLAYER_MAP = {
  // Luka Dončić
  '1629029': {
    position: 'Guard',
    jersey: '#77',
    displayName: 'LUKA DONČIĆ',
    team: 'Los Angeles Lakers',
    teamCode: 'LAL'
  },
  // Austin Reaves
  '1630559': {
    position: 'Guard',
    jersey: '#15',
    displayName: 'AUSTIN REAVES',
    team: 'Los Angeles Lakers',
    teamCode: 'LAL'
  },
  // Walker Kessler
  '1631117': {
    position: 'Center',
    jersey: '#24',
    displayName: 'WALKER KESSLER',
    team: 'Los Angeles Lakers',
    teamCode: 'LAL'
  },
  // Collin Sexton
  '1629012': {
    position: 'Guard',
    jersey: '#2',
    displayName: 'COLLIN SEXTON',
    team: 'Los Angeles Lakers',
    teamCode: 'LAL'
  },
  // Jake LaRavia
  '1631222': {
    position: 'Forward',
    jersey: '#12',
    displayName: 'JAKE LARAVIA',
    team: 'Los Angeles Lakers',
    teamCode: 'LAL'
  },
  // Quentin Grimes
  '1629656': {
    position: 'Guard',
    jersey: '#5',
    displayName: 'QUENTIN GRIMES',
    team: 'Los Angeles Lakers',
    teamCode: 'LAL'
  },
  // Ziaire Williams
  '1630533': {
    position: 'Forward',
    jersey: '#8',
    displayName: 'ZIAIRE WILLIAMS',
    team: 'Los Angeles Lakers',
    teamCode: 'LAL'
  },
  // Jarred Vanderbilt
  '1629020': {
    position: 'Forward',
    jersey: '#2',
    displayName: 'JARRED VANDERBILT',
    team: 'Los Angeles Lakers',
    teamCode: 'LAL'
  },
  // Dalton Knecht
  '1642261': {
    position: 'Forward',
    jersey: '#4',
    displayName: 'DALTON KNECHT',
    team: 'Los Angeles Lakers',
    teamCode: 'LAL'
  },
  // Kevon Looney
  '1626172': {
    position: 'Center',
    jersey: '#5',
    displayName: 'KEVON LOONEY',
    team: 'Los Angeles Lakers',
    teamCode: 'LAL'
  },
  // Maxi Kleber
  '1628467': {
    position: 'Forward',
    jersey: '#42',
    displayName: 'MAXI KLEBER',
    team: 'Los Angeles Lakers',
    teamCode: 'LAL'
  },
  // Jaden Hardy
  '1630702': {
    position: 'Guard',
    jersey: '#1',
    displayName: 'JADEN HARDY',
    team: 'Los Angeles Lakers',
    teamCode: 'LAL'
  },
  // Matisse Thybulle
  '1629680': {
    position: 'Guard-Forward',
    jersey: '#0',
    displayName: 'MATISSE THYBULLE',
    team: 'Los Angeles Lakers',
    teamCode: 'LAL'
  },
  // Sandro Mamukelashvili
  '1630572': {
    position: 'Forward-Center',
    jersey: '#54',
    displayName: 'SANDRO MAMUKELASHVILI',
    team: 'Los Angeles Lakers',
    teamCode: 'LAL'
  },
  // Nick Smith Jr.
  '1641733': {
    position: 'Guard',
    jersey: '#0',
    displayName: 'NICK SMITH JR.',
    team: 'Los Angeles Lakers',
    teamCode: 'LAL'
  }
};

const NAME_TO_ID = {
  'luka doncic': '1629029',
  'luka dončić': '1629029',
  'austin reaves': '1630559',
  'walker kessler': '1631117',
  'collin sexton': '1629012',
  'jake laravia': '1631222',
  'quentin grimes': '1629656',
  'ziaire williams': '1630533',
  'jarred vanderbilt': '1629020',
  'dalton knecht': '1642261',
  'kevon looney': '1626172',
  'maxi kleber': '1628467',
  'jaden hardy': '1630702',
  'matisse thybulle': '1629680',
  'sandro mamukelashvili': '1630572',
  'nick smith jr.': '1641733',
  'nick smith jr': '1641733'
};

/**
 * Deterministically resolves player metadata: position, jersey number, canonical display name,
 * and verified headshot URL.
 * Never supplies or returns a footer slideshow asset.
 */
export function getPlayerMeta(player) {
  if (!player) return null;

  const idStr = String(player.player_id || '').trim();
  const normName = String(player.player_name || '').toLowerCase().trim();

  let baseMeta = null;
  if (KNOWN_PLAYER_MAP[idStr]) {
    baseMeta = KNOWN_PLAYER_MAP[idStr];
  } else {
    const matchedId = NAME_TO_ID[normName];
    if (matchedId && KNOWN_PLAYER_MAP[matchedId]) {
      baseMeta = KNOWN_PLAYER_MAP[matchedId];
    }
  }

  const verifiedHeadshot = getVerifiedPlayerHeadshotUrl(player);

  return {
    position: baseMeta?.position || player.position || 'Rotation',
    jersey: baseMeta?.jersey || (player.jersey_number ? `#${player.jersey_number}` : null),
    displayName: baseMeta?.displayName || (player.player_name ? player.player_name.toUpperCase() : 'PLAYER'),
    team: baseMeta?.team || player.team || 'NBA Team',
    teamCode: baseMeta?.teamCode || player.team_code || 'NBA',
    player_name: player.player_name,
    player_id: idStr,
    headshotUrl: verifiedHeadshot,
    image: null // Explicitly null to enforce separation from footer slideshow
  };
}
