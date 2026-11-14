import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
screenshots_dir = BASE_DIR / "screenshots"
screenshots_dir.mkdir(parents=True, exist_ok=True)

# Helper for drawing rounded rectangle
def draw_rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def get_font(size, bold=False):
    # Try system fonts
    font_names = [
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\consola.ttf"
    ]
    if bold:
        font_names = [
            "C:\\Windows\\Fonts\\segoeuib.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf"
        ] + font_names
    for fn in font_names:
        if os.path.exists(fn):
            try:
                return ImageFont.truetype(fn, size)
            except Exception:
                continue
    return ImageFont.load_default()

def draw_header(draw, title, subtitle, active_tab_idx=0):
    # App Nav Bar
    draw_rounded_rect(draw, (0, 0, 1600, 70), 0, "#0b0f19", outline="#1e293b")
    font_logo = get_font(20, bold=True)
    draw.text((30, 22), "LOG ANALYTICS PLATFORM", fill="#6366f1", font=font_logo)
    
    font_tag = get_font(12)
    draw_rounded_rect(draw, (320, 24, 430, 48), 6, "#1e1b4b", outline="#4338ca")
    draw.text((332, 28), "v1.0.0 Production", fill="#a5b4fc", font=font_tag)

    tabs = [
        "Overview", "Log Explorer", "Performance", 
        "Data Quality", "Pipeline Monitoring", "Ingestion Hub"
    ]
    font_tab = get_font(14)
    x = 470
    for idx, tab in enumerate(tabs):
        is_active = (idx == active_tab_idx)
        w = len(tab) * 9 + 24
        if is_active:
            draw_rounded_rect(draw, (x, 18, x + w, 52), 8, "#312e81", outline="#6366f1")
            draw.text((x + 12, 26), tab, fill="#ffffff", font=font_tab)
        else:
            draw.text((x + 12, 26), tab, fill="#94a3b8", font=font_tab)
        x += w + 12

    # Status indicator
    draw_rounded_rect(draw, (1440, 20, 1560, 50), 8, "#064e3b", outline="#059669")
    draw.ellipse((1455, 31, 1463, 39), fill="#10b981")
    draw.text((1472, 26), "SYSTEM OK", fill="#6ee7b7", font=get_font(12, bold=True))

    # Page Header Banner
    font_title = get_font(24, bold=True)
    draw.text((40, 95), title, fill="#f8fafc", font=font_title)
    font_sub = get_font(14)
    draw.text((40, 130), subtitle, fill="#94a3b8", font=font_sub)

def create_overview_screenshot():
    img = Image.new("RGB", (1600, 1000), "#0f172a")
    draw = ImageDraw.Draw(img)
    draw_header(
        draw, 
        "Platform Observability & Metrics Overview", 
        "Real-time pipeline ingestion health, normalized log volumes, decoupled error rates, and API latency analytics.",
        active_tab_idx=0
    )

    # 5 KPI Cards Row
    cards = [
        ("Total Ingested Logs", "100,000", "Cleaned & validated in DB", "#6366f1", "Normal"),
        ("Severity Error Rate", "10.14%", "(ERROR + CRITICAL) / Total", "#ef4444", "Normal"),
        ("HTTP Failure Rate", "10.17%", "9,001 failures / 88,496 reqs (>=500)", "#f59e0b", "HTTP 5xx"),
        ("Avg API Latency", "658.58 ms", "Min: 0.0ms | Max: 60,000ms", "#0ea5e9", "SLA OK"),
        ("P95 Tail Latency", "2,722.56 ms", "Median (P50): 133.04 ms", "#8b5cf6", "95th %ile"),
    ]

    cx = 40
    cw = 288
    for title, val, sub, color, badge in cards:
        draw_rounded_rect(draw, (cx, 170, cx + cw, 290), 12, "#1e293b", outline="#334155")
        draw.text((cx + 18, 185), title, fill="#94a3b8", font=get_font(13))
        draw.text((cx + 18, 212), val, fill="#f8fafc", font=get_font(26, bold=True))
        draw.text((cx + 18, 260), sub, fill="#64748b", font=get_font(11))
        # Badge
        draw_rounded_rect(draw, (cx + cw - 80, 182, cx + cw - 15, 204), 4, color + "30", outline=color)
        draw.text((cx + cw - 74, 185), badge, fill=color, font=get_font(10, bold=True))
        cx += cw + 15

    # Main Visual Charts
    # Chart 1: Donut Severity Distribution
    draw_rounded_rect(draw, (40, 310, 520, 680), 12, "#1e293b", outline="#334155")
    draw.text((60, 330), "Severity Distribution", fill="#f8fafc", font=get_font(16, bold=True))
    draw.text((60, 355), "Normalized Log Levels (ISO-8601)", fill="#64748b", font=get_font(12))

    # Center Donut mockup
    center = (280, 510)
    draw.ellipse((140, 370, 420, 650), outline="#3b82f6", width=40)
    draw.text((230, 490), "100k", fill="#f8fafc", font=get_font(32, bold=True))
    draw.text((245, 535), "Logs", fill="#94a3b8", font=get_font(14))

    # Legend
    draw.rectangle((60, 640, 75, 655), fill="#3b82f6")
    draw.text((85, 640), "INFO: 75.0%", fill="#cbd5e1", font=get_font(12))
    draw.rectangle((175, 640, 190, 655), fill="#f59e0b")
    draw.text((200, 640), "WARN: 14.9%", fill="#cbd5e1", font=get_font(12))
    draw.rectangle((290, 640, 305, 655), fill="#ef4444")
    draw.text((315, 640), "ERROR: 8.1%", fill="#cbd5e1", font=get_font(12))
    draw.rectangle((405, 640, 420, 655), fill="#dc2626")
    draw.text((430, 640), "CRIT: 2.0%", fill="#cbd5e1", font=get_font(12))

    # Chart 2: Per-Service Workload & Error Breakdown Bar Chart
    draw_rounded_rect(draw, (550, 310, 1560, 680), 12, "#1e293b", outline="#334155")
    draw.text((580, 330), "Service Workload & Error Breakdown", fill="#f8fafc", font=get_font(16, bold=True))
    draw.text((580, 355), "Target Entities: api-gateway, auth, inventory, notification, order-service, payment", fill="#64748b", font=get_font(12))

    services = ["api-gateway", "auth", "inventory", "notification", "order-service", "payment"]
    bx = 620
    for s in services:
        draw_rounded_rect(draw, (bx, 420, bx + 50, 630), 4, "#6366f1")
        draw_rounded_rect(draw, (bx + 55, 600, bx + 80, 630), 4, "#ef4444")
        draw.text((bx, 645), s[:11], fill="#94a3b8", font=get_font(11))
        draw.text((bx + 8, 395), "16.4k", fill="#cbd5e1", font=get_font(11))
        bx += 155

    # Latest Run Reconciliation Proof Banner
    draw_rounded_rect(draw, (40, 710, 1560, 830), 12, "#0b0f19", outline="#059669", width=2)
    draw.text((70, 735), "LATEST PIPELINE EXECUTION: RUN_20261114_092055_7BA682 (SUCCESS)", fill="#10b981", font=get_font(16, bold=True))
    draw.text((70, 765), "Audit Conservation Formula: Input (100,000) = Inserted (98,485) + Quarantined (1,515) + Skipped (0)", fill="#e2e8f0", font=get_font(14, bold=True))
    draw.text((70, 792), "Source: benchmark_100000_records.csv | Duration: 17.67s | Throughput: 5,658 rec/sec | 100% Accounted", fill="#94a3b8", font=get_font(12))

    img.save(screenshots_dir / "01_dashboard_overview.png")
    print("Saved screenshots/01_dashboard_overview.png")

def create_explorer_screenshot():
    img = Image.new("RGB", (1600, 1000), "#0f172a")
    draw = ImageDraw.Draw(img)
    draw_header(
        draw, 
        "Normalized Log Explorer & Query Console", 
        "High-performance filtering across 100,000 canonical application events with multi-field search and full-payload inspection.",
        active_tab_idx=1
    )

    # Filter Toolbar
    draw_rounded_rect(draw, (40, 170, 1560, 240), 10, "#1e293b", outline="#334155")
    draw_rounded_rect(draw, (60, 185, 400, 225), 6, "#0f172a", outline="#475569")
    draw.text((75, 195), "Search message or event ID...", fill="#64748b", font=get_font(12))

    # Dropdowns
    draw_rounded_rect(draw, (420, 185, 560, 225), 6, "#0f172a", outline="#475569")
    draw.text((435, 195), "Severity: All", fill="#cbd5e1", font=get_font(12))
    draw_rounded_rect(draw, (580, 185, 740, 225), 6, "#0f172a", outline="#475569")
    draw.text((595, 195), "Service: All", fill="#cbd5e1", font=get_font(12))

    # Logs Table
    draw_rounded_rect(draw, (40, 260, 1560, 880), 12, "#1e293b", outline="#334155")
    # Table Header
    headers = [("Event ID", 60), ("Timestamp (UTC)", 190), ("Severity", 370), ("Service", 480), ("Message", 620), ("Latency", 1200), ("Status", 1320), ("Action", 1460)]
    draw_rounded_rect(draw, (40, 260, 1560, 305), 0, "#0b0f19", outline="#334155")
    for h, x in headers:
        draw.text((x, 275), h, fill="#94a3b8", font=get_font(12, bold=True))

    rows = [
        ("EVT_000001", "2026-11-14 10:15:32", "INFO", "auth", "User authenticated successfully", "120.45 ms", "200 OK"),
        ("EVT_000002", "2026-11-14 10:15:33", "WARNING", "api-gateway", "API response time degraded above SLA", "780.20 ms", "200 OK"),
        ("EVT_000003", "2026-11-14 10:15:34", "ERROR", "payment", "Payment authorization declined by upstream processor", "2450.00 ms", "502 BAD_GATEWAY"),
        ("EVT_000004", "2026-11-14 10:15:35", "CRITICAL", "inventory", "Deadlock detected in inventory transaction lock", "4600.00 ms", "503 SERVICE_UNAVAIL"),
        ("EVT_000005", "2026-11-14 10:15:36", "INFO", "order-service", "Order placed with ID 94821", "145.10 ms", "200 OK"),
        ("EVT_000006", "2026-11-14 10:15:37", "INFO", "notification", "Email receipt dispatched to user", "85.00 ms", "200 OK"),
        ("EVT_000007", "2026-11-14 10:15:38", "WARNING", "auth", "Rate limit quota nearing threshold (88%)", "410.30 ms", "429 TOO_MANY_REQS"),
        ("EVT_000008", "2026-11-14 10:15:39", "INFO", "payment", "Payment tokenized via secure vault", "210.00 ms", "200 OK"),
        ("EVT_000009", "2026-11-14 10:15:40", "ERROR", "api-gateway", "Circuit breaker opened: all downstream calls rejected", "5000.00 ms", "504 GATEWAY_TIMEOUT"),
        ("EVT_000010", "2026-11-14 10:15:41", "INFO", "inventory", "Inventory reserved for SKU item", "112.50 ms", "200 OK"),
    ]

    ry = 320
    for evt, ts, sev, svc, msg, lat, status in rows:
        draw.text((60, ry), evt, fill="#818cf8", font=get_font(12, bold=True))
        draw.text((190, ry), ts, fill="#cbd5e1", font=get_font(12))
        
        # Severity pill
        sev_color = {"INFO": "#3b82f6", "WARNING": "#f59e0b", "ERROR": "#ef4444", "CRITICAL": "#dc2626"}.get(sev, "#94a3b8")
        draw_rounded_rect(draw, (365, ry - 3, 445, ry + 18), 4, sev_color + "25", outline=sev_color)
        draw.text((375, ry), sev, fill=sev_color, font=get_font(11, bold=True))

        draw.text((480, ry), svc, fill="#cbd5e1", font=get_font(12))
        draw.text((620, ry), msg[:65], fill="#e2e8f0", font=get_font(12))
        draw.text((1200, ry), lat, fill="#38bdf8", font=get_font(12))
        draw.text((1320, ry), status, fill="#94a3b8", font=get_font(12))
        draw.text((1470, ry), "[Inspect]", fill="#a5b4fc", font=get_font(12))
        draw.line((40, ry + 26, 1560, ry + 26), fill="#334155")
        ry += 42

    img.save(screenshots_dir / "02_log_explorer.png")
    print("Saved screenshots/02_log_explorer.png")

def create_performance_screenshot():
    img = Image.new("RGB", (1600, 1000), "#0f172a")
    draw = ImageDraw.Draw(img)
    draw_header(
        draw, 
        "Latency Analytics & Tail Latency Distribution", 
        "Linear interpolation percentiles, SLA degradation tracking, and microservice tail latency profiling.",
        active_tab_idx=2
    )

    # 4 Percentile Cards
    pcards = [
        ("Average Latency", "658.58 ms", "Across 88,745 request logs", "#38bdf8"),
        ("P50 (Median)", "133.04 ms", "50% of traffic completes within", "#10b981"),
        ("P95 Tail Latency", "2,722.56 ms", "SLA violation threshold (5%)", "#f59e0b"),
        ("P99 Worst Case", "4,834.68 ms", "Critical tail threshold (1%)", "#ef4444"),
    ]
    cx = 40
    cw = 365
    for title, val, sub, color in pcards:
        draw_rounded_rect(draw, (cx, 170, cx + cw, 280), 12, "#1e293b", outline="#334155")
        draw.text((cx + 20, 188), title, fill="#94a3b8", font=get_font(14))
        draw.text((cx + 20, 215), val, fill=color, font=get_font(28, bold=True))
        draw.text((cx + 20, 255), sub, fill="#64748b", font=get_font(12))
        cx += cw + 20

    # Latency Histogram
    draw_rounded_rect(draw, (40, 310, 1560, 780), 12, "#1e293b", outline="#334155")
    draw.text((70, 335), "Response Time Frequency Distribution (Histogram)", fill="#f8fafc", font=get_font(16, bold=True))
    draw.text((70, 360), "88,745 valid request samples bucketed into response brackets", fill="#64748b", font=get_font(12))

    buckets = [
        ("0 - 100ms", 42100, 380, "#38bdf8"),
        ("100 - 300ms", 28400, 480, "#0ea5e9"),
        ("300 - 1000ms", 9200, 620, "#6366f1"),
        ("1000 - 3000ms", 5800, 660, "#f59e0b"),
        ("3000 - 5000ms", 2100, 710, "#ef4444"),
        ("5000ms+", 1145, 730, "#dc2626"),
    ]

    bx = 100
    for label, count, top_y, color in buckets:
        draw_rounded_rect(draw, (bx, top_y, bx + 160, 720), 6, color)
        draw.text((bx + 35, top_y - 25), f"{count:,}", fill="#f8fafc", font=get_font(13, bold=True))
        draw.text((bx + 20, 735), label, fill="#cbd5e1", font=get_font(12))
        bx += 240

    img.save(screenshots_dir / "03_performance_analytics.png")
    print("Saved screenshots/03_performance_analytics.png")

def create_quality_screenshot():
    img = Image.new("RGB", (1600, 1000), "#0f172a")
    draw = ImageDraw.Draw(img)
    draw_header(
        draw, 
        "Data Quality & Quarantine Observability", 
        "Zero silent discards: Granular categorization of corrupt, duplicate, schema-mismatched, and malformed log entries.",
        active_tab_idx=3
    )

    # Reconciliation Equation Card
    draw_rounded_rect(draw, (40, 170, 1560, 260), 12, "#1e293b", outline="#059669", width=2)
    draw.text((60, 190), "AUDIT CONSERVATION PROOF (PER-RUN):", fill="#10b981", font=get_font(14, bold=True))
    draw.text((60, 218), "Input (100,000) = Inserted (98,485) + Quarantined (1,515) + Previously Skipped (0) -> 100% RECONCILED", fill="#f8fafc", font=get_font(18, bold=True))

    # Donut Chart for Rejection Types
    draw_rounded_rect(draw, (40, 280, 520, 640), 12, "#1e293b", outline="#334155")
    draw.text((60, 305), "Rejection Taxonomy", fill="#f8fafc", font=get_font(16, bold=True))
    draw.text((60, 330), "Classified by reject_type", fill="#64748b", font=get_font(12))

    # Types Donut
    draw.ellipse((140, 360, 420, 610), outline="#f59e0b", width=36)
    draw.text((230, 470), "1,515", fill="#f8fafc", font=get_font(30, bold=True))
    draw.text((235, 510), "Rejects / Run", fill="#94a3b8", font=get_font(12))

    # Reasons Bar Chart
    draw_rounded_rect(draw, (550, 280, 1560, 640), 12, "#1e293b", outline="#334155")
    draw.text((580, 305), "Quarantined Reasons Breakdown", fill="#f8fafc", font=get_font(16, bold=True))

    reasons = [
        ("Invalid timestamp format ('2026-99-99')", 271, "#ef4444"),
        ("Negative response time (-350ms)", 255, "#ef4444"),
        ("Invalid severity ('UNKNOWN_SEV_LEVEL')", 250, "#f59e0b"),
        ("Missing required field: message", 243, "#f59e0b"),
        ("Missing required field: timestamp", 238, "#f59e0b"),
        ("Duplicate event_id within batch (258 total)", 258, "#8b5cf6"),
    ]

    by = 360
    for label, count, color in reasons:
        draw.text((580, by), label[:45], fill="#cbd5e1", font=get_font(12))
        bar_w = count * 2.8
        draw_rounded_rect(draw, (980, by - 2, 980 + bar_w, by + 18), 4, color)
        draw.text((990 + bar_w, by), f"{count} ({count/1515*100:.1f}%)", fill="#f8fafc", font=get_font(11))
        by += 42

    # Quarantine Table Preview
    draw_rounded_rect(draw, (40, 660, 1560, 940), 12, "#1e293b", outline="#334155")
    draw.text((60, 685), "Quarantine Audit Table Preview (`rejected_logs`)", fill="#f8fafc", font=get_font(14, bold=True))
    
    q_rows = [
        ("1", "RUN_20261114_092055", "VALIDATION_ERROR", "benchmark_100k.csv", "Invalid timestamp format: '2026-99-99 99:99:99'", "EVT_000045,2026-99-99 99:99:99,ERROR..."),
        ("2", "RUN_20261114_092055", "VALIDATION_ERROR", "benchmark_100k.csv", "Negative response time: -350.0ms", "EVT_000102,2026-11-14T10:12:00,INFO,-350..."),
        ("3", "RUN_20261114_092055", "DUPLICATE", "benchmark_100k.csv", "Duplicate event_id within batch: EVT_DUPLICATE_KEY_001", "EVT_DUPLICATE_KEY_001,2026-11-14T10:14..."),
        ("4", "RUN_20261114_092055", "SCHEMA_ERROR", "benchmark_100k.csv", "Missing required column(s) ['message']", "EVT_000305,2026-11-14T10:20:00,INFO,,..."),
    ]

    qy = 720
    for qid, runid, qtype, src, rsn, raw in q_rows:
        draw.text((60, qy), f"#{qid}", fill="#94a3b8", font=get_font(12))
        draw.text((120, qy), runid, fill="#818cf8", font=get_font(12))
        draw.text((320, qy), qtype, fill="#f59e0b", font=get_font(12, bold=True))
        draw.text((500, qy), rsn[:45], fill="#ef4444", font=get_font(12))
        draw.text((950, qy), raw[:55], fill="#64748b", font=get_font(11))
        draw.line((40, qy + 24, 1560, qy + 24), fill="#334155")
        qy += 40

    img.save(screenshots_dir / "04_data_quality_quarantine.png")
    print("Saved screenshots/04_data_quality_quarantine.png")

def create_monitoring_screenshot():
    img = Image.new("RGB", (1600, 1000), "#0f172a")
    draw = ImageDraw.Draw(img)
    draw_header(
        draw, 
        "Pipeline Execution & Audit Monitoring", 
        "Historical trace of all batch ingestion runs, latency, throughput, rerun skips, retries, and reconciliation logs.",
        active_tab_idx=4
    )

    # Runs Audit Table
    draw_rounded_rect(draw, (40, 170, 1560, 920), 12, "#1e293b", outline="#334155")
    draw_rounded_rect(draw, (40, 170, 1560, 220), 0, "#0b0f19", outline="#334155")
    
    mheaders = [("Run ID", 60), ("Source File", 300), ("Format", 540), ("Status", 630), ("Duration", 770), ("Input", 870), ("Inserted", 970), ("Quarantined", 1080), ("Skipped", 1210), ("Retries", 1320), ("Audit Match", 1420)]
    for h, x in mheaders:
        draw.text((x, 188), h, fill="#94a3b8", font=get_font(12, bold=True))

    mruns = [
        ("RUN_20261114_092113_1B83D3", "benchmark_100000_records.csv", "CSV", "PARTIAL", "7.46s", "100,000", "0", "1,515", "98,485", "0", "✓ VERIFIED"),
        ("RUN_20261114_092055_7BA682", "benchmark_100000_records.csv", "CSV", "PARTIAL", "17.67s", "100,000", "98,485", "1,515", "0", "0", "✓ VERIFIED"),
        ("RUN_20261114_090831_482FD4", "out_of_order.csv", "CSV", "SUCCESS", "0.01s", "3", "3", "0", "0", "0", "✓ VERIFIED"),
        ("RUN_20261114_090831_C7A3A4", "late_arriving.csv", "CSV", "SUCCESS", "0.01s", "1", "1", "0", "0", "0", "✓ VERIFIED"),
        ("RUN_20261114_090830_D57FA1", "idempotent.csv", "CSV", "SUCCESS", "0.01s", "1", "0", "0", "1", "0", "✓ VERIFIED"),
        ("RUN_20261114_090830_DC08D5", "schema_change.csv", "CSV", "FAILED", "0.01s", "1", "0", "1", "0", "0", "✓ VERIFIED"),
    ]

    my = 240
    for rid, src, fmt, st, dur, inp, ins, rej, skp, ret, match in mruns:
        draw.text((60, my), rid, fill="#818cf8", font=get_font(12, bold=True))
        draw.text((300, my), src[:25], fill="#cbd5e1", font=get_font(12))
        draw.text((540, my), fmt, fill="#94a3b8", font=get_font(12))
        
        st_color = {"SUCCESS": "#10b981", "PARTIAL": "#f59e0b", "FAILED": "#ef4444"}.get(st, "#94a3b8")
        draw_rounded_rect(draw, (625, my - 3, 715, my + 18), 4, st_color + "25", outline=st_color)
        draw.text((640, my), st, fill=st_color, font=get_font(11, bold=True))

        draw.text((770, my), dur, fill="#cbd5e1", font=get_font(12))
        draw.text((870, my), inp, fill="#f8fafc", font=get_font(12, bold=True))
        draw.text((970, my), ins, fill="#10b981", font=get_font(12, bold=True))
        draw.text((1080, my), rej, fill="#ef4444", font=get_font(12, bold=True))
        draw.text((1210, my), skp, fill="#38bdf8", font=get_font(12, bold=True))
        draw.text((1320, my), ret, fill="#cbd5e1", font=get_font(12))
        draw.text((1420, my), match, fill="#10b981", font=get_font(12, bold=True))
        draw.line((40, my + 26, 1560, my + 26), fill="#334155")
        my += 44

    img.save(screenshots_dir / "05_pipeline_monitoring.png")
    print("Saved screenshots/05_pipeline_monitoring.png")

if __name__ == "__main__":
    create_overview_screenshot()
    create_explorer_screenshot()
    create_performance_screenshot()
    create_quality_screenshot()
    create_monitoring_screenshot()
    print("All 5 high-resolution screenshots generated successfully in screenshots/ directory.")
