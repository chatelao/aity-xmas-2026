#include <stdbool.h>
#include <string.h>
#include "dns_server.h"
#include "board_config.h"

#ifdef ESP_PLATFORM
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "lwip/sockets.h"
#include "lwip/netdb.h"
#endif

#ifdef ESP_PLATFORM
static const char *TAG = "dns_server";
#endif

// DNS header is 12 bytes
#define DNS_HEADER_LEN 12
#define DNS_TYPE_A 1
#define DNS_CLASS_IN 1

size_t dns_server_build_response(const uint8_t *query,
                                 size_t query_len,
                                 uint8_t *response,
                                 size_t response_max_len,
                                 const uint8_t ip_addr[4]) {
    if (query == NULL || response == NULL || ip_addr == NULL) {
        return 0;
    }
    if (query_len < DNS_HEADER_LEN + 5 || query_len > DNS_MAX_PACKET_SIZE) {
        return 0;
    }

    // Parse QNAME to locate QTYPE and QCLASS
    size_t pos = DNS_HEADER_LEN;
    while (pos < query_len) {
        uint8_t label_len = query[pos];
        if (label_len == 0) {
            pos++;
            break;
        }
        // Reject compressed labels in question section or out-of-bounds lengths
        if ((label_len & 0xC0) != 0 || pos + 1 + label_len >= query_len) {
            return 0;
        }
        pos += 1 + label_len;
    }

    // Need 4 bytes after QNAME for QTYPE (2) and QCLASS (2)
    if (pos + 4 > query_len) {
        return 0;
    }

    uint16_t qtype = (uint16_t)((query[pos] << 8) | query[pos + 1]);
    uint16_t qclass = (uint16_t)((query[pos + 2] << 8) | query[pos + 3]);
    size_t question_end = pos + 4;

    bool is_type_a = (qtype == DNS_TYPE_A && qclass == DNS_CLASS_IN);
    size_t needed_len = question_end + (is_type_a ? 16 : 0);
    if (needed_len > response_max_len) {
        return 0;
    }

    // Copy header + question section verbatim
    memcpy(response, query, question_end);

    // Flags: QR=1 (response), AA=1 (authoritative), RD=copied, RA=1, RCODE=0 (NOERROR)
    response[2] = (uint8_t)(0x84 | (query[2] & 0x01));
    response[3] = 0x80;
    // QDCOUNT = 1
    response[4] = 0x00;
    response[5] = 0x01;
    // ANCOUNT = 1 for Type A, 0 for AAAA/HTTPS/SVCB (prevents mobile OS timeout delays)
    response[6] = 0x00;
    response[7] = is_type_a ? 0x01 : 0x00;
    // NSCOUNT = 0, ARCOUNT = 0
    response[8] = 0x00;
    response[9] = 0x00;
    response[10] = 0x00;
    response[11] = 0x00;

    if (!is_type_a) {
        return question_end;
    }

    // Append Answer RR: Name pointer 0xC00C -> offset 12 (start of QNAME)
    size_t ans = question_end;
    response[ans + 0] = 0xC0;
    response[ans + 1] = 0x0C;
    // TYPE = A (1)
    response[ans + 2] = 0x00;
    response[ans + 3] = 0x01;
    // CLASS = IN (1)
    response[ans + 4] = 0x00;
    response[ans + 5] = 0x01;
    // TTL = 60 seconds
    response[ans + 6] = 0x00;
    response[ans + 7] = 0x00;
    response[ans + 8] = 0x00;
    response[ans + 9] = 0x3C;
    // RDLENGTH = 4
    response[ans + 10] = 0x00;
    response[ans + 11] = 0x04;
    // RDATA = AP IPv4 address (192.168.4.1)
    response[ans + 12] = ip_addr[0];
    response[ans + 13] = ip_addr[1];
    response[ans + 14] = ip_addr[2];
    response[ans + 15] = ip_addr[3];

    return ans + 16;
}

#ifdef ESP_PLATFORM
static void dns_server_task(void *param) {
    (void)param;
    const uint8_t ap_ip[4] = {
        XMAS_AP_IP_OCTET_0,
        XMAS_AP_IP_OCTET_1,
        XMAS_AP_IP_OCTET_2,
        XMAS_AP_IP_OCTET_3
    };

    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock < 0) {
        ESP_LOGE(TAG, "Failed to create UDP socket for DNS");
        vTaskDelete(NULL);
        return;
    }

    int reuse = 1;
    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));

    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(XMAS_DNS_PORT);
    addr.sin_addr.s_addr = htonl(INADDR_ANY);

    if (bind(sock, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        ESP_LOGE(TAG, "Failed to bind DNS UDP port %d", XMAS_DNS_PORT);
        close(sock);
        vTaskDelete(NULL);
        return;
    }

    ESP_LOGI(TAG, "Captive Portal DNS server listening on UDP/%d -> %s", XMAS_DNS_PORT, XMAS_AP_IP_STR);

    uint8_t rx_buf[DNS_MAX_PACKET_SIZE];
    uint8_t tx_buf[DNS_MAX_PACKET_SIZE];

    for (;;) {
        struct sockaddr_in client_addr;
        socklen_t client_len = sizeof(client_addr);
        ssize_t rx_len = recvfrom(sock, rx_buf, sizeof(rx_buf), 0,
                                  (struct sockaddr *)&client_addr, &client_len);
        if (rx_len <= 0) {
            continue;
        }
        size_t tx_len = dns_server_build_response(rx_buf, (size_t)rx_len, tx_buf, sizeof(tx_buf), ap_ip);
        if (tx_len > 0) {
            sendto(sock, tx_buf, tx_len, 0, (struct sockaddr *)&client_addr, client_len);
        }
    }
}
#endif

void dns_server_start(void) {
#ifdef ESP_PLATFORM
    xTaskCreate(dns_server_task, "dns_server", 4096, NULL, 4, NULL);
#endif
}
