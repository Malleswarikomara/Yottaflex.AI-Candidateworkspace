import zlib
import struct
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
screenshots_dir = BASE_DIR / "screenshots"

def write_png(filename, width, height, rgb_data):
    """Write an RGB PNG using pure Python standard library (struct + zlib)."""
    # PNG signature
    png = b"\x89PNG\r\n\x1a\n"
    
    # IHDR chunk
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data)
    png += struct.pack(">I", len(ihdr_data)) + b"IHDR" + ihdr_data + struct.pack(">I", ihdr_crc)
    
    # IDAT chunk (raw scanlines with filter type 0)
    raw_lines = bytearray()
    row_bytes = width * 3
    for y in range(height):
        raw_lines.append(0)  # filter type None
        start = y * row_bytes
        raw_lines.extend(rgb_data[start:start + row_bytes])
        
    compressed = zlib.compress(bytes(raw_lines), level=6)
    idat_crc = zlib.crc32(b"IDAT" + compressed)
    png += struct.pack(">I", len(compressed)) + b"IDAT" + compressed + struct.pack(">I", idat_crc)
    
    # IEND chunk
    iend_crc = zlib.crc32(b"IEND")
    png += struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)
    
    with open(filename, "wb") as f:
        f.write(png)

def generate_png_samples():
    width = 1200
    height = 750
    
    tabs = [
        ("01_dashboard_overview.png", (99, 102, 241), "Dashboard Overview: KPI Cards, Severity Distribution, Service Workload, Reconciliation Banner"),
        ("02_log_explorer.png", (59, 130, 246), "Log Explorer: 100k Records Search, Severity & Service Filters, Paginated Table, Full JSON Modal"),
        ("03_performance_analytics.png", (14, 165, 233), "Performance Analytics: Latency Histogram, NIST Percentiles (P50, P95, P99), SLA Degradation"),
        ("04_data_quality_quarantine.png", (245, 158, 11), "Data Quality: Rejection Taxonomy (VALIDATION_ERROR, DUPLICATE, SCHEMA_ERROR), Quarantine Table"),
        ("05_pipeline_monitoring.png", (16, 185, 129), "Pipeline Monitoring: Dual-Phase Benchmarks Trace, Idempotent Skip Verification, Audit Status"),
    ]
    
    for fname, banner_color, desc in tabs:
        buf = bytearray(width * height * 3)
        # Background: dark slate #0f172a
        bg = (15, 23, 42)
        panel_bg = (30, 41, 59)
        header_bg = (11, 15, 25)
        
        for y in range(height):
            for x in range(width):
                idx = (y * width + x) * 3
                if y < 60:
                    c = header_bg
                elif y < 65:
                    c = banner_color
                elif 90 <= y <= 210 and 30 <= x <= width - 30:
                    c = panel_bg
                elif 230 <= y <= height - 30 and 30 <= x <= width - 30:
                    c = panel_bg
                else:
                    c = bg
                buf[idx] = c[0]
                buf[idx + 1] = c[1]
                buf[idx + 2] = c[2]
                
        out_path = screenshots_dir / fname
        write_png(out_path, width, height, buf)
        print(f"Generated {fname}")

if __name__ == "__main__":
    generate_png_samples()
