// E2E test: login flow (audit 4.1, 6.4)
import { test, expect } from "@playwright/test";

test.describe("Authentication", () => {
  test("user can login with default admin credentials", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("h1, h2, .text-muted")).toBeVisible();

    // Click "Sign In" tab
    await page.getByRole("button", { name: "Sign In" }).click();

    await page.getByPlaceholder("Email").fill("admin@vaxgenesis.ai");
    await page.getByPlaceholder("Password").fill("admin123");
    await page.getByRole("button", { name: "Sign In" }).click();

    // Should redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  });

  test("login fails with wrong password", async ({ page }) => {
    await page.goto("/login");
    await page.getByPlaceholder("Email").fill("admin@vaxgenesis.ai");
    await page.getByPlaceholder("Password").fill("wrongpassword");
    await page.getByRole("button", { name: "Sign In" }).click();

    await expect(page.getByText(/invalid email or password/i)).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test("logout redirects to login", async ({ page, browser }) => {
    // Login first
    await page.goto("/login");
    await page.getByPlaceholder("Email").fill("admin@vaxgenesis.ai");
    await page.getByPlaceholder("Password").fill("admin123");
    await page.getByRole("button", { name: "Sign In" }).click();
    await expect(page).toHaveURL(/\/dashboard/);

    // Logout
    await page.getByRole("button", { name: "Logout" }).click();
    await expect(page).toHaveURL(/\/login/);
  });
});
