{
    "spec": {
        "containers": [{
            "name": "kube-apiserver",
            "resources": {
                "limits": {
                    "cpu": "$API_SERVER_CPU_LIMIT",
                    "memory": "$API_SERVER_MEMORY_LIMIT"
                }
            }
        }]
    }
}
