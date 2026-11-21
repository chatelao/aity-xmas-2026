#ifndef WIFI_AP_H
#define WIFI_AP_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

void wifi_ap_configure_xiao_antenna(void);
bool wifi_ap_start(void);
uint8_t wifi_ap_get_station_count(void);
uint32_t wifi_ap_get_uptime_seconds(void);

#ifdef __cplusplus
}
#endif

#endif // WIFI_AP_H
