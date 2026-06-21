const CARD_TAG = "windguru-dashboard";

class WindguruDashboard extends HTMLElement {
  static getStubConfig() {
    return {
      title: "Talamone",
      direction_entity: "sensor.talamone_wind_direction",
      average_entity: "sensor.talamone_wind_average",
      gust_entity: "sensor.talamone_wind_gust",
      temperature_entity: "sensor.talamone_temperature",
      max_speed: 40,
    };
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
  }

  setConfig(config) {
    this.config = { ...WindguruDashboard.getStubConfig(), ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 5;
  }

  getGridOptions() {
    return {
      columns: "full",
      rows: "auto",
      min_columns: 6,
    };
  }

  _number(entityId) {
    const value = Number.parseFloat(this._hass?.states?.[entityId]?.state);
    return Number.isFinite(value) ? value : null;
  }

  _directionLabel(degrees) {
    if (degrees === null) return "—";
    const labels = [
      "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
      "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO",
    ];
    return labels[Math.round((((degrees % 360) + 360) % 360) / 22.5) % 16];
  }

  _gaugePoint(value, maximum, radius) {
    const ratio = Math.max(0, Math.min(value / maximum, 1));
    const angle = Math.PI - ratio * Math.PI;
    return {
      x: 150 + radius * Math.cos(angle),
      y: 150 - radius * Math.sin(angle),
      ratio,
    };
  }

  _escape(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  _render() {
    if (!this.config || !this.shadowRoot) return;

    const direction = this._number(this.config.direction_entity);
    const average = this._number(this.config.average_entity);
    const gust = this._number(this.config.gust_entity);
    const temperature = this._number(this.config.temperature_entity);
    const requestedMax = Number(this.config.max_speed) || 40;
    const observed = Math.max(average || 0, gust || 0);
    const maximum = Math.max(10, requestedMax, Math.ceil(observed / 10) * 10);
    const averagePoint = this._gaugePoint(average || 0, maximum, 110);
    const gustInner = this._gaugePoint(gust || 0, maximum, 88);
    const gustOuter = this._gaugePoint(gust || 0, maximum, 124);
    const normalizedDirection =
      direction === null ? 0 : ((direction % 360) + 360) % 360;
    const directionText =
      direction === null ? "—" : `${Math.round(normalizedDirection)}°`;
    const averageText = average === null ? "—" : average.toFixed(1);
    const gustText = gust === null ? "—" : gust.toFixed(1);
    const temperatureText = temperature === null ? "—" : temperature.toFixed(1);
    const title = this._escape(this.config.title || "Talamone");
    const ticks = Array.from({ length: 24 }, (_, index) => {
      const angle = index * 15;
      const major = index % 6 === 0;
      return `<line x1="120" y1="${major ? 21 : 24}" x2="120"
        y2="${major ? 34 : 30}" stroke="rgba(190,229,247,${major ? ".7" : ".32"})"
        stroke-width="${major ? 2 : 1}" transform="rotate(${angle} 120 120)"/>`;
    }).join("");

    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        ha-card {
          overflow: hidden; color: #f7fbff;
          background: radial-gradient(circle at 12% 5%, rgba(62,194,255,.26), transparent 34%),
            linear-gradient(145deg, #102c46 0%, #0b2035 58%, #071725 100%);
          border: 1px solid rgba(124,207,255,.18);
          box-shadow: 0 12px 32px rgba(1,16,29,.28);
        }
        .header { display:flex; justify-content:space-between; align-items:center; padding:20px 22px 6px; }
        .eyebrow { color:#78d8ff; font-size:11px; font-weight:750; letter-spacing:.18em; text-transform:uppercase; }
        h2 { margin:3px 0 0; font-size:25px; letter-spacing:-.02em; }
        .live { display:flex; align-items:center; gap:7px; color:#b9d7e8; font-size:11px; font-weight:700; letter-spacing:.12em; }
        .live::before { width:8px; height:8px; content:""; border-radius:50%; background:#48e0a4; box-shadow:0 0 0 5px rgba(72,224,164,.12); }
        .layout { display:grid; grid-template-columns:minmax(210px,.9fr) minmax(270px,1.25fr); gap:14px; padding:12px 18px 18px; }
        .panel { position:relative; border:1px solid rgba(156,218,248,.13); border-radius:20px; background:rgba(255,255,255,.045); cursor:pointer; transition:.2s ease; }
        .panel:hover { background:rgba(255,255,255,.075); transform:translateY(-1px); }
        .compass { min-height:286px; padding:14px; text-align:center; }
        .compass svg { width:min(230px,100%); height:auto; }
        .compass-meta { margin-top:-3px; }
        .direction { font-size:27px; font-weight:760; }
        .direction span { color:#76d8ff; }
        .caption { color:#90adc0; font-size:11px; letter-spacing:.13em; text-transform:uppercase; }
        .right { display:grid; grid-template-rows:1fr auto; gap:14px; }
        .gauge { min-height:215px; padding:10px 16px 14px; text-align:center; }
        .gauge svg { width:min(330px,100%); height:auto; margin-top:1px; }
        .gauge-value { margin-top:-64px; font-size:42px; font-weight:780; letter-spacing:-.04em; }
        .gauge-value small { margin-left:4px; color:#91b3c6; font-size:15px; letter-spacing:0; }
        .wind-label { color:#8ba9bb; font-size:11px; font-weight:700; letter-spacing:.13em; text-transform:uppercase; }
        .gust-row { display:flex; justify-content:center; margin-top:13px; }
        .gust-pill { display:inline-flex; gap:8px; align-items:center; padding:7px 12px; border:1px solid rgba(255,166,64,.3); border-radius:999px; color:#ffd3a1; background:rgba(255,139,45,.11); font-size:12px; }
        .gust-pill b { color:#fff; font-size:15px; }
        .temperature { display:flex; align-items:center; justify-content:space-between; min-height:76px; padding:13px 18px; }
        .temp-left { display:flex; gap:12px; align-items:center; }
        .thermometer { display:grid; width:42px; height:42px; place-items:center; border-radius:14px; color:#ffbc66; background:rgba(255,172,67,.12); font-size:24px; }
        .temp-value { font-size:30px; font-weight:760; }
        .temp-value small { color:#9db7c7; font-size:15px; }
        .scale { fill:#7f9daf; font:11px sans-serif; }
        @media (max-width:560px) { .layout { grid-template-columns:1fr; } .compass { min-height:260px; } }
      </style>
      <ha-card>
        <div class="header">
          <div><div class="eyebrow">Wind station</div><h2>${title}</h2></div>
          <div class="live">LIVE</div>
        </div>
        <div class="layout">
          <div class="panel compass" data-entity="${this._escape(this.config.direction_entity)}">
            <svg viewBox="0 0 240 240" aria-label="Direzione del vento ${directionText}">
              <circle cx="120" cy="120" r="98" fill="none" stroke="rgba(139,205,237,.18)" stroke-width="2"/>
              <circle cx="120" cy="120" r="77" fill="rgba(3,20,34,.26)" stroke="rgba(139,205,237,.09)"/>
              ${ticks}
              <g fill="#c7e5f4" font-family="sans-serif" font-size="13" font-weight="700" text-anchor="middle">
                <text x="120" y="18" fill="#ffac60">N</text><text x="225" y="125">E</text>
                <text x="120" y="235">S</text><text x="15" y="125">O</text>
              </g>
              <g transform="rotate(${normalizedDirection} 120 120)" style="transition:transform .7s cubic-bezier(.2,.8,.2,1)">
                <path d="M120 41 L108 119 L120 109 L132 119 Z" fill="#ff9e4a"/>
                <path d="M120 199 L108 119 L120 130 L132 119 Z" fill="#d9f2ff" opacity=".86"/>
              </g>
              <circle cx="120" cy="120" r="8" fill="#0b2438" stroke="#edfaff" stroke-width="3"/>
            </svg>
            <div class="compass-meta">
              <div class="direction"><span>${this._directionLabel(direction)}</span> ${directionText}</div>
              <div class="caption">Direzione del vento</div>
            </div>
          </div>
          <div class="right">
            <div class="panel gauge" data-entity="${this._escape(this.config.average_entity)}">
              <svg viewBox="0 0 300 180" aria-label="Vento medio ${averageText} nodi, raffica ${gustText} nodi">
                <defs><linearGradient id="wind-gradient" x1="0" x2="1">
                  <stop offset="0" stop-color="#40d7b0"/><stop offset=".55" stop-color="#3cb9f2"/><stop offset="1" stop-color="#7a75ff"/>
                </linearGradient></defs>
                <path d="M40 150 A110 110 0 0 1 260 150" fill="none" stroke="rgba(139,205,237,.14)" stroke-width="20" stroke-linecap="round" pathLength="100"/>
                <path d="M40 150 A110 110 0 0 1 260 150" fill="none" stroke="url(#wind-gradient)" stroke-width="20" stroke-linecap="round" pathLength="100" stroke-dasharray="${averagePoint.ratio * 100} 100" style="transition:stroke-dasharray .7s ease"/>
                <line x1="${gustInner.x}" y1="${gustInner.y}" x2="${gustOuter.x}" y2="${gustOuter.y}" stroke="#ff9e4a" stroke-width="6" stroke-linecap="round" style="transition:all .7s ease"/>
                <circle cx="${gustOuter.x}" cy="${gustOuter.y}" r="5" fill="#ff9e4a"/>
                <text x="34" y="169" class="scale">0</text><text x="250" y="169" class="scale">${maximum}</text>
              </svg>
              <div class="gauge-value">${averageText}<small>kn</small></div>
              <div class="wind-label">Vento medio</div>
              <div class="gust-row"><div class="gust-pill">Raffica <b>${gustText} kn</b></div></div>
            </div>
            <div class="panel temperature" data-entity="${this._escape(this.config.temperature_entity)}">
              <div class="temp-left"><div class="thermometer"><ha-icon icon="mdi:thermometer"></ha-icon></div><div><div class="caption">Temperatura esterna</div><div class="temp-value">${temperatureText}<small> °C</small></div></div></div>
              <div class="caption">Talamone</div>
            </div>
          </div>
        </div>
      </ha-card>`;

    this.shadowRoot.querySelectorAll("[data-entity]").forEach((element) => {
      element.addEventListener("click", () => {
        const event = new Event("hass-more-info", { bubbles: true, composed: true });
        event.detail = { entityId: element.dataset.entity };
        this.dispatchEvent(event);
      });
    });
  }
}

if (!customElements.get(CARD_TAG)) {
  customElements.define(CARD_TAG, WindguruDashboard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: CARD_TAG,
    name: "Windguru Dashboard",
    description: "Compass, average wind, gust and outdoor temperature.",
    preview: true,
  });
}
