#!/usr/bin/env python3

import matplotlib.pyplot as plt
import datetime
import json
import sys
import os

nodes_from_ip = {
    "192.168.4.60": "A",
    "192.168.4.59": "B",
    "192.168.4.55": "C",
    "192.168.4.51": "D"
}

subtitles = {
        "TCP": ["Congestion Window Size", "Re-transmissions"],
        "UDP": ["Jitter", "Packet Loss"]
}

ylabels = {
        "TCP": ["cwnd size", "re-transmissions count"],
        "UDP": ["ms", "packet loss %"]
}

def load_json(file):
    with open(file, "r") as f:
        return json.load(f)

def tcp_compare(name, time, rtrans, cwnd):

    fig = plt.figure()

    fig.suptitle(name)

    plt.plot(time, rtrans, label = "re-trans")
    plt.plot(time, cwnd, label = "cwnd")
    fig.legend()

    fig.savefig(name + "_CMP")

def udp_compare(name, time, bdw, jit, plp):

    fig = plt.figure()

    fig.suptitle(name)

    plt.plot(time, bdw, label = "bandwidth")
    plt.plot(time, jit, label = "jitter")
    plt.plot(time, plp, label = "packet loss %")
    fig.legend()

    fig.savefig(name + "_CMP")

def parse_data(json_file):

    json_data = load_json(json_file)

    #print(json_data["start"]["connected"][0]["local_host"])

    client = nodes_from_ip[json_data["start"]["connected"][0]["local_host"]]
    server = nodes_from_ip[json_data["start"]["connected"][0]["remote_host"]]
    protocol = json_data["start"]["test_start"]["protocol"]

    time_intervals = json_data["intervals"]
    time_intervals_sum = [item["sum"] for item in time_intervals]
    time_intervals_stream = [item["streams"][0] for item in time_intervals]

    time_axis = [int(item["end"]) for item in time_intervals_sum]

    throughput = [item["bits_per_second"] / 1_000_000 for item in time_intervals_sum]
    if protocol == "TCP":
        metric2 = [item["snd_cwnd"] for item in time_intervals_stream]
        metric3 = [item["retransmits"] for item in time_intervals_stream]
    else:
        metric2 = [item["jitter_ms"] for item in time_intervals_sum]
        metric3 = [item["lost_percent"] for item in time_intervals_sum]


    return (client, server, protocol, time_axis, throughput, metric2, metric3)

def main():

    if len(sys.argv) <= 1:
        print("Usage: python3 iperf_plot.py <DIR>")
        sys.exit(1)

    data_dir = os.path.abspath(sys.argv[1])

    if not os.path.isdir(data_dir):
        print("Specified directory does not exist!")
        sys.exit(1)

    plot_dir = data_dir + "_PLOTS"
    if not os.path.isdir(plot_dir):
        os.mkdir(plot_dir)

    data_dir_files = sorted(os.listdir(data_dir))

    # NOTE: make it more generic
    if len(data_dir_files) == 2:

        data_dir1 = os.path.join(data_dir, data_dir_files[0])
        data_dir2 = os.path.join(data_dir, data_dir_files[1])

        flow1_files = sorted(os.listdir(data_dir1))
        flow2_files = sorted(os.listdir(data_dir2))

        zero_pad = [0] * 60
        for f1_json_file, f2_json_file in zip(flow1_files, flow2_files):

            print(f1_json_file, f2_json_file)


            f1_json_file_abs = os.path.join(data_dir1, f1_json_file)
            f2_json_file_abs = os.path.join(data_dir2, f2_json_file)

            f1_data = parse_data(f1_json_file_abs)
            f2_data = parse_data(f2_json_file_abs)

            time_axis = f1_data[3]
            protocol = f1_data[2]
            if protocol == "TCP":
                c1 = f1_data[0]
                s1 = f1_data[1]
                c2 = f2_data[0]
                s2 = f2_data[1]
            else:
                c1 = f1_data[1]
                s1 = f1_data[0]
                c2 = f2_data[1]
                s2 = f2_data[0]

            fig, (ax1, ax2, ax3) = plt.subplots(3, sharex=True)

            ax1.plot(time_axis, f1_data[4], label = f"{c1} to {s1}")
            ax1.plot(time_axis, zero_pad + f2_data[4], label = f"{c2} to {s2}")

            ax2.plot(time_axis, f1_data[5])
            ax2.plot(time_axis, zero_pad + f2_data[5])

            ax3.plot(time_axis, f1_data[6])
            ax3.plot(time_axis, zero_pad + f2_data[6])

            fig.legend()

            ax1.grid()
            ax2.grid()
            ax3.grid()

            ax1.set_ylabel('Mbps')
            ax2.set_ylabel(ylabels[protocol][0])
            ax3.set_ylabel(ylabels[protocol][1])

            ax1.set_title("Throughput")
            ax2.set_title(subtitles[protocol][0])
            ax3.set_title(subtitles[protocol][1])

            ax3.set_xlabel('Time (s)')

            file_name = os.path.join(plot_dir, os.path.splitext(f1_json_file)[0] + "-" + os.path.splitext(f2_json_file)[0])
            fig.savefig(file_name)
        sys.exit(0)

    for json_file in os.listdir(data_dir):
        json_file_abs = os.path.join(data_dir, json_file)

        (client, server, protocol, time_axis, throughput, metric2, metric3) = parse_data(json_file_abs)

        fig, (ax1, ax2, ax3) = plt.subplots(3, sharex=True)

        ax1.plot(time_axis, throughput)
        ax2.plot(time_axis, metric2)
        ax3.plot(time_axis, metric3)

        ax1.grid()
        ax2.grid()
        ax3.grid()

        ax1.set_ylabel('Mbps')
        ax2.set_ylabel(ylabels[protocol][0])
        ax3.set_ylabel(ylabels[protocol][1])

        ax1.set_title("Throughput")
        ax2.set_title(subtitles[protocol][0])
        ax3.set_title(subtitles[protocol][1])

        ax3.set_xlabel('Time (s)')

        file_name = os.path.join(plot_dir, os.path.splitext(json_file)[0])
        fig.savefig(file_name)

        print(f"file: {json_file}\n"
              f"client: {client}\n"
              f"server: {server}\n"
              f"protocol: {protocol}\n"
             )

if __name__ == "__main__":
    main()

