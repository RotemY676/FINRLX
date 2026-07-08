// Universe browser — data

const UNIVERSES = [
  { id: "us-lc-500",  name: "US-LargeCap-500",  count: 500, active: true,  updated: "2h ago",  owner: "Rivka",   desc: "Top 500 by market cap, ADV ≥ $50M" },
  { id: "us-semis",   name: "US-Semis-focused", count: 42,  active: false, updated: "3d ago",  owner: "Rivka",   desc: "GICS 4530 + custom adds" },
  { id: "eu-lc-200",  name: "EU-LargeCap-200",  count: 200, active: false, updated: "1w ago",  owner: "Yoav",    desc: "STOXX 600 subset, EUR-hedged" },
  { id: "us-smid",    name: "US-SMID-cap",      count: 850, active: false, updated: "6d ago",  owner: "Rivka",   desc: "$2B–$20B mkt cap" },
  { id: "global-ai",  name: "Global-AI-thematic", count: 68, active: false, updated: "1d ago", owner: "Team",    desc: "Custom thematic, LLM-tagged" },
];

const FACTORS = ["Momentum", "Value", "Quality", "Low-vol", "Size", "Growth"];

// 22 sample constituents, pre-computed factor z-scores
const CONSTITUENTS = [
  { tk: "NVDA",  name: "NVIDIA",          sector: "Semis",      mcap: 3120, adv: 28.4, liq: "high",  beta: 1.67, f: { Momentum: 2.8, Value: -1.9, Quality: 1.4, "Low-vol": -1.8, Size: 2.9, Growth: 2.6 }, inBasket: true },
  { tk: "AAPL",  name: "Apple",           sector: "Hardware",   mcap: 3380, adv: 19.2, liq: "high",  beta: 1.18, f: { Momentum: 0.6, Value: -0.4, Quality: 2.1, "Low-vol": 0.3,  Size: 2.9, Growth: 0.7 }, inBasket: true },
  { tk: "MSFT",  name: "Microsoft",       sector: "Software",   mcap: 3210, adv: 15.8, liq: "high",  beta: 1.02, f: { Momentum: 1.1, Value: -0.2, Quality: 2.4, "Low-vol": 0.8,  Size: 2.9, Growth: 1.4 }, inBasket: true },
  { tk: "GOOGL", name: "Alphabet",        sector: "Comm Svc",   mcap: 2480, adv: 14.1, liq: "high",  beta: 1.09, f: { Momentum: 0.9, Value: 0.3,  Quality: 1.8, "Low-vol": 0.4,  Size: 2.7, Growth: 1.1 }, inBasket: true },
  { tk: "META",  name: "Meta",            sector: "Comm Svc",   mcap: 1540, adv: 11.9, liq: "high",  beta: 1.28, f: { Momentum: 1.8, Value: 0.1,  Quality: 1.6, "Low-vol": -0.3, Size: 2.5, Growth: 1.7 }, inBasket: true },
  { tk: "AVGO",  name: "Broadcom",        sector: "Semis",      mcap:  880, adv:  6.8, liq: "high",  beta: 1.42, f: { Momentum: 2.4, Value: -0.8, Quality: 1.9, "Low-vol": -1.1, Size: 2.3, Growth: 1.9 }, inBasket: true },
  { tk: "TSLA",  name: "Tesla",           sector: "Auto",       mcap:  740, adv: 18.4, liq: "high",  beta: 2.14, f: { Momentum: 0.2, Value: -2.3, Quality: 0.4, "Low-vol": -2.8, Size: 2.2, Growth: 0.9 }, inBasket: true },
  { tk: "AMD",   name: "AMD",             sector: "Semis",      mcap:  280, adv:  8.1, liq: "high",  beta: 1.84, f: { Momentum: 1.3, Value: -1.4, Quality: 0.8, "Low-vol": -2.1, Size: 1.9, Growth: 1.6 }, inBasket: true },
  { tk: "ANET",  name: "Arista Networks", sector: "Networking", mcap:  145, adv:  1.2, liq: "med",   beta: 1.38, f: { Momentum: 1.9, Value: -0.6, Quality: 2.2, "Low-vol": -0.9, Size: 1.4, Growth: 1.8 }, inBasket: true },
  { tk: "CRWD",  name: "CrowdStrike",     sector: "Software",   mcap:   85, adv:  1.4, liq: "med",   beta: 1.46, f: { Momentum: 1.1, Value: -1.8, Quality: 1.4, "Low-vol": -1.3, Size: 1.1, Growth: 2.2 }, inBasket: true },
  { tk: "JPM",   name: "JPMorgan",        sector: "Financials", mcap:  620, adv:  8.9, liq: "high",  beta: 1.11, f: { Momentum: 0.7, Value: 0.9,  Quality: 1.4, "Low-vol": 0.7,  Size: 2.1, Growth: 0.3 }, inBasket: false },
  { tk: "V",     name: "Visa",            sector: "Financials", mcap:  520, adv:  5.1, liq: "high",  beta: 0.92, f: { Momentum: 0.4, Value: -0.3, Quality: 2.3, "Low-vol": 1.2,  Size: 2.0, Growth: 0.8 }, inBasket: false },
  { tk: "UNH",   name: "UnitedHealth",    sector: "Healthcare", mcap:  480, adv:  4.2, liq: "high",  beta: 0.74, f: { Momentum: -0.8,Value: 0.6,  Quality: 1.7, "Low-vol": 1.6,  Size: 1.9, Growth: 0.2 }, inBasket: false },
  { tk: "XOM",   name: "Exxon Mobil",     sector: "Energy",     mcap:  460, adv:  6.1, liq: "high",  beta: 0.84, f: { Momentum: -0.4,Value: 1.4,  Quality: 1.1, "Low-vol": 1.1,  Size: 1.9, Growth: -0.4 }, inBasket: false },
  { tk: "PG",    name: "Procter & Gamble",sector: "Staples",    mcap:  390, adv:  3.3, liq: "high",  beta: 0.58, f: { Momentum: -0.2,Value: 0.2,  Quality: 1.9, "Low-vol": 2.1,  Size: 1.8, Growth: -0.3 }, inBasket: false },
  { tk: "KO",    name: "Coca-Cola",       sector: "Staples",    mcap:  290, adv:  2.4, liq: "high",  beta: 0.51, f: { Momentum: -0.3,Value: 0.3,  Quality: 1.8, "Low-vol": 2.3,  Size: 1.6, Growth: -0.5 }, inBasket: false },
  { tk: "CAT",   name: "Caterpillar",     sector: "Industrials",mcap:  180, adv:  2.1, liq: "high",  beta: 1.24, f: { Momentum: 0.3, Value: 0.8,  Quality: 1.2, "Low-vol": 0.1,  Size: 1.5, Growth: 0.4 }, inBasket: false },
  { tk: "BA",    name: "Boeing",          sector: "Industrials",mcap:  130, adv:  3.4, liq: "high",  beta: 1.62, f: { Momentum: -1.4,Value: -0.9, Quality: -0.6, "Low-vol": -1.7,Size: 1.4, Growth: -0.8 }, inBasket: false },
  { tk: "NEE",   name: "NextEra Energy",  sector: "Utilities",  mcap:  160, adv:  1.8, liq: "med",   beta: 0.62, f: { Momentum: -0.6,Value: 0.4,  Quality: 1.3, "Low-vol": 1.9,  Size: 1.4, Growth: 0.1 }, inBasket: false },
  { tk: "CVX",   name: "Chevron",         sector: "Energy",     mcap:  290, adv:  3.9, liq: "high",  beta: 1.01, f: { Momentum: -0.3,Value: 1.1,  Quality: 1.0, "Low-vol": 0.9,  Size: 1.7, Growth: -0.6 }, inBasket: false },
  { tk: "BAC",   name: "Bank of America", sector: "Financials", mcap:  340, adv:  6.8, liq: "high",  beta: 1.32, f: { Momentum: 0.6, Value: 1.2,  Quality: 0.8, "Low-vol": 0.2,  Size: 1.7, Growth: 0.1 }, inBasket: false },
  { tk: "AMZN",  name: "Amazon",          sector: "Discretionary",mcap:1810,adv: 16.4, liq: "high",  beta: 1.22, f: { Momentum: 1.0, Value: -0.7, Quality: 1.6, "Low-vol": 0.1,  Size: 2.4, Growth: 1.5 }, inBasket: false },
];

const FILTER_DEFAULTS = {
  minMcap: 50,        // $B
  minADV: 1.0,        // $M daily
  liqMin: "med",      // low|med|high
  sectors: [],        // empty = all
  basketOnly: false,
};

Object.assign(window, { UNIVERSES, FACTORS, CONSTITUENTS, FILTER_DEFAULTS });
