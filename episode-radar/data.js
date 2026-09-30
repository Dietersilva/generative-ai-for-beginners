'use strict';

// Catalog data for Episode Radar: services, which service carries each sports
// channel, and the memberships, phone plans and cards that include streaming.
// These facts change often. Every network rule and perk carries a source, and
// `checked` is the date they were last verified. Review this file every month.
window.EPISODE_RADAR_DATA = (() => {
  const services = [
    { id: 'netflix', label: 'Netflix', names: ['netflix'], hosts: ['netflix.com'], home: 'https://www.netflix.com/' },
    { id: 'hulu', label: 'Hulu', names: ['hulu'], hosts: ['hulu.com'], home: 'https://www.hulu.com/' },
    { id: 'prime', label: 'Prime Video', names: ['prime video', 'amazon prime video', 'amazon prime', 'amazon video'], hosts: ['primevideo.com', 'amazon.com'], home: 'https://www.primevideo.com/' },
    { id: 'hbomax', label: 'HBO Max', names: ['hbo max', 'max'], hosts: ['hbomax.com', 'max.com'], home: 'https://www.hbomax.com/',
      tiers: ['basic', 'standard', 'premium'], tierLabels: { basic: 'Basic with Ads', standard: 'Standard', premium: 'Premium' } },
    { id: 'disney', label: 'Disney+', names: ['disney+'], hosts: ['disneyplus.com'], home: 'https://www.disneyplus.com/' },
    { id: 'appletv', label: 'Apple TV', names: ['apple tv+', 'apple tv'], hosts: ['tv.apple.com'], home: 'https://tv.apple.com/' },
    { id: 'paramount', label: 'Paramount+', names: ['paramount+', 'cbs all access'], hosts: ['paramountplus.com'], home: 'https://www.paramountplus.com/' },
    { id: 'peacock', label: 'Peacock', names: ['peacock', 'peacock premium'], hosts: ['peacocktv.com'], home: 'https://www.peacocktv.com/' },
    { id: 'espn', label: 'ESPN', names: ['espn+', 'espn'], hosts: ['espn.com'], home: 'https://plus.espn.com/',
      tiers: ['select', 'unlimited'], tierLabels: { select: 'ESPN Select', unlimited: 'ESPN Unlimited' } },
    { id: 'foxone', label: 'Fox One', names: ['fox one'], hosts: ['fox.com'], home: 'https://www.fox.com/' },
    { id: 'youtube', label: 'YouTube', names: ['youtube'], hosts: ['youtube.com'], home: 'https://www.youtube.com/', free: true },
  ];

  // US sports channels as listings print them, lower-cased. `tier` is the
  // lowest plan that includes live games; `antenna` means free over the air.
  const networks = [
    { names: ['cbs'], service: 'paramount', antenna: true, note: 'Paramount+ streams the CBS game in your local market.', source: 'https://www.cabletv.com/paramount-plus/review/nfl' },
    { names: ['paramount+', 'paramount plus'], service: 'paramount', source: 'https://www.cabletv.com/paramount-plus/review/nfl' },
    { names: ['nbc'], service: 'peacock', antenna: true, note: 'Peacock Premium simulcasts NBC games.', source: 'https://www.nbc.com/nbc-insider/nfl-sunday-night-football-schedule-2026-2027' },
    { names: ['peacock'], service: 'peacock', source: 'https://www.cabletv.com/peacock/nfl' },
    { names: ['fox'], service: 'foxone', antenna: true, note: 'Fox One streams FOX and FS1.', source: 'https://en.wikipedia.org/wiki/Fox_One' },
    { names: ['fs1', 'fox sports 1', 'fs2', 'fox sports 2', 'fox one'], service: 'foxone', source: 'https://en.wikipedia.org/wiki/Fox_One' },
    { names: ['abc', 'espn on abc'], service: 'espn', tier: 'unlimited', antenna: true, note: 'ESPN Unlimited includes ESPN on ABC.', source: 'https://www.antennaland.com/espn-unlimited-vs-espn-select/' },
    { names: ['espn', 'espn2', 'espnu', 'espnews', 'espn deportes', 'sec network', 'acc network'], service: 'espn', tier: 'unlimited', note: 'The ESPN TV channels need ESPN Unlimited.', source: 'https://support.espn.com/hc/en-us/articles/40375339514260-What-is-ESPN-Unlimited' },
    { names: ['espn+', 'espn plus'], service: 'espn', tier: 'select', source: 'https://www.antennaland.com/espn-unlimited-vs-espn-select/' },
    { names: ['tnt', 'tbs', 'trutv', 'tru tv', 'tnt sports'], service: 'hbomax', tier: 'standard', note: 'Live sports need HBO Max Standard or Premium, not Basic with Ads.', source: 'https://www.hbomax.com/sports' },
    { names: ['prime video', 'amazon prime video', 'amazon prime'], service: 'prime', source: 'https://www.howtogeek.com/where-to-stream-every-nfl-game-2026-2027-season/' },
    { names: ['netflix'], service: 'netflix', source: 'https://www.howtogeek.com/where-to-stream-every-nfl-game-2026-2027-season/' },
    { names: ['apple tv', 'apple tv+'], service: 'appletv' },
    { names: ['youtube'], service: 'youtube' },
  ];

  // What people may already have. `grants` gives access to a service (at a
  // tier when it matters for sports); `networks` covers channels directly;
  // `credit` pays back part of a bill. `options` are mutually exclusive choices.
  const perks = [
    { id: 'antenna', label: 'TV antenna', detail: 'Free local CBS, NBC, FOX and ABC, including their games.',
      networks: ['cbs', 'nbc', 'fox', 'abc', 'espn on abc'] },
    { id: 'livetv', label: 'Cable or a live TV service', detail: 'YouTube TV, Hulu + Live TV, Sling, Fubo or cable usually include ESPN, TNT, FOX, FS1 and the local networks. Packages differ, so check yours.',
      networks: ['cbs', 'nbc', 'fox', 'abc', 'espn on abc', 'espn', 'espn2', 'espnu', 'espnews', 'sec network', 'acc network', 'tnt', 'tbs', 'trutv', 'tru tv', 'tnt sports', 'fs1', 'fox sports 1', 'fs2', 'fox sports 2', 'nfl network', 'nba tv', 'mlb network', 'nhl network'] },
    { id: 'amazon', label: 'Amazon Prime', detail: 'Prime Video with ads.',
      grants: [{ service: 'prime' }], source: 'https://variety.com/2026/streaming/news/amazon-prime-video-ultra-no-ads-price-increase-1236687124/' },
    { id: 'walmart', label: 'Walmart+', detail: 'One of Peacock Premium or Paramount+ Essential, with ads. You can switch every 90 days.',
      options: [
        { id: 'peacock', label: 'Peacock chosen', grants: [{ service: 'peacock' }] },
        { id: 'paramount', label: 'Paramount+ chosen', grants: [{ service: 'paramount' }] },
      ], source: 'https://corporate.walmart.com/news/2025/09/01/walmart-plus-celebrates-5th-anniversary-with-expanded-video-streaming-choices' },
    { id: 'instacart', label: 'Instacart+', detail: 'Peacock Premium.',
      grants: [{ service: 'peacock' }], source: 'https://www.kiplinger.com/personal-finance/online-shopping/instacart-users-can-now-get-peacock-streaming-for-free' },
    { id: 'tmobile', label: 'T-Mobile', detail: 'Experience More includes Netflix and Apple TV; Experience Beyond adds Hulu.',
      options: [
        { id: 'more', label: 'Experience More', grants: [{ service: 'netflix' }, { service: 'appletv' }] },
        { id: 'beyond', label: 'Experience Beyond', grants: [{ service: 'netflix' }, { service: 'appletv' }, { service: 'hulu' }] },
      ], source: 'https://www.hollywoodreporter.com/lifestyle/lifestyle-news/best-t-mobile-streaming-deal-plans-free-netflix-hulu-apple-tv-1236419303/' },
    { id: 'verizon-disney', label: 'Verizon perk: Disney bundle', detail: 'Disney+, Hulu and ESPN Select, a $10 a month add-on.',
      grants: [{ service: 'disney' }, { service: 'hulu' }, { service: 'espn', tier: 'select' }], source: 'https://www.verizon.com/support/disney-bundle-faqs/' },
    { id: 'verizon-netflix-max', label: 'Verizon perk: Netflix and HBO Max', detail: 'Both with ads, a $13 a month add-on. HBO Max Basic with Ads has no live sports.',
      grants: [{ service: 'netflix' }, { service: 'hbomax', tier: 'basic' }], source: 'https://tech.yahoo.com/streaming/deals/articles/taking-advantage-verizons-streaming-perks-193051718.html' },
    { id: 'spotify-student', label: 'Spotify Premium Student', detail: 'Hulu with ads.',
      grants: [{ service: 'hulu' }], source: 'https://www.spotify.com/us/student/' },
    { id: 'chase-reserve', label: 'Chase Sapphire Reserve', detail: 'Apple TV and Apple Music, through June 22, 2027.',
      grants: [{ service: 'appletv' }], source: 'https://www.chase.com/personal/credit-cards/education/rewards-benefits/apple-tv-and-chase-sapphire-reserve-credit-card' },
    { id: 'amex-platinum', label: 'Amex Platinum', detail: 'Up to $25 a month back on Disney+, Hulu, ESPN, Paramount+, Peacock and a few others.',
      credit: { cents: 2500, services: ['disney', 'hulu', 'espn', 'paramount', 'peacock'] }, source: 'https://global.americanexpress.com/card-benefits/detail/digital-entertainment/platinum' },
  ];

  const deepFreeze = (o) => {
    for (const v of Object.values(o)) if (v && typeof v === 'object') deepFreeze(v);
    return Object.freeze(o);
  };
  return deepFreeze({ checked: '2026-09-30', services, networks, perks });
})();
