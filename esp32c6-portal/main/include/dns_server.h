#ifndef DNS_SERVER_H
#define DNS_SERVER_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define DNS_MAX_PACKET_SIZE 512

/**
 * Pure DNS captive-portal packet builder (host-testable).
 *
 * Parses an incoming DNS query and builds a DNS response:
 * - For Type A (1) Class IN (1) queries: returns a 1-answer reply pointing to ip_addr[4] (TTL 60s).
 * - For non-A queries (e.g. AAAA, HTTPS, SVCB): returns NOERROR with 0 answers so mobile OSes
 *   immediately fall back to IPv4 HTTP captive portal probing without waiting for DNS timeouts.
 *
 * Returns the response length in bytes, or 0 if the query is malformed.
 */
size_t dns_server_build_response(const uint8_t *query,
                                 size_t query_len,
                                 uint8_t *response,
                                 size_t response_max_len,
                                 const uint8_t ip_addr[4]);

void dns_server_start(void);

#ifdef __cplusplus
}
#endif

#endif // DNS_SERVER_H
