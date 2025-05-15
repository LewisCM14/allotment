/**
 * API Cache Service
 * Provides in-memory caching for API responses
 */

interface CacheEntry<T> {
	data: T;
	timestamp: number;
}

export interface CacheOptions {
	duration?: number;
	key?: string;
}

class ApiCache {
	private cache = new Map<string, CacheEntry<unknown>>();
	private defaultDuration = 5 * 60 * 1000; // 5 minutes

	set<T>(key: string, data: T, duration?: number): void {
		this.cache.set(key, {
			data,
			timestamp: Date.now(),
		});

		// Optional automatic cleanup after duration
		if (duration && duration > 0) {
			setTimeout(() => {
				this.cache.delete(key);
			}, duration);
		}
	}

	get<T>(key: string): T | null {
		const entry = this.cache.get(key);
		if (!entry) return null;

		// Check if entry is expired
		if (Date.now() - entry.timestamp > this.defaultDuration) {
			this.cache.delete(key);
			return null;
		}

		return entry.data as T;
	}

	/**
	 * Invalidate cache entries matching a pattern
	 */
	invalidate(keyPattern: RegExp): void {
		for (const key of this.cache.keys()) {
			if (keyPattern.test(key)) {
				this.cache.delete(key);
			}
		}
	}

	/**
	 * Invalidate all cache entries with a certain prefix
	 */
	invalidateByPrefix(prefix: string): void {
		for (const key of this.cache.keys()) {
			if (key.startsWith(prefix)) {
				this.cache.delete(key);
			}
		}
	}

	/**
	 * Clear all cached data
	 */
	clear(): void {
		this.cache.clear();
	}

	/**
	 * Get cache statistics
	 */
	getStats(): { size: number; keys: string[] } {
		return {
			size: this.cache.size,
			keys: Array.from(this.cache.keys()),
		};
	}
}

export const apiCache = new ApiCache();
