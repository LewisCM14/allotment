import api, { handleApiError } from "../../../services/api";
import type {
    IUserFeedPreference,
    IFeedPreferenceRequest,
    IFeedPreferenceUpdateRequest,
    IFeedType,
    IDay,
} from "../forms/PreferenceSchema";

// Re-export types for easier importing in tests
export type {
    IUserFeedPreference,
    IFeedPreferenceRequest,
    IFeedPreferenceUpdateRequest,
    IFeedType,
    IDay,
};

export class NoPreferencesFoundError extends Error {
    constructor(message = "No feed preferences found") {
        super(message);
        this.name = "NoPreferencesFoundError";
    }
}

export const getUserFeedPreferences = async (): Promise<
    IUserFeedPreference[]
> => {
    try {
        const response = await api.get<IUserFeedPreference[]>("/users/preferences");
        return response.data;
    } catch (error: unknown) {
        return handleApiError(
            error,
            "Failed to fetch feed preferences. Please try again.",
        );
    }
};

export const createUserFeedPreference = async (
    preferenceData: IFeedPreferenceRequest,
): Promise<IUserFeedPreference> => {
    try {
        const response = await api.post<IUserFeedPreference>(
            "/users/preferences",
            preferenceData,
        );
        return response.data;
    } catch (error: unknown) {
        return handleApiError(
            error,
            "Failed to create feed preference. Please try again.",
        );
    }
};

export const updateUserFeedPreference = async (
    feedId: string,
    preferenceData: IFeedPreferenceUpdateRequest,
): Promise<IUserFeedPreference> => {
    try {
        const response = await api.put<IUserFeedPreference>(
            `/users/preferences/${feedId}`,
            preferenceData,
        );
        return response.data;
    } catch (error: unknown) {
        return handleApiError(
            error,
            "Failed to update feed preference. Please try again.",
        );
    }
};

export const getFeedTypes = async (): Promise<IFeedType[]> => {
    try {
        const response = await api.get<IFeedType[]>("/feed");
        return response.data;
    } catch (error: unknown) {
        return handleApiError(
            error,
            "Failed to fetch feed types. Please try again.",
        );
    }
};

export const getDays = async (): Promise<IDay[]> => {
    try {
        const response = await api.get<IDay[]>("/days");
        return response.data;
    } catch (error: unknown) {
        return handleApiError(error, "Failed to fetch days. Please try again.");
    }
};
