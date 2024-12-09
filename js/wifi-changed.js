// https://medium.com/@alanhe421/surge%E5%AE%9E%E7%8E%B0%E6%A0%B9%E6%8D%AEwi-fi%E6%83%85%E5%86%B5%E8%87%AA%E5%8A%A8%E8%B0%83%E6%95%B4%E4%BB%A3%E7%90%86%E7%AD%96%E7%95%A5-659592e16177
const WIFI_DONT_NEED_PROXYS = ['xiaomi_Alan_5G_1'];
const CURRENT_WIFI_SSID_KEY = 'current_wifi_ssid';

if (wifiChanged()) {
  const mode = WIFI_DONT_NEED_PROXYS.includes($network.wifi.ssid)
    ? 'direct'
    : 'rule';
  $surge.setOutboundMode(mode);
  $notification.post(
    'Surge',
    `Wi-Fi changed to ${$network.wifi.ssid || 'cellular'}`,
    `use ${mode} mode`
  );
}

function wifiChanged() {
  const currentWifiSSid = $persistentStore.read(CURRENT_WIFI_SSID_KEY);
  const changed = currentWifiSSid !== $network.wifi.ssid;
  changed && $persistentStore.write($network.wifi.ssid, CURRENT_WIFI_SSID_KEY);
  return changed;
}

$done();
