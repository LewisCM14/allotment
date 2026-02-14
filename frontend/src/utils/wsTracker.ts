(() => {
	// track all open sockets
	const OriginalWebSocket = globalThis.WebSocket;
	const __trackedSockets = new Set<WebSocket>();

	// override constructor with subclass
	class TrackedWebSocket extends OriginalWebSocket {
		constructor(url: string | URL, protocols?: string | string[]) {
			const urlStr = typeof url === "string" ? url : url.toString();
			super(urlStr, protocols);
			__trackedSockets.add(this);
			this.addEventListener("close", () => __trackedSockets.delete(this));
		}
	}
	globalThis.WebSocket = TrackedWebSocket;

	// close sockets on pagehide
	globalThis.addEventListener("pagehide", () => {
		for (const ws of __trackedSockets) ws.close();
	});
})();

export {};
