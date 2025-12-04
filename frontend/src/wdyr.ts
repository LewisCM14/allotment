import React from "react";

const { default: whyDidYouRender } = await import(
	"@welldone-software/why-did-you-render"
);

whyDidYouRender(React, {
	trackAllPureComponents: false,
	collapseGroups: true,
	logOwnerReasons: true,
});

console.info("why-did-you-render active (dev mode)");
