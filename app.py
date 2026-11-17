
import streamlit as st
import psutil
import time
import socket
import hashlib
import math
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="LiveSysBench",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.main {
    background-color: #0e1117;
}
[data-testid="stMetric"] {
    background-color: #192330;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #29394a;
}
h1, h2, h3 {
    color: #58c4dd;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 LiveSysBench")
st.subheader("Real-Time Computer System and Network Performance Evaluation")

st.caption(
    "Live monitoring | Performance benchmarking | "
    "Queuing theory | Experimental analysis"
)

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "history" not in st.session_state:
    st.session_state.history = []

if "previous_net" not in st.session_state:
    st.session_state.previous_net = None

if "previous_disk" not in st.session_state:
    st.session_state.previous_disk = None

if "previous_time" not in st.session_state:
    st.session_state.previous_time = None

if "benchmark_result" not in st.session_state:
    st.session_state.benchmark_result = None

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("⚙️ Dashboard Controls")

refresh_rate = st.sidebar.selectbox(
    "Refresh interval",
    [1, 2, 3, 5],
    index=1
)

auto_refresh = st.sidebar.toggle(
    "Enable live monitoring",
    value=True
)

if st.sidebar.button("Clear monitoring history"):
    st.session_state.history = []
    st.session_state.previous_net = None
    st.session_state.previous_disk = None
    st.session_state.previous_time = None
    st.rerun()

if auto_refresh:
    st_autorefresh(
        interval=refresh_rate * 1000,
        key="live_refresh"
    )

# --------------------------------------------------
# SYSTEM INFORMATION
# --------------------------------------------------

st.header("1. System Information")

cpu_count = psutil.cpu_count(logical=True)
physical_cores = psutil.cpu_count(logical=False)

memory = psutil.virtual_memory()
disk = psutil.disk_usage("/")

info1, info2, info3, info4 = st.columns(4)

info1.metric("Logical CPU Cores", cpu_count)
info2.metric("Physical CPU Cores", physical_cores)
info3.metric("Total RAM", f"{memory.total / (1024**3):.2f} GB")
info4.metric("Disk Capacity", f"{disk.total / (1024**3):.2f} GB")

# --------------------------------------------------
# LIVE PERFORMANCE MEASUREMENTS
# --------------------------------------------------

st.header("2. Real-Time Performance Monitoring")

cpu = psutil.cpu_percent(interval=0.3)

memory = psutil.virtual_memory()
disk = psutil.disk_usage("/")

net = psutil.net_io_counters()
disk_io = psutil.disk_io_counters()

current_time = time.time()

upload_rate = 0.0
download_rate = 0.0
read_rate = 0.0
write_rate = 0.0

if st.session_state.previous_time is not None:
    elapsed = current_time - st.session_state.previous_time

    if elapsed > 0:
        previous_net = st.session_state.previous_net
        previous_disk = st.session_state.previous_disk

        upload_rate = max(
            0,
            net.bytes_sent - previous_net.bytes_sent
        ) / elapsed / (1024 * 1024)

        download_rate = max(
            0,
            net.bytes_recv - previous_net.bytes_recv
        ) / elapsed / (1024 * 1024)

        if disk_io is not None and previous_disk is not None:
            read_rate = max(
                0,
                disk_io.read_bytes - previous_disk.read_bytes
            ) / elapsed / (1024 * 1024)

            write_rate = max(
                0,
                disk_io.write_bytes - previous_disk.write_bytes
            ) / elapsed / (1024 * 1024)

st.session_state.previous_net = net
st.session_state.previous_disk = disk_io
st.session_state.previous_time = current_time

# CPU and memory metrics

c1, c2, c3, c4 = st.columns(4)

c1.metric("CPU Utilization", f"{cpu:.1f}%")
c2.metric("RAM Utilization", f"{memory.percent:.1f}%")
c3.metric("Disk Utilization", f"{disk.percent:.1f}%")
c4.metric("Running Processes", len(psutil.pids()))

# Network and disk metrics

c5, c6, c7, c8 = st.columns(4)

c5.metric("Upload Speed", f"{upload_rate:.3f} MB/s")
c6.metric("Download Speed", f"{download_rate:.3f} MB/s")
c7.metric("Disk Read", f"{read_rate:.3f} MB/s")
c8.metric("Disk Write", f"{write_rate:.3f} MB/s")

# --------------------------------------------------
# NETWORK LATENCY
# --------------------------------------------------

st.header("3. Network Latency Evaluation")

def measure_latency(host="1.1.1.1", port=443):
    try:
        start = time.perf_counter()

        with socket.create_connection(
            (host, port),
            timeout=2
        ):
            pass

        end = time.perf_counter()

        return (end - start) * 1000

    except (OSError, TimeoutError):
        return None


if st.button("Measure Network Latency"):
    latency = measure_latency()

    if latency is not None:
        st.success(f"Connection response time: {latency:.2f} ms")
        st.caption(
            "This is TCP connection establishment time, "
            "not ICMP ping or application response time."
        )
    else:
        st.warning("Unable to establish a network connection.")

# --------------------------------------------------
# PERFORMANCE HISTORY
# --------------------------------------------------

st.session_state.history.append({
    "Time": time.strftime("%H:%M:%S"),
    "CPU": cpu,
    "Memory": memory.percent,
    "Disk": disk.percent,
    "Upload": upload_rate,
    "Download": download_rate
})

st.session_state.history = st.session_state.history[-60:]

df = pd.DataFrame(st.session_state.history)

st.header("4. Live Performance Charts")

if not df.empty:
    chart1, chart2 = st.columns(2)

    with chart1:
        st.plotly_chart(
            px.line(
                df,
                x="Time",
                y=["CPU", "Memory", "Disk"],
                title="System Resource Utilization (%)",
                markers=True
            ),
            use_container_width=True
        )

    with chart2:
        st.plotly_chart(
            px.line(
                df,
                x="Time",
                y=["Upload", "Download"],
                title="Network Throughput (MB/s)",
                markers=True
            ),
            use_container_width=True
        )

    st.dataframe(
        df.tail(10),
        use_container_width=True,
        hide_index=True
    )

# --------------------------------------------------
# CONTROLLED CPU BENCHMARK
# --------------------------------------------------

st.header("5. CPU Performance Benchmark")

st.write(
    "Execute a short, bounded computational workload "
    "and measure its execution throughput."
)

if st.button("Run CPU Benchmark"):
    iterations = 0

    start = time.perf_counter()
    deadline = start + 0.75

    while time.perf_counter() < deadline:
        hashlib.sha256(
            b"LiveSysBench Performance Evaluation"
        ).digest()

        iterations += 1

    elapsed = time.perf_counter() - start

    result = iterations / elapsed

    st.session_state.benchmark_result = {
        "iterations": iterations,
        "elapsed": elapsed,
        "throughput": result
    }

if st.session_state.benchmark_result:
    result = st.session_state.benchmark_result

    b1, b2, b3 = st.columns(3)

    b1.metric("Iterations", f"{result['iterations']:,}")
    b2.metric("Execution Time", f"{result['elapsed']:.3f} sec")
    b3.metric(
        "Throughput",
        f"{result['throughput']:,.0f} operations/sec"
    )

    st.info(
        "Benchmark results depend on CPU architecture, "
        "runtime conditions and system load. Compare results "
        "only under documented experimental conditions."
    )

# --------------------------------------------------
# LITTLE'S LAW
# --------------------------------------------------

st.header("6. Little's Law Calculator")

st.latex(r"L = \lambda W")

st.write(
    "Calculate the average number of jobs in a system "
    "using arrival rate and average response time."
)

l1, l2 = st.columns(2)

with l1:
    arrival_rate = st.number_input(
        "Arrival rate (jobs/second)",
        min_value=0.0,
        value=5.0,
        step=0.5
    )

with l2:
    response_time = st.number_input(
        "Average response time (seconds)",
        min_value=0.0,
        value=0.2,
        step=0.1
    )

if st.button("Calculate Little's Law"):
    L = arrival_rate * response_time

    st.success(f"Average number of jobs in system (L): {L:.4f}")

# --------------------------------------------------
# QUEUING THEORY
# --------------------------------------------------

st.header("7. Queuing Theory Performance Analyzer")

st.latex(
    r"\rho = \frac{\lambda}{c\mu}"
)

st.write(
    "Analyze M/M/1 and M/M/c queues using "
    "the Erlang-C formula."
)

q1, q2, q3 = st.columns(3)

with q1:
    lam = st.number_input(
        "Arrival rate λ (jobs/sec)",
        min_value=0.0,
        value=5.0,
        step=0.5,
        key="queue_lambda"
    )

with q2:
    mu = st.number_input(
        "Service rate μ (jobs/sec/server)",
        min_value=0.01,
        value=10.0,
        step=0.5
    )

with q3:
    servers = st.number_input(
        "Number of servers",
        min_value=1,
        max_value=20,
        value=1,
        step=1
    )


def queue_analysis(lam, mu, c):

    if lam == 0:
        return {
            "utilization": 0,
            "Lq": 0,
            "L": 0,
            "Wq": 0,
            "W": 1 / mu,
            "capacity": c * mu
        }

    rho = lam / (c * mu)

    if rho >= 1:
        return None

    a = lam / mu

    summation = sum(
        (a ** n) / math.factorial(n)
        for n in range(c)
    )

    tail = (a ** c) / (
        math.factorial(c) * (1 - rho)
    )

    p0 = 1 / (summation + tail)

    probability_wait = tail * p0

    Lq = probability_wait * rho / (1 - rho)

    Wq = Lq / lam

    W = Wq + (1 / mu)

    L = lam * W

    return {
        "utilization": rho * 100,
        "Lq": Lq,
        "L": L,
        "Wq": Wq,
        "W": W,
        "capacity": c * mu
    }


if st.button("Analyze Queue Performance"):

    result = queue_analysis(lam, mu, int(servers))

    if result is None:

        st.error(
            "The system is unstable because arrival rate "
            "must be lower than total service capacity."
        )

    else:

        st.success("Queueing analysis completed.")

        r1, r2, r3 = st.columns(3)

        r1.metric(
            "Server Utilization",
            f"{result['utilization']:.2f}%"
        )

        r2.metric(
            "Average Queue Length (Lq)",
            f"{result['Lq']:.4f}"
        )

        r3.metric(
            "Average System Jobs (L)",
            f"{result['L']:.4f}"
        )

        r4, r5, r6 = st.columns(3)

        r4.metric(
            "Queue Waiting Time",
            f"{result['Wq']:.4f} sec"
        )

        r5.metric(
            "System Response Time",
            f"{result['W']:.4f} sec"
        )

        r6.metric(
            "Maximum Theoretical Capacity",
            f"{result['capacity']:.2f} jobs/sec"
        )

        st.info(
            "This is an analytical infinite-buffer, "
            "Poisson-arrival, exponential-service queueing model. "
            "It assumes identical independent servers."
        )

# --------------------------------------------------
# PERFORMANCE EVALUATION
# --------------------------------------------------

st.header("8. Performance Evaluation Report")

utilization = cpu

if utilization < 50:
    st.success("CPU status: Low utilization")

elif utilization < 80:
    st.warning("CPU status: Moderate utilization")

else:
    st.error("CPU status: High utilization")

if memory.percent < 70:
    st.success("Memory status: Available capacity is sufficient")

elif memory.percent < 90:
    st.warning("Memory status: Memory usage is elevated")

else:
    st.error("Memory status: Memory utilization is high")

if st.button("Generate Performance Summary"):

    report = pd.DataFrame([{
        "CPU Utilization (%)": cpu,
        "RAM Utilization (%)": memory.percent,
        "Disk Utilization (%)": disk.percent,
        "Upload (MB/s)": upload_rate,
        "Download (MB/s)": download_rate,
        "Processes": len(psutil.pids())
    }])

    st.dataframe(report, use_container_width=True)

    st.download_button(
        "Download Performance Report",
        data=report.to_csv(index=False),
        file_name="LiveSysBench_Report.csv",
        mime="text/csv"
    )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "LiveSysBench | FI1916 - Performance Evaluation "
    "of Computer Systems and Networks | "
    "Anna University Regulation 2021"
)
