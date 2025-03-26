#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail
set -x

CPU_PERCENT="40"
MEM_PERCENT="80"

while getopts "c:m:" arg; do
	case "$arg" in
		c)
			CPU_PERCENT="${OPTARG}"
			;;
		m)
			MEM_PERCENT="${OPTARG}"
			;;
	esac
done

cpus="$(grep -c ^processor /proc/cpuinfo)"
memory="$(awk '/MemTotal/ { printf "%d \n", $2/1024 }' /proc/meminfo)"

export API_SERVER_CPU_LIMIT=$((cpus * 1000 * ${CPU_PERCENT} / 100))m
export API_SERVER_MEMORY_LIMIT=$((memory * ${MEM_PERCENT} / 100))Mi

envsubst < "/tmp/kubeadm/patches/kube-apiserver+strategic.yaml.tpl"  > "/etc/kubernetes/patches/kube-apiserver+strategic.yaml"
