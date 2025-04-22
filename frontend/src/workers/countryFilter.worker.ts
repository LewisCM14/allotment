self.onmessage = (e: MessageEvent) => {
	const { searchValue, options } = e.data;
	if (!searchValue.trim()) {
		postMessage(options);
		return;
	}
	const lower = searchValue.toLowerCase();
	const filtered = options.filter((opt: { label: string }) =>
		opt.label.toLowerCase().includes(lower),
	);
	postMessage(filtered);
};
