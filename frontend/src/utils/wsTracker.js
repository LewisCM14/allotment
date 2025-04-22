(() => {
	const OriginalWebSocket = window.WebSocket;
	const __trackedSockets = new Set();
	window.WebSocket = (url, protocols) => {
		const ws = new OriginalWebSocket(url, protocols);
		__trackedSockets.add(ws);
		ws.addEventListener("close", () => __trackedSockets.delete(ws));
		return ws;
	};
	window.addEventListener("pagehide", () => {
		for (const ws of __trackedSockets) {
			ws.close();
		}
	});
})();
