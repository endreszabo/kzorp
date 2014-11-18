#ifndef _KZORP_LOOKUP_INTERNAL_H
#define _KZORP_LOOKUP_INTERNAL_H

/* 
 * Copyright (C) 2006-2012, BalaBit IT Ltd.
 * This program/include file is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as published
 * by the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * This program/include file is distributed in the hope that it will be
 * useful, but WITHOUT ANY WARRANTY; without even the implied warranty
 * of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation,Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */
/*
 * KZorp lookup internal function declarations and struct definitions.
 * It enables to test originally static functions.
 * The File containing the definitions of the functions must include this file.
 */

#include "kzorp.h"

#ifdef KZ_USERSPACE
#define KZ_PROTECTED
#else
#define KZ_PROTECTED static
#endif

#define KZ_NOT_MATCHING_SCORE ((u_int64_t)-1)

struct kz_lookup_ipv6_node {
  struct kz_lookup_ipv6_node *parent;
  struct kz_lookup_ipv6_node *left;
  struct kz_lookup_ipv6_node *right;
  struct in6_addr addr;
  struct kz_zone *zone;
  __u16 prefix_len;
};

/* header of the lookup data. After dimension_map there are additional data,
 * for the dimensions in the rule, as specified by the dimension_map. */
struct kz_rule_lookup_data {
	/* back-pointer to original rule structure so that we have the
	 * service and dispatcher pointers */
	const struct kz_dispatcher_n_dimension_rule *orig;

	u_int32_t bytes_to_next; /* number of bytes to the next rule (includes
				  * the full kz_rule_lookup_data header size),
				  * 0 if there are no more rules */
	u_int32_t dimension_map;

	/* additional bytes here for dimension data. See also KZORP_DIMENSION */
};

struct kz_rule_lookup_cursor {
	struct kz_rule_lookup_data *rule;
	u_int32_t pos;
};

KZ_PROTECTED struct kz_rule_lookup_data*
kz_rule_lookup_cursor_next_rule(struct kz_rule_lookup_cursor *cursor);

KZ_PROTECTED int64_t
kz_ndim_eval_rule(struct kz_rule_lookup_cursor * cursor,
		  int64_t best_all,
		  const struct kz_reqids * const reqids,
		  const struct net_device * const iface,
		  u_int8_t l3proto,
		  const union nf_inet_addr * const src_addr,
		  const union nf_inet_addr * const dst_addr,
		  u_int8_t l4proto, u_int16_t src_port, u_int16_t dst_port,
		  const struct kz_zone * const src_zone,
		  const struct kz_zone * const dst_zone,
		  const unsigned long *src_zone_mask,
		  const unsigned long *dst_zone_mask);

KZ_PROTECTED size_t
kz_generate_lookup_data_rule_size(const struct kz_dispatcher_n_dimension_rule * const rule);

KZ_PROTECTED struct kz_rule_lookup_data *
kz_generate_lookup_data_rule(const struct kz_dispatcher_n_dimension_rule * const rule, void *buf);

/**
 * struct kz_percpu_env - per-CPU work area for the n-dimensional lookup algorithms
 * @max_result_size: the maximal size of the result set to return
 * @src_mask: bitmask to use as a temporary helper for source zone evaluation
 * @dst_mask: bitmask to use as a temporary helper for destination zone evaluation
 * @results: the buffer to return results in, an array of pointers to
 *       struct kz_dispatcher_n_dimension_rule structures, should point to an
 *       array with at lease @max_result_size elements
 * @result_size: the number of matching rules stored in @results
 */
struct kz_percpu_env {
  /* in */
  size_t max_result_size;
  unsigned long *src_mask;
  unsigned long *dst_mask;
  /* out */
  struct kz_dispatcher_n_dimension_rule const **result_rules;
  size_t result_size;
};

KZ_PROTECTED u_int32_t
kz_ndim_eval(
  const struct kz_reqids *reqids, const struct net_device *iface, u_int8_t l3proto,
  const union nf_inet_addr * const src_addr, const union nf_inet_addr * const dst_addr,
  u_int8_t l4proto, u_int16_t src_port, u_int16_t dst_port,
  const struct kz_zone * src_zone,
  const struct kz_zone * dst_zone,
  const struct kz_head_d * const dispatchers,
  struct kz_percpu_env *lenv
);


/**
 * mark_zone_path - mark all reachable zone IDs starting from a given zone
 * @mask: the bitfield to mark zones in
 * @zone: the zone to start with
 *
 * Starting with @zone and iterating up on the admin_parent chain this
 * function sets bits in @mask to 1 for all accessible zones.
 */
static __always_inline void
mark_zone_path(unsigned long *mask, const struct kz_zone *zone)
{
	while (zone != NULL) {
		set_bit(zone->index, mask);
		zone = zone->admin_parent;
	}
}

/**
 * mask_to_size_v4 - given a 32 bit IPv4 subnet mask return how many leading 1 bits are set
 * @mask: IPv4 subnet mask
 *
 * Returns: the number of leading '1' bits in @mask
 */
static __always_inline unsigned int
mask_to_size_v4(const struct in_addr * const mask)
{
	if (mask == 0U)
		return 0;
	else
		return 32 - fls(ntohl(~mask->s_addr));
}

/**
 * mask_to_size_v6 - given a 128 bit IPv6 subnet mask return how many leading 1 bits are set
 * @mask: IPv6 subnet mask
 *
 * Returns: the number of leading '1' bits in @mask
 */
static __always_inline unsigned int
mask_to_size_v6(const struct in6_addr * const mask)
{
	unsigned int i;

	if (mask->s6_addr32[0] == 0U &&
	    mask->s6_addr32[1] == 0U &&
	    mask->s6_addr32[2] == 0U &&
	    mask->s6_addr32[3] == 0U)
		return 0;

	for (i = 0; i < 4; i++) {
		u_int32_t m = mask->s6_addr32[i];
		if (m == 0xffffffff)
			continue;
		if (m == 0)
			return i * 32;

		return i * 32 + 32 - fls(ntohl(~m));
	}

	return 128;
}

KZ_PROTECTED void
kz_generate_lookup_data(struct kz_head_d *dispatchers);

KZ_PROTECTED inline struct kz_lookup_ipv6_node *
ipv6_node_new(void);

KZ_PROTECTED inline void
ipv6_node_free(struct kz_lookup_ipv6_node *n);

struct kz_lookup_ipv6_node *
ipv6_add(struct kz_lookup_ipv6_node *root, struct in6_addr *addr, int prefix_len);

KZ_PROTECTED struct kz_lookup_ipv6_node *
ipv6_lookup(struct kz_lookup_ipv6_node *root, const struct in6_addr *addr);

KZ_PROTECTED void
ipv6_destroy(struct kz_lookup_ipv6_node *node);

#endif /* _KZORP_LOOKUP_INTERNAL_H */
