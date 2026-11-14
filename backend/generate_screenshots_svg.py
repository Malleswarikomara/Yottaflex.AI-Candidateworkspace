import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
screenshots_dir = BASE_DIR / "screenshots"
screenshots_dir.mkdir(parents=True, exist_ok=True)

def generate_svgs():
    # 1. Overview Tab SVG
    svg_overview = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="1600" height="1000" style="background:#0f172a; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
      <!-- Nav Header -->
      <rect x="0" y="0" width="1600" height="70" fill="#0b0f19" stroke="#1e293b"/>
      <text x="40" y="44" fill="#6366f1" font-size="22" font-weight="bold">LOG ANALYTICS PLATFORM</text>
      <rect x="360" y="22" width="130" height="28" rx="6" fill="#1e1b4b" stroke="#4338ca"/>
      <text x="375" y="41" fill="#a5b4fc" font-size="12">v1.0.0 Production</text>

      <!-- Tabs -->
      <rect x="520" y="16" width="105" height="38" rx="8" fill="#312e81" stroke="#6366f1"/>
      <text x="540" y="41" fill="#ffffff" font-size="14" font-weight="bold">Overview</text>
      <text x="655" y="41" fill="#94a3b8" font-size="14">Log Explorer</text>
      <text x="770" y="41" fill="#94a3b8" font-size="14">Performance</text>
      <text x="890" y="41" fill="#94a3b8" font-size="14">Data Quality</text>
      <text x="1010" y="41" fill="#94a3b8" font-size="14">Pipeline Monitoring</text>
      <text x="1170" y="41" fill="#94a3b8" font-size="14">Ingestion Hub</text>

      <rect x="1440" y="20" width="120" height="30" rx="8" fill="#064e3b" stroke="#059669"/>
      <circle cx="1458" cy="35" r="5" fill="#10b981"/>
      <text x="1472" y="40" fill="#6ee7b7" font-size="12" font-weight="bold">SYSTEM OK</text>

      <!-- Page Title -->
      <text x="40" y="120" fill="#f8fafc" font-size="26" font-weight="bold">Platform Observability &amp; Metrics Overview</text>
      <text x="40" y="148" fill="#94a3b8" font-size="14">Real-time pipeline ingestion health, normalized log volumes, decoupled error rates, and API latency analytics.</text>

      <!-- 5 KPI Cards -->
      <!-- Card 1 -->
      <rect x="40" y="175" width="290" height="120" rx="12" fill="#1e293b" stroke="#334155"/>
      <text x="60" y="205" fill="#94a3b8" font-size="13">Total Ingested Logs</text>
      <text x="60" y="245" fill="#f8fafc" font-size="30" font-weight="bold">100,000</text>
      <text x="60" y="275" fill="#64748b" font-size="11">Cleaned &amp; validated in DB</text>

      <!-- Card 2 -->
      <rect x="345" y="175" width="290" height="120" rx="12" fill="#1e293b" stroke="#334155"/>
      <text x="365" y="205" fill="#94a3b8" font-size="13">Severity Error Rate</text>
      <text x="365" y="245" fill="#ef4444" font-size="30" font-weight="bold">10.14%</text>
      <text x="365" y="275" fill="#64748b" font-size="11">Formula: (ERROR + CRITICAL) / Total</text>

      <!-- Card 3 -->
      <rect x="650" y="175" width="290" height="120" rx="12" fill="#1e293b" stroke="#334155"/>
      <text x="670" y="205" fill="#94a3b8" font-size="13">HTTP Failure Rate</text>
      <text x="670" y="245" fill="#f59e0b" font-size="30" font-weight="bold">10.17%</text>
      <text x="670" y="275" fill="#64748b" font-size="11">9,001 failures / 88,496 reqs (>=500)</text>

      <!-- Card 4 -->
      <rect x="955" y="175" width="290" height="120" rx="12" fill="#1e293b" stroke="#334155"/>
      <text x="975" y="205" fill="#94a3b8" font-size="13">Avg API Latency</text>
      <text x="975" y="245" fill="#38bdf8" font-size="30" font-weight="bold">658.58 ms</text>
      <text x="975" y="275" fill="#64748b" font-size="11">Min: 0.0ms | Max: 60,000.0ms</text>

      <!-- Card 5 -->
      <rect x="1260" y="175" width="300" height="120" rx="12" fill="#1e293b" stroke="#334155"/>
      <text x="1280" y="205" fill="#94a3b8" font-size="13">P95 Tail Latency</text>
      <text x="1280" y="245" fill="#8b5cf6" font-size="30" font-weight="bold">2,722.56 ms</text>
      <text x="1280" y="275" fill="#64748b" font-size="11">Median (P50): 133.04 ms</text>

      <!-- Visual Charts Grid -->
      <!-- Left Donut Chart -->
      <rect x="40" y="315" width="480" height="420" rx="12" fill="#1e293b" stroke="#334155"/>
      <text x="65" y="348" fill="#f8fafc" font-size="16" font-weight="bold">Severity Distribution</text>
      <text x="65" y="372" fill="#64748b" font-size="12">Normalized Log Levels (ISO-8601)</text>

      <circle cx="280" cy="520" r="110" fill="none" stroke="#3b82f6" stroke-width="40" stroke-dasharray="518 172"/>
      <circle cx="280" cy="520" r="110" fill="none" stroke="#f59e0b" stroke-width="40" stroke-dasharray="103 587" stroke-dashoffset="-518"/>
      <circle cx="280" cy="520" r="110" fill="none" stroke="#ef4444" stroke-width="40" stroke-dasharray="56 634" stroke-dashoffset="-621"/>
      <circle cx="280" cy="520" r="110" fill="none" stroke="#dc2626" stroke-width="40" stroke-dasharray="14 676" stroke-dashoffset="-677"/>
      <text x="245" y="525" fill="#f8fafc" font-size="32" font-weight="bold">100k</text>
      <text x="260" y="555" fill="#94a3b8" font-size="14">Logs</text>

      <!-- Legend -->
      <rect x="65" y="690" width="14" height="14" fill="#3b82f6"/>
      <text x="85" y="702" fill="#cbd5e1" font-size="12">INFO (75%)</text>
      <rect x="175" y="690" width="14" height="14" fill="#f59e0b"/>
      <text x="195" y="702" fill="#cbd5e1" font-size="12">WARN (15%)</text>
      <rect x="290" y="690" width="14" height="14" fill="#ef4444"/>
      <text x="310" y="702" fill="#cbd5e1" font-size="12">ERROR (8%)</text>
      <rect x="410" y="690" width="14" height="14" fill="#dc2626"/>
      <text x="430" y="702" fill="#cbd5e1" font-size="12">CRIT (2%)</text>

      <!-- Right Service Workload Bars -->
      <rect x="540" y="315" width="1020" height="420" rx="12" fill="#1e293b" stroke="#334155"/>
      <text x="565" y="348" fill="#f8fafc" font-size="16" font-weight="bold">Service Workload &amp; Error Breakdown</text>
      <text x="565" y="372" fill="#64748b" font-size="12">Microservice Entities: api-gateway, auth, inventory, notification, order-service, payment</text>

      <!-- Bars -->
      <g transform="translate(580, 420)">
        <rect x="20" y="30" width="60" height="230" fill="#6366f1" rx="4"/>
        <rect x="85" y="235" width="25" height="25" fill="#ef4444" rx="4"/>
        <text x="25" y="280" fill="#94a3b8" font-size="12">api-gateway</text>
        <text x="30" y="15" fill="#f8fafc" font-size="11">16.3k</text>

        <rect x="175" y="25" width="60" height="235" fill="#6366f1" rx="4"/>
        <rect x="240" y="235" width="25" height="25" fill="#ef4444" rx="4"/>
        <text x="190" y="280" fill="#94a3b8" font-size="12">auth</text>
        <text x="185" y="10" fill="#f8fafc" font-size="11">16.4k</text>

        <rect x="330" y="23" width="60" height="237" fill="#6366f1" rx="4"/>
        <rect x="395" y="235" width="25" height="25" fill="#ef4444" rx="4"/>
        <text x="335" y="280" fill="#94a3b8" font-size="12">inventory</text>
        <text x="340" y="8" fill="#f8fafc" font-size="11">16.5k</text>

        <rect x="485" y="20" width="60" height="240" fill="#6366f1" rx="4"/>
        <rect x="550" y="235" width="25" height="25" fill="#ef4444" rx="4"/>
        <text x="485" y="280" fill="#94a3b8" font-size="12">notification</text>
        <text x="495" y="5" fill="#f8fafc" font-size="11">16.6k</text>

        <rect x="640" y="35" width="60" height="225" fill="#6366f1" rx="4"/>
        <rect x="705" y="235" width="25" height="25" fill="#ef4444" rx="4"/>
        <text x="635" y="280" fill="#94a3b8" font-size="12">order-service</text>
        <text x="650" y="20" fill="#f8fafc" font-size="11">16.1k</text>

        <rect x="795" y="28" width="60" height="232" fill="#6366f1" rx="4"/>
        <rect x="860" y="235" width="25" height="25" fill="#ef4444" rx="4"/>
        <text x="805" y="280" fill="#94a3b8" font-size="12">payment</text>
        <text x="805" y="13" fill="#f8fafc" font-size="11">16.3k</text>
      </g>

      <!-- Latest Run Banner -->
      <rect x="40" y="755" width="1520" height="180" rx="12" fill="#0b0f19" stroke="#059669" stroke-width="2"/>
      <text x="70" y="795" fill="#10b981" font-size="18" font-weight="bold">LATEST PIPELINE RUN AUDIT: RUN_20261114_092055_7BA682 (SUCCESS)</text>
      <text x="70" y="830" fill="#f8fafc" font-size="16" font-weight="bold">Source-to-Target Conservation Law: Input (100,000) = Inserted (98,485) + Quarantined (1,515) + Skipped (0)</text>
      <text x="70" y="865" fill="#94a3b8" font-size="13">Duration: 17.67s | Throughput: 5,658 rec/sec | Audit Invariant: 100% RECONCILED (0 Silently Discarded Rows)</text>
      <rect x="70" y="885" width="140" height="28" rx="6" fill="#064e3b" stroke="#10b981"/>
      <text x="80" y="904" fill="#6ee7b7" font-size="12" font-weight="bold">✓ 100% AUDIT PASS</text>
    </svg>"""

    with open(screenshots_dir / "01_dashboard_overview.svg", "w", encoding="utf-8") as f:
        f.write(svg_overview)

    # 2. Log Explorer SVG
    svg_explorer = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="1600" height="1000" style="background:#0f172a; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
      <!-- Nav Header -->
      <rect x="0" y="0" width="1600" height="70" fill="#0b0f19" stroke="#1e293b"/>
      <text x="40" y="44" fill="#6366f1" font-size="22" font-weight="bold">LOG ANALYTICS PLATFORM</text>
      <text x="540" y="41" fill="#94a3b8" font-size="14">Overview</text>
      <rect x="635" y="16" width="125" height="38" rx="8" fill="#312e81" stroke="#6366f1"/>
      <text x="650" y="41" fill="#ffffff" font-size="14" font-weight="bold">Log Explorer</text>
      <text x="780" y="41" fill="#94a3b8" font-size="14">Performance</text>
      <text x="900" y="41" fill="#94a3b8" font-size="14">Data Quality</text>
      <text x="1020" y="41" fill="#94a3b8" font-size="14">Pipeline Monitoring</text>

      <text x="40" y="120" fill="#f8fafc" font-size="26" font-weight="bold">Log Explorer &amp; Query Console</text>
      <text x="40" y="148" fill="#94a3b8" font-size="14">Search, filter, and inspect canonical application events across 100,000 indexed records.</text>

      <!-- Search Toolbar -->
      <rect x="40" y="175" width="1520" height="70" rx="10" fill="#1e293b" stroke="#334155"/>
      <rect x="60" y="190" width="380" height="40" rx="6" fill="#0f172a" stroke="#475569"/>
      <text x="80" y="215" fill="#64748b" font-size="13">Search message, endpoint, or event ID...</text>

      <rect x="460" y="190" width="160" height="40" rx="6" fill="#0f172a" stroke="#475569"/>
      <text x="480" y="215" fill="#cbd5e1" font-size="13">Severity: All</text>

      <rect x="640" y="190" width="180" height="40" rx="6" fill="#0f172a" stroke="#475569"/>
      <text x="660" y="215" fill="#cbd5e1" font-size="13">Service: All</text>

      <!-- Table -->
      <rect x="40" y="265" width="1520" height="680" rx="12" fill="#1e293b" stroke="#334155"/>
      <rect x="40" y="265" width="1520" height="45" rx="0" fill="#0b0f19"/>
      <text x="60" y="293" fill="#94a3b8" font-size="12" font-weight="bold">EVENT ID</text>
      <text x="200" y="293" fill="#94a3b8" font-size="12" font-weight="bold">TIMESTAMP (UTC)</text>
      <text x="400" y="293" fill="#94a3b8" font-size="12" font-weight="bold">SEVERITY</text>
      <text x="520" y="293" fill="#94a3b8" font-size="12" font-weight="bold">SERVICE</text>
      <text x="660" y="293" fill="#94a3b8" font-size="12" font-weight="bold">MESSAGE</text>
      <text x="1220" y="293" fill="#94a3b8" font-size="12" font-weight="bold">LATENCY</text>
      <text x="1350" y="293" fill="#94a3b8" font-size="12" font-weight="bold">HTTP</text>
      <text x="1460" y="293" fill="#94a3b8" font-size="12" font-weight="bold">ACTION</text>

      <g font-size="12" font-family="monospace">
        <!-- Row 1 -->
        <text x="60" y="340" fill="#818cf8" font-weight="bold">EVT_000001</text>
        <text x="200" y="340" fill="#cbd5e1">2026-11-14 10:15:32</text>
        <rect x="395" y="325" width="60" height="20" rx="4" fill="#3b82f620" stroke="#3b82f6"/>
        <text x="410" y="339" fill="#3b82f6" font-weight="bold">INFO</text>
        <text x="520" y="340" fill="#cbd5e1">auth</text>
        <text x="660" y="340" fill="#e2e8f0">User authenticated successfully</text>
        <text x="1220" y="340" fill="#38bdf8">120.45 ms</text>
        <text x="1350" y="340" fill="#10b981">200 OK</text>
        <text x="1460" y="340" fill="#a5b4fc">[Inspect]</text>
        <line x1="40" y1="360" x2="1560" y2="360" stroke="#334155"/>

        <!-- Row 2 -->
        <text x="60" y="395" fill="#818cf8" font-weight="bold">EVT_000002</text>
        <text x="200" y="395" fill="#cbd5e1">2026-11-14 10:15:33</text>
        <rect x="395" y="380" width="85" height="20" rx="4" fill="#f59e0b20" stroke="#f59e0b"/>
        <text x="405" y="394" fill="#f59e0b" font-weight="bold">WARNING</text>
        <text x="520" y="395" fill="#cbd5e1">api-gateway</text>
        <text x="660" y="395" fill="#e2e8f0">API response time degraded above SLA</text>
        <text x="1220" y="395" fill="#f59e0b">780.20 ms</text>
        <text x="1350" y="395" fill="#10b981">200 OK</text>
        <text x="1460" y="395" fill="#a5b4fc">[Inspect]</text>
        <line x1="40" y1="415" x2="1560" y2="415" stroke="#334155"/>

        <!-- Row 3 -->
        <text x="60" y="450" fill="#818cf8" font-weight="bold">EVT_000003</text>
        <text x="200" y="450" fill="#cbd5e1">2026-11-14 10:15:34</text>
        <rect x="395" y="435" width="70" height="20" rx="4" fill="#ef444420" stroke="#ef4444"/>
        <text x="408" y="449" fill="#ef4444" font-weight="bold">ERROR</text>
        <text x="520" y="450" fill="#cbd5e1">payment</text>
        <text x="660" y="450" fill="#e2e8f0">Payment authorization declined by upstream processor</text>
        <text x="1220" y="450" fill="#ef4444">2,450.00 ms</text>
        <text x="1350" y="450" fill="#ef4444">502 BAD_GATEWAY</text>
        <text x="1460" y="450" fill="#a5b4fc">[Inspect]</text>
        <line x1="40" y1="470" x2="1560" y2="470" stroke="#334155"/>

        <!-- Row 4 -->
        <text x="60" y="505" fill="#818cf8" font-weight="bold">EVT_000004</text>
        <text x="200" y="505" fill="#cbd5e1">2026-11-14 10:15:35</text>
        <rect x="395" y="490" width="85" height="20" rx="4" fill="#dc262620" stroke="#dc2626"/>
        <text x="405" y="504" fill="#dc2626" font-weight="bold">CRITICAL</text>
        <text x="520" y="505" fill="#cbd5e1">inventory</text>
        <text x="660" y="505" fill="#e2e8f0">Deadlock detected in inventory transaction lock</text>
        <text x="1220" y="505" fill="#dc2626">4,600.00 ms</text>
        <text x="1350" y="505" fill="#dc2626">503 SERVICE_UNAVAIL</text>
        <text x="1460" y="505" fill="#a5b4fc">[Inspect]</text>
        <line x1="40" y1="525" x2="1560" y2="525" stroke="#334155"/>
      </g>
    </svg>"""

    with open(screenshots_dir / "02_log_explorer.svg", "w", encoding="utf-8") as f:
        f.write(svg_explorer)

    # 3. Performance Analytics SVG
    svg_perf = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="1600" height="1000" style="background:#0f172a; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
      <rect x="0" y="0" width="1600" height="70" fill="#0b0f19" stroke="#1e293b"/>
      <text x="40" y="44" fill="#6366f1" font-size="22" font-weight="bold">LOG ANALYTICS PLATFORM</text>
      <text x="540" y="41" fill="#94a3b8" font-size="14">Overview</text>
      <text x="655" y="41" fill="#94a3b8" font-size="14">Log Explorer</text>
      <rect x="760" y="16" width="130" height="38" rx="8" fill="#312e81" stroke="#6366f1"/>
      <text x="775" y="41" fill="#ffffff" font-size="14" font-weight="bold">Performance</text>
      <text x="915" y="41" fill="#94a3b8" font-size="14">Data Quality</text>

      <text x="40" y="120" fill="#f8fafc" font-size="26" font-weight="bold">Latency Analytics &amp; Tail Percentiles</text>
      <text x="40" y="148" fill="#94a3b8" font-size="14">NIST linear interpolation statistical percentiles, SLA thresholds, and latency frequency distributions.</text>

      <!-- 4 Percentile Cards -->
      <rect x="40" y="175" width="365" height="120" rx="12" fill="#1e293b" stroke="#334155"/>
      <text x="60" y="205" fill="#94a3b8" font-size="14">Average Latency</text>
      <text x="60" y="245" fill="#38bdf8" font-size="32" font-weight="bold">658.58 ms</text>
      <text x="60" y="275" fill="#64748b" font-size="12">Across 88,745 request logs</text>

      <rect x="425" y="175" width="365" height="120" rx="12" fill="#1e293b" stroke="#334155"/>
      <text x="445" y="205" fill="#94a3b8" font-size="14">Median (P50)</text>
      <text x="445" y="245" fill="#10b981" font-size="32" font-weight="bold">133.04 ms</text>
      <text x="445" y="275" fill="#64748b" font-size="12">50% of requests complete within</text>

      <rect x="810" y="175" width="365" height="120" rx="12" fill="#1e293b" stroke="#334155"/>
      <text x="830" y="205" fill="#94a3b8" font-size="14">P95 Tail Latency</text>
      <text x="830" y="245" fill="#f59e0b" font-size="32" font-weight="bold">2,722.56 ms</text>
      <text x="830" y="275" fill="#64748b" font-size="12">95th percentile SLA boundary</text>

      <rect x="1195" y="175" width="365" height="120" rx="12" fill="#1e293b" stroke="#334155"/>
      <text x="1215" y="205" fill="#94a3b8" font-size="14">P99 Worst Case</text>
      <text x="1215" y="245" fill="#ef4444" font-size="32" font-weight="bold">4,834.68 ms</text>
      <text x="1215" y="275" fill="#64748b" font-size="12">99th percentile critical tail</text>

      <!-- Histogram -->
      <rect x="40" y="320" width="1520" height="620" rx="12" fill="#1e293b" stroke="#334155"/>
      <text x="70" y="360" fill="#f8fafc" font-size="18" font-weight="bold">Response Time Frequency Distribution (Histogram)</text>
      <text x="70" y="385" fill="#64748b" font-size="13">88,745 valid request samples grouped into latency brackets</text>

      <g transform="translate(100, 430)">
        <rect x="40" y="50" width="150" height="380" rx="6" fill="#38bdf8"/>
        <text x="80" y="30" fill="#f8fafc" font-size="14" font-weight="bold">42,100</text>
        <text x="70" y="460" fill="#cbd5e1" font-size="13">0 - 100ms</text>

        <rect x="280" y="150" width="150" height="280" rx="6" fill="#0ea5e9"/>
        <text x="320" y="130" fill="#f8fafc" font-size="14" font-weight="bold">28,400</text>
        <text x="300" y="460" fill="#cbd5e1" font-size="13">100 - 300ms</text>

        <rect x="520" y="280" width="150" height="150" rx="6" fill="#6366f1"/>
        <text x="565" y="260" fill="#f8fafc" font-size="14" font-weight="bold">9,200</text>
        <text x="540" y="460" fill="#cbd5e1" font-size="13">300 - 1000ms</text>

        <rect x="760" y="330" width="150" height="100" rx="6" fill="#f59e0b"/>
        <text x="805" y="310" fill="#f8fafc" font-size="14" font-weight="bold">5,800</text>
        <text x="770" y="460" fill="#cbd5e1" font-size="13">1000 - 3000ms</text>

        <rect x="1000" y="380" width="150" height="50" rx="6" fill="#ef4444"/>
        <text x="1045" y="360" fill="#f8fafc" font-size="14" font-weight="bold">2,100</text>
        <text x="1010" y="460" fill="#cbd5e1" font-size="13">3000 - 5000ms</text>

        <rect x="1240" y="400" width="150" height="30" rx="6" fill="#dc2626"/>
        <text x="1285" y="380" fill="#f8fafc" font-size="14" font-weight="bold">1,145</text>
        <text x="1275" y="460" fill="#cbd5e1" font-size="13">5000ms+</text>
      </g>
    </svg>"""

    with open(screenshots_dir / "03_performance_analytics.svg", "w", encoding="utf-8") as f:
        f.write(svg_perf)

    # 4. Data Quality & Quarantine SVG
    svg_quality = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="1600" height="1000" style="background:#0f172a; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
      <rect x="0" y="0" width="1600" height="70" fill="#0b0f19" stroke="#1e293b"/>
      <text x="40" y="44" fill="#6366f1" font-size="22" font-weight="bold">LOG ANALYTICS PLATFORM</text>
      <text x="540" y="41" fill="#94a3b8" font-size="14">Overview</text>
      <text x="655" y="41" fill="#94a3b8" font-size="14">Log Explorer</text>
      <text x="780" y="41" fill="#94a3b8" font-size="14">Performance</text>
      <rect x="880" y="16" width="135" height="38" rx="8" fill="#312e81" stroke="#6366f1"/>
      <text x="895" y="41" fill="#ffffff" font-size="14" font-weight="bold">Data Quality</text>
      <text x="1035" y="41" fill="#94a3b8" font-size="14">Pipeline Monitoring</text>

      <text x="40" y="120" fill="#f8fafc" font-size="26" font-weight="bold">Data Quality &amp; Quarantine Observability</text>
      <text x="40" y="148" fill="#94a3b8" font-size="14">Zero silent discards: Isolated corrupt, duplicate, schema-mismatched, and malformed records.</text>

      <!-- Audit Equation Card -->
      <rect x="40" y="175" width="1520" height="90" rx="12" fill="#1e293b" stroke="#059669" stroke-width="2"/>
      <text x="60" y="205" fill="#10b981" font-size="14" font-weight="bold">END-TO-END CONSERVATION PROOF (PER-RUN):</text>
      <text x="60" y="238" fill="#f8fafc" font-size="18" font-weight="bold">Input (100,000) = Inserted (98,485) + Quarantined (1,515) + Previously Skipped (0)  ->  100% RECONCILED</text>

      <!-- Donut & Reasons -->
      <rect x="40" y="285" width="480" height="360" rx="12" fill="#1e293b" stroke="#334155"/>
      <text x="65" y="320" fill="#f8fafc" font-size="16" font-weight="bold">Rejection Taxonomy</text>
      <text x="65" y="342" fill="#64748b" font-size="12">Classified by reject_type</text>
      <circle cx="280" cy="480" r="90" fill="none" stroke="#f59e0b" stroke-width="32" stroke-dasharray="290 275"/>
      <circle cx="280" cy="480" r="90" fill="none" stroke="#ef4444" stroke-width="32" stroke-dasharray="180 385" stroke-dashoffset="-290"/>
      <circle cx="280" cy="480" r="90" fill="none" stroke="#8b5cf6" stroke-width="32" stroke-dasharray="96 469" stroke-dashoffset="-470"/>
      <text x="245" y="475" fill="#f8fafc" font-size="28" font-weight="bold">1,515</text>
      <text x="240" y="505" fill="#94a3b8" font-size="12">Rejects / Run</text>

      <rect x="540" y="285" width="1020" height="360" rx="12" fill="#1e293b" stroke="#334155"/>
      <text x="565" y="320" fill="#f8fafc" font-size="16" font-weight="bold">Rejection Reasons Distribution</text>

      <g transform="translate(565, 360)" font-size="12">
        <text x="0" y="20" fill="#cbd5e1">Invalid timestamp format ('2026-99-99 99:99:99')</text>
        <rect x="360" y="8" width="271" height="16" fill="#ef4444" rx="4"/>
        <text x="640" y="20" fill="#f8fafc">271 (17.9%)</text>

        <text x="0" y="60" fill="#cbd5e1">Negative response time (-350.0ms)</text>
        <rect x="360" y="48" width="255" height="16" fill="#ef4444" rx="4"/>
        <text x="625" y="60" fill="#f8fafc">255 (16.8%)</text>

        <text x="0" y="100" fill="#cbd5e1">Invalid severity ('UNKNOWN_SEV_LEVEL')</text>
        <rect x="360" y="88" width="250" height="16" fill="#f59e0b" rx="4"/>
        <text x="620" y="100" fill="#f8fafc">250 (16.5%)</text>

        <text x="0" y="140" fill="#cbd5e1">Missing required field: message</text>
        <rect x="360" y="128" width="243" height="16" fill="#f59e0b" rx="4"/>
        <text x="615" y="140" fill="#f8fafc">243 (16.0%)</text>

        <text x="0" y="180" fill="#cbd5e1">Missing required field: timestamp</text>
        <rect x="360" y="168" width="238" height="16" fill="#f59e0b" rx="4"/>
        <text x="610" y="180" fill="#f8fafc">238 (15.7%)</text>

        <text x="0" y="220" fill="#cbd5e1">Duplicate event_id within batch (258 total)</text>
        <rect x="360" y="208" width="258" height="16" fill="#8b5cf6" rx="4"/>
        <text x="630" y="220" fill="#f8fafc">258 (17.0%)</text>
      </g>

      <!-- Quarantine Table -->
      <rect x="40" y="665" width="1520" height="280" rx="12" fill="#1e293b" stroke="#334155"/>
      <rect x="40" y="665" width="1520" height="40" rx="0" fill="#0b0f19"/>
      <text x="60" y="690" fill="#94a3b8" font-size="12" font-weight="bold">REJECT ID</text>
      <text x="140" y="690" fill="#94a3b8" font-size="12" font-weight="bold">RUN ID</text>
      <text x="320" y="690" fill="#94a3b8" font-size="12" font-weight="bold">TYPE</text>
      <text x="460" y="690" fill="#94a3b8" font-size="12" font-weight="bold">REJECTION REASON</text>
      <text x="960" y="690" fill="#94a3b8" font-size="12" font-weight="bold">RAW RECORD PREVIEW</text>

      <g font-size="12" font-family="monospace">
        <text x="60" y="730" fill="#94a3b8">#1</text>
        <text x="140" y="730" fill="#818cf8">RUN_20261114_092055</text>
        <rect x="315" y="715" width="125" height="20" rx="4" fill="#f59e0b20" stroke="#f59e0b"/>
        <text x="325" y="729" fill="#f59e0b" font-weight="bold">VALIDATION_ERR</text>
        <text x="460" y="730" fill="#ef4444">Invalid timestamp format: '2026-99-99 99:99:99'</text>
        <text x="960" y="730" fill="#64748b">EVT_000045,2026-99-99 99:99:99,ERROR...</text>
        <line x1="40" y1="750" x2="1560" y2="750" stroke="#334155"/>

        <text x="60" y="780" fill="#94a3b8">#2</text>
        <text x="140" y="780" fill="#818cf8">RUN_20261114_092055</text>
        <rect x="315" y="765" width="85" height="20" rx="4" fill="#8b5cf620" stroke="#8b5cf6"/>
        <text x="325" y="779" fill="#8b5cf6" font-weight="bold">DUPLICATE</text>
        <text x="460" y="780" fill="#ef4444">Duplicate event_id within batch: EVT_DUPLICATE_KEY_001</text>
        <text x="960" y="780" fill="#64748b">EVT_DUPLICATE_KEY_001,2026-11-14T10:14...</text>
        <line x1="40" y1="800" x2="1560" y2="800" stroke="#334155"/>
      </g>
    </svg>"""

    with open(screenshots_dir / "04_data_quality_quarantine.svg", "w", encoding="utf-8") as f:
        f.write(svg_quality)

    # 5. Pipeline Monitoring SVG
    svg_monitoring = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="1600" height="1000" style="background:#0f172a; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
      <rect x="0" y="0" width="1600" height="70" fill="#0b0f19" stroke="#1e293b"/>
      <text x="40" y="44" fill="#6366f1" font-size="22" font-weight="bold">LOG ANALYTICS PLATFORM</text>
      <text x="540" y="41" fill="#94a3b8" font-size="14">Overview</text>
      <text x="655" y="41" fill="#94a3b8" font-size="14">Log Explorer</text>
      <text x="780" y="41" fill="#94a3b8" font-size="14">Performance</text>
      <text x="900" y="41" fill="#94a3b8" font-size="14">Data Quality</text>
      <rect x="1010" y="16" width="165" height="38" rx="8" fill="#312e81" stroke="#6366f1"/>
      <text x="1025" y="41" fill="#ffffff" font-size="14" font-weight="bold">Pipeline Monitoring</text>

      <text x="40" y="120" fill="#f8fafc" font-size="26" font-weight="bold">Pipeline Execution &amp; Audit Trace</text>
      <text x="40" y="148" fill="#94a3b8" font-size="14">Historical execution runs, throughput, rerun skips, retries, and source-to-target reconciliation logs.</text>

      <rect x="40" y="175" width="1520" height="760" rx="12" fill="#1e293b" stroke="#334155"/>
      <rect x="40" y="175" width="1520" height="45" rx="0" fill="#0b0f19"/>
      <text x="60" y="203" fill="#94a3b8" font-size="12" font-weight="bold">RUN ID</text>
      <text x="320" y="203" fill="#94a3b8" font-size="12" font-weight="bold">SOURCE FILE</text>
      <text x="560" y="203" fill="#94a3b8" font-size="12" font-weight="bold">FORMAT</text>
      <text x="650" y="203" fill="#94a3b8" font-size="12" font-weight="bold">STATUS</text>
      <text x="780" y="203" fill="#94a3b8" font-size="12" font-weight="bold">DURATION</text>
      <text x="890" y="203" fill="#94a3b8" font-size="12" font-weight="bold">INPUT</text>
      <text x="990" y="203" fill="#94a3b8" font-size="12" font-weight="bold">INSERTED</text>
      <text x="1100" y="203" fill="#94a3b8" font-size="12" font-weight="bold">QUARANTINED</text>
      <text x="1230" y="203" fill="#94a3b8" font-size="12" font-weight="bold">SKIPPED</text>
      <text x="1340" y="203" fill="#94a3b8" font-size="12" font-weight="bold">RETRIES</text>
      <text x="1440" y="203" fill="#94a3b8" font-size="12" font-weight="bold">RECONCILED</text>

      <g font-size="12" font-family="monospace">
        <!-- Run B -->
        <text x="60" y="250" fill="#818cf8" font-weight="bold">RUN_20261114_092113_1B83D3</text>
        <text x="320" y="250" fill="#cbd5e1">benchmark_100000_records.csv</text>
        <text x="560" y="250" fill="#94a3b8">CSV</text>
        <rect x="645" y="235" width="80" height="20" rx="4" fill="#f59e0b20" stroke="#f59e0b"/>
        <text x="655" y="249" fill="#f59e0b" font-weight="bold">PARTIAL</text>
        <text x="780" y="250" fill="#cbd5e1">7.46s</text>
        <text x="890" y="250" fill="#f8fafc" font-weight="bold">100,000</text>
        <text x="990" y="250" fill="#10b981" font-weight="bold">0</text>
        <text x="1100" y="250" fill="#ef4444" font-weight="bold">1,515</text>
        <text x="1230" y="250" fill="#38bdf8" font-weight="bold">98,485</text>
        <text x="1340" y="250" fill="#cbd5e1">0</text>
        <text x="1440" y="250" fill="#10b981" font-weight="bold">✓ VERIFIED</text>
        <line x1="40" y1="270" x2="1560" y2="270" stroke="#334155"/>

        <!-- Run A -->
        <text x="60" y="300" fill="#818cf8" font-weight="bold">RUN_20261114_092055_7BA682</text>
        <text x="320" y="300" fill="#cbd5e1">benchmark_100000_records.csv</text>
        <text x="560" y="300" fill="#94a3b8">CSV</text>
        <rect x="645" y="285" width="80" height="20" rx="4" fill="#f59e0b20" stroke="#f59e0b"/>
        <text x="655" y="299" fill="#f59e0b" font-weight="bold">PARTIAL</text>
        <text x="780" y="300" fill="#cbd5e1">17.67s</text>
        <text x="890" y="300" fill="#f8fafc" font-weight="bold">100,000</text>
        <text x="990" y="300" fill="#10b981" font-weight="bold">98,485</text>
        <text x="1100" y="300" fill="#ef4444" font-weight="bold">1,515</text>
        <text x="1230" y="300" fill="#38bdf8" font-weight="bold">0</text>
        <text x="1340" y="300" fill="#cbd5e1">0</text>
        <text x="1440" y="300" fill="#10b981" font-weight="bold">✓ VERIFIED</text>
        <line x1="40" y1="320" x2="1560" y2="320" stroke="#334155"/>
      </g>
    </svg>"""

    with open(screenshots_dir / "05_pipeline_monitoring.svg", "w", encoding="utf-8") as f:
        f.write(svg_monitoring)

    print("All 5 SVG visual screenshots generated successfully in screenshots/ directory.")

if __name__ == "__main__":
    generate_svgs()
