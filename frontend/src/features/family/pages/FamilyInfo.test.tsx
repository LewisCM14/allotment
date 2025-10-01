import { render, screen, waitFor } from "@testing-library/react";
import FamilyInfoPage from "./FamilyInfo";
import * as useFamilyInfoHook from "../hooks/useFamilyInfo";
import React from "react";
import { describe, it, beforeEach, vi, expect, type Mock } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";

// Mock useFamilyInfo
vi.mock("../hooks/useFamilyInfo");

describe("FamilyInfoPage", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	function renderWithRoute(familyId: string) {
		return render(
			<MemoryRouter initialEntries={[`/families/${familyId}`]}>
				<Routes>
					<Route path="/families/:familyId" element={<FamilyInfoPage />} />
				</Routes>
			</MemoryRouter>,
		);
	}

	it("renders loading state", () => {
		(useFamilyInfoHook.useFamilyInfo as unknown as Mock).mockReturnValue({
			data: null,
			isLoading: true,
			error: null,
			isSuccess: false,
		});
		renderWithRoute("123");
		expect(screen.getByText(/loading/i)).toBeInTheDocument();
	});

	it("renders error state", () => {
		(useFamilyInfoHook.useFamilyInfo as unknown as Mock).mockReturnValue({
			data: null,
			isLoading: false,
			error: new Error("Failed to fetch family info"),
			isSuccess: false,
		});
		renderWithRoute("123");
		expect(
			screen.getByText(
				/failed to load family information.*failed to fetch family info/i,
			),
		).toBeInTheDocument();
	});

	it("renders not found when isSuccess is true but data is null", () => {
		(useFamilyInfoHook.useFamilyInfo as unknown as Mock).mockReturnValue({
			data: null,
			isLoading: false,
			error: null,
			isSuccess: true,
		});
		renderWithRoute("123");
		expect(screen.getByText(/not found/i)).toBeInTheDocument();
	});

	it("renders nothing if data is null and not loading or success", () => {
		(useFamilyInfoHook.useFamilyInfo as unknown as Mock).mockReturnValue({
			data: null,
			isLoading: false,
			error: null,
			isSuccess: false,
		});
		renderWithRoute("123");
		// Should not render anything specific
		expect(screen.queryByText(/not found/i)).not.toBeInTheDocument();
		expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
	});

	it("renders family info with all fields and lists", () => {
		(useFamilyInfoHook.useFamilyInfo as unknown as Mock).mockReturnValue({
			data: {
				family_id: "123",
				family_name: "Test Family",
				description: "A test family",
				botanical_group: {
					botanical_group_id: "bg1",
					botanical_group_name: "Root Crops",
					rotate_years: 3,
				},
				companion_to: [
					{ family_id: "c1", family_name: "Carrot" },
					{ family_id: "c2", family_name: "Pea" },
				],
				antagonises: [{ family_id: "a1", family_name: "Onion" }],
				pests: ["Aphid", "Slug"],
				diseases: ["Blight"],
			},
			isLoading: false,
			error: null,
			isSuccess: true,
		});
		renderWithRoute("123");
		expect(screen.getByText(/test family/i)).toBeInTheDocument();
		expect(screen.getByText(/root crops/i)).toBeInTheDocument();
		expect(screen.getByText(/3 year/)).toBeInTheDocument();
		expect(screen.getByText(/carrot/i)).toBeInTheDocument();
		expect(screen.getByText(/pea/i)).toBeInTheDocument();
		expect(screen.getByText(/onion/i)).toBeInTheDocument();
		expect(screen.getByText(/pests/i)).toBeInTheDocument();
		expect(screen.getByText(/diseases/i)).toBeInTheDocument();
	});

	it("renders 'Perennial' if recommended_rotation_years is null", () => {
		// Note: rotate_years null indicates perennial
		(useFamilyInfoHook.useFamilyInfo as unknown as Mock).mockReturnValue({
			data: {
				family_id: "123",
				family_name: "Test Family",
				description: "A test family",
				botanical_group: {
					botanical_group_id: "bg1",
					botanical_group_name: "Root Crops",
					rotate_years: null,
				},
				companion_to: [],
				antagonises: [],
				pests: [],
				diseases: [],
			},
			isLoading: false,
			error: null,
			isSuccess: true,
		});
		renderWithRoute("123");
		expect(screen.getByText(/perennial/i)).toBeInTheDocument();
	});

	it("renders empty states for all lists", () => {
		(useFamilyInfoHook.useFamilyInfo as unknown as Mock).mockReturnValue({
			data: {
				family_id: "123",
				family_name: "Test Family",
				description: "A test family",
				botanical_group: {
					botanical_group_id: "bg1",
					botanical_group_name: "Root Crops",
					rotate_years: 2,
				},
				companion_to: [],
				antagonises: [],
				pests: [],
				diseases: [],
			},
			isLoading: false,
			error: null,
			isSuccess: true,
		});
		renderWithRoute("123");
		expect(
			screen.getByText(/no companion families listed/i),
		).toBeInTheDocument();
		expect(
			screen.getByText(/no antagonist families listed/i),
		).toBeInTheDocument();
		expect(screen.getByText(/no pests listed/i)).toBeInTheDocument();
		expect(screen.getByText(/no diseases listed/i)).toBeInTheDocument();
	});

	it("handles missing botanical_group gracefully", () => {
		(useFamilyInfoHook.useFamilyInfo as unknown as Mock).mockReturnValue({
			data: {
				family_id: "123",
				family_name: "Test Family",
				description: "A test family",
				botanical_group: undefined,
				companion_to: [],
				antagonises: [],
				pests: [],
				diseases: [],
			},
			isLoading: false,
			error: null,
			isSuccess: true,
		});
		renderWithRoute("123");
		// Should not throw, may render nothing or fallback
		expect(screen.getByText(/test family/i)).toBeInTheDocument();
	});
});
