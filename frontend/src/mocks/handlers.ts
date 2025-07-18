import { authHandlers } from "./authHandlers";
import { userHandlers } from "./userHandlers";
import { familyHandlers } from "./familyHandlers";

export const handlers = [...authHandlers, ...userHandlers, ...familyHandlers];
