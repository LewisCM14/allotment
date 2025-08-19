import { z } from "zod";

export const feedPreferenceSchema = z.object({
	feed_id: z.string().uuid("Invalid feed ID"),
	day_id: z.string().uuid("Invalid day ID"),
});

export type FeedPreferenceFormData = z.infer<typeof feedPreferenceSchema>;

export interface IFeedType {
	id: string;
	name: string;
}

export interface IDay {
	id: string;
	name: string;
}

export interface IUserFeedPreference {
	user_id: string;
	feed_id: string;
	day_id: string;
	feed: IFeedType;
	day: IDay;
}

export interface IFeedPreferenceRequest {
	feed_id: string;
	day_id: string;
}

export interface IFeedPreferenceUpdateRequest {
	day_id: string;
}
