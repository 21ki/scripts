$httpClient.get({
	url: "https://7b367ed3.proxy.webhookapp.com",
	body: {
        "id": "surge-http",
        "name": "surge",
        "port": 6152,
        "address": $network.v4.primaryAddress,
        "check": {
            "Name": "Surge HTTP proxy service check",
            "TCP": $network.v4.primaryAddress + ":6152",
            "Interval": "60s"
        }
    }
}, function(error, response, data) {
    if (error) {
        $done(error);
    } else {
        $done({response});
    }
});
